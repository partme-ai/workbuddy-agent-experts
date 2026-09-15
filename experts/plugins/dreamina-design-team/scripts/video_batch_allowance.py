"""Private durable accounting for one approved Dreamina video batch."""

from __future__ import annotations

import copy
import fcntl
import hashlib
import hmac
import json
import os
import re
import secrets
import stat
import tempfile
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping

from scripts.json_contracts import ContractValidationError, canonical_fingerprint, parse_rfc3339, validate_contract
from scripts.video_generation_planner import PlanningError, quote_total, validate_batch_quote


class BatchScopeError(ValueError):
    """The quote, request, or durable state is outside the approved envelope."""


class BudgetExceededError(BatchScopeError):
    """Declared or consumed credits exceed the exact pre-enumerated ceiling."""


class AllowanceAlreadyActivatedError(BatchScopeError):
    """A quote fingerprint has already consumed its one activation approval."""


class ReservationConsumedError(BatchScopeError):
    """An exact shot attempt has already been irreversibly reserved."""


class AllowanceNotFoundError(BatchScopeError):
    """No durable allowance exists for the opaque identifier."""


class AllowanceCommitIndeterminateError(BatchScopeError):
    """A durable replace may have committed; reconcile state instead of retrying."""

    def __init__(self, allowance_id: str, operation: str) -> None:
        super().__init__(f"{operation} outcome is indeterminate for {allowance_id}; reconcile before continuing")
        self.allowance_id = allowance_id
        self.operation = operation


class SealKeyUnavailableError(BatchScopeError):
    """The stable private allowance seal key is missing, changed, or unsafe."""


_SEAL_DOMAIN = b"codex-dreamina-design/video-batch-allowance/v1\x00"


_ALLOWANCE_ID = re.compile(r"^ba_[a-f0-9]{32}$")
_RESERVATION_ID = re.compile(r"^br_[a-f0-9]{32}$")
_SUBMIT_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_ERROR_CODE = re.compile(r"^[A-Z0-9_-]{1,128}$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_all(descriptor: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(descriptor, payload[offset:])
        if not isinstance(written, int) or written <= 0:
            raise OSError("durable write made no progress")
        offset += written


class FileSealKeyStore:
    """Load one stable 256-bit HMAC key from an owner-only no-follow file."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else Path.home() / ".config" / "codex-dreamina-design" / "allowance-seal.key"
        parent = self.path.parent
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            self._parent_fd = os.open(parent, flags)
            metadata = os.fstat(self._parent_fd)
            if (
                not stat.S_ISDIR(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o700
            ):
                raise SealKeyUnavailableError("seal key directory ownership, type, or mode is unsafe")
            self._parent_identity = os.fstat(self._parent_fd)
        except Exception:
            descriptor = getattr(self, "_parent_fd", None)
            if descriptor is not None:
                os.close(descriptor)
                self._parent_fd = None
            raise

    def load(self, *, allow_create: bool) -> bytes:
        self._assert_parent()
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(self.path.name, flags, dir_fd=self._parent_fd)
        except FileNotFoundError:
            if not allow_create:
                raise SealKeyUnavailableError("seal key is missing while allowances exist")
            key = secrets.token_bytes(32)
            try:
                descriptor = os.open(self.path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=self._parent_fd)
                try:
                    _write_all(descriptor, key)
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
            except FileExistsError:
                return self.load(allow_create=False)
            os.fsync(self._parent_fd)
            return key
        except OSError as exc:
            raise SealKeyUnavailableError("seal key cannot be safely opened") from exc
        try:
            before = os.fstat(descriptor)
            key = os.read(descriptor, 33)
            after = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        try:
            current = os.stat(self.path.name, dir_fd=self._parent_fd, follow_symlinks=False)
        except OSError as exc:
            raise SealKeyUnavailableError("seal key path changed during read") from exc
        if (
            not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid()
            or stat.S_IMODE(before.st_mode) != 0o600 or before.st_ino != after.st_ino
            or before.st_dev != after.st_dev or before.st_size != after.st_size or len(key) != 32
            or current.st_ino != after.st_ino or current.st_dev != after.st_dev
        ):
            raise SealKeyUnavailableError("seal key ownership, mode, identity, or length is unsafe")
        return key

    def close(self) -> None:
        descriptor = getattr(self, "_parent_fd", None)
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
            self._parent_fd = None

    def _assert_parent(self) -> None:
        current = self.path.parent.lstat()
        pinned = os.fstat(self._parent_fd)
        if (
            not stat.S_ISDIR(current.st_mode)
            or current.st_uid != os.getuid()
            or stat.S_IMODE(current.st_mode) != 0o700
            or (current.st_dev, current.st_ino) != (pinned.st_dev, pinned.st_ino)
            or (pinned.st_dev, pinned.st_ino) != (self._parent_identity.st_dev, self._parent_identity.st_ino)
        ):
            raise SealKeyUnavailableError("seal key directory identity changed")


class LocalQuoteResolver:
    """Persist and resolve the exact immutable quote when no project-store resolver is injected."""

    def __init__(self, root: Path, *, parent_fd: int | None = None) -> None:
        self._root = Path(root) / "quotes"
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        self._parent_fd = None
        self._owns_parent = parent_fd is None
        try:
            if parent_fd is None:
                base = Path(root)
                base.mkdir(parents=True, exist_ok=True, mode=0o700)
                self._parent_fd = os.open(base, flags)
                parent_fd = self._parent_fd
                parent_metadata = os.fstat(parent_fd)
                if (
                    not stat.S_ISDIR(parent_metadata.st_mode)
                    or parent_metadata.st_uid != os.getuid()
                    or stat.S_IMODE(parent_metadata.st_mode) != 0o700
                ):
                    raise BatchScopeError("quote parent directory is unsafe")
            expected = None
            try:
                os.mkdir("quotes", 0o700, dir_fd=parent_fd)
                expected = os.stat("quotes", dir_fd=parent_fd, follow_symlinks=False)
            except FileExistsError:
                expected = os.stat("quotes", dir_fd=parent_fd, follow_symlinks=False)
                if (
                    not stat.S_ISDIR(expected.st_mode)
                    or expected.st_uid != os.getuid()
                    or stat.S_IMODE(expected.st_mode) != 0o700
                ):
                    raise BatchScopeError("quote directory ownership, type, or mode is unsafe")
            self._root_fd = os.open("quotes", flags, dir_fd=parent_fd)
            metadata = os.fstat(self._root_fd)
            if (
                not stat.S_ISDIR(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o700
                or expected is not None
                and (metadata.st_dev, metadata.st_ino) != (expected.st_dev, expected.st_ino)
            ):
                raise BatchScopeError("quote directory ownership, type, mode, or identity is unsafe")
            self._identity = os.fstat(self._root_fd)
            self._pinned_parent_fd = parent_fd
        except Exception as exc:
            self.close()
            if isinstance(exc, BatchScopeError):
                raise
            raise BatchScopeError("quote directory initialization is unsafe") from exc

    @staticmethod
    def identity(quote: Mapping[str, Any]) -> dict[str, Any]:
        relative = f"{quote['project_id']}/video_batch_quote/{quote['quote_version']}.json"
        return {"project_id": quote["project_id"], "family": "video_batch_quote", "version": quote["quote_version"], "path": relative, "fingerprint": quote["quote_fingerprint"]}

    def persist(self, quote: Mapping[str, Any]) -> dict[str, Any]:
        identity = self.identity(quote)
        self._assert_identity()
        name = f"{identity['fingerprint']}.json"
        encoded = json.dumps(dict(quote), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        try:
            descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=self._root_fd)
        except FileExistsError:
            if self.resolve(identity) != dict(quote):
                raise BatchScopeError("persisted quote identity collides with different content")
            return identity
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.fsync(self._root_fd)
        return identity

    def resolve(self, identity: Mapping[str, Any]) -> dict[str, Any]:
        self._assert_identity()
        fingerprint = identity.get("fingerprint")
        if not isinstance(fingerprint, str) or re.fullmatch(r"[a-f0-9]{64}", fingerprint) is None:
            raise BatchScopeError("quote identity is invalid")
        name = f"{fingerprint}.json"
        try:
            descriptor = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=self._root_fd)
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o600:
                os.close(descriptor)
                raise BatchScopeError("persisted quote file is unsafe")
            with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
                quote = json.load(handle)
            current = os.stat(name, dir_fd=self._root_fd, follow_symlinks=False)
            if (metadata.st_dev, metadata.st_ino) != (current.st_dev, current.st_ino):
                raise BatchScopeError("persisted quote path changed during read")
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            raise BatchScopeError("persisted quote cannot be resolved") from exc
        return quote

    def close(self) -> None:
        descriptor = getattr(self, "_root_fd", None)
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
            self._root_fd = None
        if self._owns_parent:
            descriptor = getattr(self, "_parent_fd", None)
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
                self._parent_fd = None

    def _assert_identity(self) -> None:
        current = os.stat("quotes", dir_fd=self._pinned_parent_fd, follow_symlinks=False)
        pinned = os.fstat(self._root_fd)
        if (
            not stat.S_ISDIR(current.st_mode)
            or current.st_uid != os.getuid()
            or stat.S_IMODE(current.st_mode) != 0o700
            or (current.st_dev, current.st_ino) != (pinned.st_dev, pinned.st_ino)
            or (pinned.st_dev, pinned.st_ino) != (self._identity.st_dev, self._identity.st_ino)
        ):
            raise BatchScopeError("quote directory identity changed")


class VideoBatchAllowance:
    """Activate and irreversibly consume an exact, non-expandable quote."""

    def __init__(
        self,
        root: Path,
        *,
        seal_key_store: Any | None = None,
        quote_resolver: Any | None = None,
        project_store: Any | None = None,
        rights_service: Any | None = None,
        now: Any | None = None,
        quote_max_age_seconds: int = 86400,
    ) -> None:
        self._root = Path(root)
        self._allowances = self._root / "allowances"
        self._activations = self._root / "activations"
        self._seal_key_store = seal_key_store
        self._quote_resolver = quote_resolver
        self._owns_seal_key_store = seal_key_store is None
        self._owns_quote_resolver = quote_resolver is None
        self._project_store = project_store
        self._rights_service = rights_service
        self._now = now or (lambda: datetime.now(timezone.utc))
        if isinstance(quote_max_age_seconds, bool) or not isinstance(quote_max_age_seconds, int) or quote_max_age_seconds < 1:
            raise ValueError("quote_max_age_seconds must be a positive integer")
        self._quote_max_age = timedelta(seconds=quote_max_age_seconds)
        self._thread_lock = threading.RLock()
        self._closed = False
        directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        self._parent_fd = self._root_fd = self._allowances_fd = self._activations_fd = None
        try:
            self._root.parent.mkdir(parents=True, exist_ok=True)
            self._parent_fd = os.open(self._root.parent, directory_flags)
            expected_root = None
            try:
                os.mkdir(self._root.name, 0o700, dir_fd=self._parent_fd)
                expected_root = os.stat(
                    self._root.name, dir_fd=self._parent_fd, follow_symlinks=False
                )
            except FileExistsError:
                expected_root = os.stat(self._root.name, dir_fd=self._parent_fd, follow_symlinks=False)
                if (
                    not stat.S_ISDIR(expected_root.st_mode)
                    or expected_root.st_uid != os.getuid()
                    or stat.S_IMODE(expected_root.st_mode) != 0o700
                ):
                    raise BatchScopeError("allowance root ownership, type, or mode is unsafe")
            self._root_fd = os.open(self._root.name, directory_flags, dir_fd=self._parent_fd)
            root_metadata = os.fstat(self._root_fd)
            if (
                not stat.S_ISDIR(root_metadata.st_mode)
                or root_metadata.st_uid != os.getuid()
                or stat.S_IMODE(root_metadata.st_mode) != 0o700
                or expected_root is not None
                and (root_metadata.st_dev, root_metadata.st_ino) != (expected_root.st_dev, expected_root.st_ino)
            ):
                raise BatchScopeError("allowance root ownership, type, mode, or identity is unsafe")
            child_expectations = {}
            for name in ("allowances", "activations"):
                try:
                    os.mkdir(name, 0o700, dir_fd=self._root_fd)
                except FileExistsError:
                    expected = os.stat(name, dir_fd=self._root_fd, follow_symlinks=False)
                    if (
                        not stat.S_ISDIR(expected.st_mode)
                        or expected.st_uid != os.getuid()
                        or stat.S_IMODE(expected.st_mode) != 0o700
                    ):
                        raise BatchScopeError("allowance child directory ownership, type, or mode is unsafe")
                    child_expectations[name] = expected
            self._allowances_fd = os.open("allowances", directory_flags, dir_fd=self._root_fd)
            self._activations_fd = os.open("activations", directory_flags, dir_fd=self._root_fd)
            for name, descriptor in (("allowances", self._allowances_fd), ("activations", self._activations_fd)):
                metadata = os.fstat(descriptor)
                expected = child_expectations.get(name)
                if (
                    not stat.S_ISDIR(metadata.st_mode)
                    or metadata.st_uid != os.getuid()
                    or stat.S_IMODE(metadata.st_mode) != 0o700
                    or expected is not None
                    and (metadata.st_dev, metadata.st_ino) != (expected.st_dev, expected.st_ino)
                ):
                    raise BatchScopeError("allowance child directory ownership, type, mode, or identity is unsafe")
            self._parent_identity = os.fstat(self._parent_fd)
            self._root_identity = os.fstat(self._root_fd)
            self._allowances_identity = os.fstat(self._allowances_fd)
            self._activations_identity = os.fstat(self._activations_fd)
            if self._seal_key_store is None:
                self._seal_key_store = FileSealKeyStore()
            if self._quote_resolver is None:
                self._quote_resolver = LocalQuoteResolver(self._root, parent_fd=self._root_fd)
        except Exception as exc:
            self.close()
            if isinstance(exc, BatchScopeError):
                raise
            raise BatchScopeError("allowance directory initialization is unsafe") from exc

    def close(self) -> None:
        """Wait for local operations, then idempotently close owned descriptors."""
        with self._thread_lock:
            if self._closed:
                return
            self._closed = True
            for field in ("_activations_fd", "_allowances_fd", "_root_fd", "_parent_fd"):
                descriptor = getattr(self, field, None)
                if descriptor is not None:
                    try:
                        os.close(descriptor)
                    except OSError:
                        pass
                    setattr(self, field, None)
            if self._owns_quote_resolver and isinstance(self._quote_resolver, LocalQuoteResolver):
                self._quote_resolver.close()
            if self._owns_seal_key_store and isinstance(self._seal_key_store, FileSealKeyStore):
                self._seal_key_store.close()

    def activate(self, quote: Mapping[str, Any], approver: Any) -> str:
        """Obtain native approval once and persist the exact batch allowance."""
        quote_copy = self._copy_json(quote)
        self._validate_quote_for_activation(quote_copy)
        self._revalidate_rights(quote_copy)
        quote_fingerprint = quote_copy["quote_fingerprint"]
        with self._exclusive_lock():
            key = self._seal_key_store.load(allow_create=not self._allowance_names())
            activation_path = self._activations / f"{quote_fingerprint}.json"
            if self._exists_at(self._activations_fd, activation_path.name) or any(
                self._load_name(name, key=key)["quote_fingerprint"] == quote_fingerprint
                for name in self._allowance_names()
            ):
                raise AllowanceAlreadyActivatedError("quote approval was already activated")
            quote_identity = self._persist_quote(quote_copy)
            if self._copy_json(self._quote_resolver.resolve(copy.deepcopy(quote_identity))) != quote_copy:
                raise BatchScopeError("persisted exact quote changed before native confirmation")
            approval_request = self._approval_request(quote_copy)
            confirmation_request = copy.deepcopy(approval_request)
            approval_bytes = self._canonical_bytes(confirmation_request)
            if approver.confirm_video_batch(confirmation_request) != "native-video-batch-confirmed":
                raise BatchScopeError("native whole-batch approval was not granted")
            if self._canonical_bytes(confirmation_request) != approval_bytes:
                raise BatchScopeError("native approver changed the exact batch envelope")
            allowance_id = "ba_" + secrets.token_hex(16)
            timestamp = _now_iso()
            requests = self._flatten_requests(quote_copy)
            allowance: dict[str, Any] = {
                "schema_version": "1.0", "allowance_id": allowance_id, "state": "active",
                "project_id": quote_copy["project_id"], "quote_version": quote_copy["quote_version"],
                "quote_fingerprint": quote_fingerprint, "quote_identity": quote_identity,
                "source_sha256": quote_copy["source_sha256"],
                "analysis_version": quote_copy["analysis_version"], "design_version": quote_copy["design_version"],
                "design_fingerprint": quote_copy["design_fingerprint"],
                "creative_mode": quote_copy["creative_mode"], "audio_policy": quote_copy["audio_policy"],
                "destination": quote_copy["output_destination"],
                "output_profile": copy.deepcopy(quote_copy["output_profile"]),
                "capability_snapshot_fingerprint": quote_copy["capability_snapshot_fingerprint"],
                "cost_basis": copy.deepcopy(quote_copy["cost_basis"]),
                "item_count": quote_copy["item_count"], "task_count": quote_copy["task_count"],
                "reserved_retry_count": quote_copy["reserved_retry_count"],
                "total_credit_ceiling": quote_copy["total_credit_ceiling"], "consumed_credits": 0,
                "requests": requests, "reservations": [], "activated_at": timestamp,
                "history": [{"state": "active", "at": timestamp}],
                "seal_key_id": hashlib.sha256(key).hexdigest(),
            }
            if quote_copy["creative_mode"] == "authorized_replication":
                allowance["rights_receipt_id"] = quote_copy["rights_receipt_id"]
                allowance["rights_receipt_fingerprint"] = quote_copy["rights_receipt_fingerprint"]
            self._seal(allowance, key)
            try:
                # Revalidate immediately before publication: the native dialog may have
                # remained open across expiry or a receipt/design replacement.
                self._validate_quote_for_activation(quote_copy)
                if self._copy_json(self._quote_resolver.resolve(copy.deepcopy(quote_identity))) != quote_copy:
                    raise BatchScopeError("persisted exact quote changed during native confirmation")
                self._revalidate_rights(quote_copy)
                self._atomic_write_at(self._allowances_fd, f"{allowance_id}.json", allowance, allowance_id=allowance_id, operation="activation")
                self._atomic_write_at(self._activations_fd, activation_path.name, {"allowance_id": allowance_id, "quote_fingerprint": quote_fingerprint}, allowance_id=allowance_id, operation="activation-index")
            except BatchScopeError:
                raise
            except Exception as exc:
                raise AllowanceCommitIndeterminateError(allowance_id, "activation") from exc
            return allowance_id

    def assert_quote(self, allowance_id: str, quote: Mapping[str, Any]) -> None:
        """Reject any quote other than the exact approved canonical quote."""
        allowance = self.get(allowance_id)
        quote_copy = self._copy_json(quote)
        try:
            validate_batch_quote(quote_copy)
        except (ContractValidationError, PlanningError, TypeError, ValueError) as exc:
            raise BatchScopeError("quote is invalid or outside the approved batch envelope") from exc
        if quote_copy != self._resolve_quote(allowance) or quote_copy["quote_fingerprint"] != allowance["quote_fingerprint"]:
            raise BatchScopeError("quote is outside the approved batch envelope")

    def reserve(self, allowance_id: str, *, shot_id: str, attempt: int, request_fingerprint: str) -> dict[str, Any]:
        """Consume one exact pre-enumerated reservation under an exclusive file lock."""
        if (
            not isinstance(shot_id, str)
            or isinstance(attempt, bool)
            or not isinstance(attempt, int)
            or not isinstance(request_fingerprint, str)
        ):
            raise BatchScopeError("reservation tuple has invalid types")
        with self._exclusive_lock():
            key = self._seal_key_store.load(allow_create=False)
            allowance = self._load_allowance(allowance_id, key=key)
            item = next((entry for entry in allowance["requests"] if entry["request_fingerprint"] == request_fingerprint), None)
            if item is None or item["shot_id"] != shot_id or item["attempt"] != attempt:
                raise BatchScopeError("request is outside the approved batch envelope")
            if any(
                reservation["request_fingerprint"] == request_fingerprint
                for other in self._all_allowances(key)
                for reservation in other["reservations"]
            ) or any(
                (reservation["shot_id"], reservation["attempt"]) == (shot_id, attempt)
                for reservation in allowance["reservations"]
            ):
                raise ReservationConsumedError("the exact request reservation is already consumed")
            new_total = allowance["consumed_credits"] + item["credit_ceiling"]
            if new_total > allowance["total_credit_ceiling"]:
                raise BudgetExceededError("reservation exceeds the approved credit ceiling")
            timestamp = _now_iso()
            reservation = {
                "reservation_id": "br_" + secrets.token_hex(16), "allowance_id": allowance_id, "shot_id": shot_id,
                "attempt": attempt, "request_fingerprint": request_fingerprint,
                "credit_ceiling": item["credit_ceiling"], "state": "reserved", "reserved_at": timestamp,
                "history": [{"state": "reserved", "at": timestamp}],
            }
            allowance["reservations"].append(reservation)
            allowance["consumed_credits"] = new_total
            if len(allowance["reservations"]) == len(allowance["requests"]):
                allowance["state"] = "exhausted"
            allowance["history"].append({"state": "reserved", "at": timestamp, "reservation_id": reservation["reservation_id"]})
            self._seal(allowance, key)
            self._atomic_write_at(self._allowances_fd, f"{allowance_id}.json", allowance, allowance_id=allowance_id, operation="reservation")
            return copy.deepcopy(reservation)

    def commit(self, reservation_id: str, submit_id: str) -> dict[str, Any]:
        """Bind a consumed reservation to the opaque provider submit identifier."""
        if not _RESERVATION_ID.fullmatch(reservation_id) or not isinstance(submit_id, str) or _SUBMIT_ID.fullmatch(submit_id) is None:
            raise BatchScopeError("invalid reservation or submit identifier")
        return self._transition_reservation(reservation_id, "committed", submit_id=submit_id)

    def mark_ambiguous(self, reservation_id: str, error_code: str, *, submit_id: str | None = None) -> dict[str, Any]:
        """Irreversibly record an unknown result after the invocation boundary."""
        if not _RESERVATION_ID.fullmatch(reservation_id) or not isinstance(error_code, str) or _ERROR_CODE.fullmatch(error_code) is None:
            raise BatchScopeError("invalid reservation or ambiguity code")
        if submit_id is not None and (not isinstance(submit_id, str) or _SUBMIT_ID.fullmatch(submit_id) is None):
            raise BatchScopeError("invalid ambiguous submit identifier")
        details = {
            "error_code": error_code,
            "required_action": "query" if submit_id is not None else "manual_review",
        }
        if submit_id is not None:
            details["submit_id"] = submit_id
        return self._transition_reservation(reservation_id, "ambiguous", **details)

    def get(self, allowance_id: str) -> dict[str, Any]:
        """Return a validated copy of one durable allowance."""
        with self._exclusive_lock():
            key = self._seal_key_store.load(allow_create=False)
            return copy.deepcopy(self._load_allowance(allowance_id, key=key))

    def _transition_reservation(self, reservation_id: str, state: str, **details: str) -> dict[str, Any]:
        with self._exclusive_lock():
            key = self._seal_key_store.load(allow_create=False)
            loaded = [(name, self._load_name(name, key=key)) for name in self._allowance_names()]
            for name, allowance in loaded:
                reservation = next((item for item in allowance["reservations"] if item["reservation_id"] == reservation_id), None)
                if reservation is None:
                    continue
                submit_id = details.get("submit_id")
                if submit_id is not None and any(
                    other["reservation_id"] != reservation_id and other.get("submit_id") == submit_id
                    for _, candidate in loaded
                    for other in candidate["reservations"]
                ):
                    raise ReservationConsumedError("submit identifier is already bound to another reservation")
                if reservation["state"] != "reserved":
                    if reservation["state"] == state and all(reservation.get(key) == value for key, value in details.items()):
                        return copy.deepcopy(reservation)
                    raise ReservationConsumedError("reservation already crossed its terminal boundary")
                timestamp = _now_iso()
                reservation["state"] = state
                reservation.update(details)
                event = {"state": state, "at": timestamp, **details}
                reservation["history"].append(event)
                allowance["history"].append({"state": state, "at": timestamp, "reservation_id": reservation_id, **details})
                self._seal(allowance, key)
                self._atomic_write_at(self._allowances_fd, name, allowance, allowance_id=allowance["allowance_id"], operation=state)
                return copy.deepcopy(reservation)
        raise AllowanceNotFoundError("reservation does not exist")

    def _validate_quote_for_activation(self, quote: Mapping[str, Any]) -> None:
        literal_total = quote_total(quote.get("items", [])) if isinstance(quote.get("items"), list) else -1
        if quote.get("total_credit_ceiling") != literal_total:
            raise BudgetExceededError("declared total does not equal request ceilings")
        try:
            validate_batch_quote(quote)
        except (ContractValidationError, PlanningError, TypeError, ValueError) as exc:
            raise BatchScopeError("invalid batch quote") from exc
        try:
            quoted_at = parse_rfc3339(quote["quoted_at"], label="quoted_at")
            recorded_at = parse_rfc3339(quote["cost_basis"]["recorded_at"], label="cost_basis.recorded_at")
            current = self._now()
            if isinstance(current, str):
                current = parse_rfc3339(current, label="now")
            current = current.astimezone(timezone.utc)
        except (AttributeError, TypeError, ValueError) as exc:
            raise BatchScopeError("quote freshness evidence is invalid") from exc
        for label, timestamp in (("quoted_at", quoted_at), ("cost_basis.recorded_at", recorded_at)):
            if timestamp > current + timedelta(minutes=5) or current - timestamp > self._quote_max_age:
                raise BatchScopeError(f"{label} is stale or from the future")
        fingerprints = [
            attempt["request_fingerprint"]
            for item in quote["items"]
            for attempt in item["attempts"]
        ]
        if len(fingerprints) != len(set(fingerprints)):
            raise BatchScopeError("request fingerprints must be unique across the approved batch")
        tuples = [
            (item["shot_id"], attempt["attempt_number"])
            for item in quote["items"]
            for attempt in item["attempts"]
        ]
        if len(tuples) != len(set(tuples)):
            raise BatchScopeError("shot attempt tuples must be unique within the approved batch")
        if quote["creative_mode"] == "authorized_replication":
            if not isinstance(quote.get("rights_receipt_id"), str) or not isinstance(quote.get("rights_receipt_fingerprint"), str):
                raise BatchScopeError("replication quote lacks exact rights receipt binding")
        elif "rights_receipt_id" in quote or "rights_receipt_fingerprint" in quote:
            raise BatchScopeError("original redesign must not carry rights receipt fields")

    @staticmethod
    def _flatten_requests(quote: Mapping[str, Any]) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for item in quote["items"]:
            for attempt in item["attempts"]:
                request = attempt["request"]
                entries.append({
                    "shot_id": item["shot_id"], "attempt": attempt["attempt_number"], "mode": item["mode"],
                    "model": request.get("model"), "video_resolution": request["video_resolution"],
                    "duration_seconds": request["duration_seconds"],
                    "request_fingerprint": attempt["request_fingerprint"],
                    "credit_ceiling": attempt["credit_ceiling"],
                })
        return entries

    @classmethod
    def _approval_request(cls, quote: Mapping[str, Any]) -> dict[str, Any]:
        request = {
            "action": "activate-video-batch-allowance", "project_id": quote["project_id"],
            "quote_version": quote["quote_version"], "quote_fingerprint": quote["quote_fingerprint"],
            "source_sha256": quote["source_sha256"], "analysis_version": quote["analysis_version"],
            "design_version": quote["design_version"], "design_fingerprint": quote["design_fingerprint"],
            "creative_mode": quote["creative_mode"], "audio_policy": quote["audio_policy"],
            "machine_fingerprint": quote["machine_fingerprint"],
            "capability_snapshot_fingerprint": quote["capability_snapshot_fingerprint"],
            "shot_count": quote["item_count"], "task_count": quote["task_count"],
            "reserved_retry_count": quote["reserved_retry_count"],
            "target_total_duration_seconds": quote["target_total_duration_seconds"],
            "total_credit_ceiling": quote["total_credit_ceiling"], "destination": quote["output_destination"],
            "cost_basis": copy.deepcopy(quote["cost_basis"]),
            "quoted_at": quote["quoted_at"],
            "output_profile": copy.deepcopy(quote["output_profile"]), "items": copy.deepcopy(quote["items"]),
        }
        if quote["creative_mode"] == "authorized_replication":
            request["rights_receipt_id"] = quote["rights_receipt_id"]
            request["rights_receipt_fingerprint"] = quote["rights_receipt_fingerprint"]
        return request

    @staticmethod
    def _rights_binding(quote: Mapping[str, Any]) -> str | None:
        value = quote.get("rights_receipt_fingerprint")
        return value if isinstance(value, str) else None

    def _load_allowance(self, allowance_id: str, *, key: bytes) -> dict[str, Any]:
        self._allowance_path(allowance_id)
        return self._load_name(f"{allowance_id}.json", key=key)

    def _load_name(self, name: str, *, key: bytes) -> dict[str, Any]:
        if re.fullmatch(r"ba_[a-f0-9]{32}\.json", name) is None:
            raise BatchScopeError("unsafe allowance file name")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(name, flags, dir_fd=self._allowances_fd)
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid() or stat.S_IMODE(before.st_mode) != 0o600:
                os.close(descriptor)
                raise BatchScopeError("allowance file ownership, type, or mode is unsafe")
            with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            current = os.stat(name, dir_fd=self._allowances_fd, follow_symlinks=False)
            if (before.st_dev, before.st_ino) != (current.st_dev, current.st_ino):
                raise BatchScopeError("allowance path changed during read")
        except BatchScopeError:
            raise
        except (OSError, json.JSONDecodeError) as exc:
            raise BatchScopeError("allowance durable state is missing or corrupt") from exc
        return self._validate_loaded(payload, key=key)

    def _load_path(self, path: Path, *, key: bytes) -> dict[str, Any]:
        try:
            metadata = path.lstat()
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o600
            ):
                raise BatchScopeError("allowance file ownership, type, or mode is unsafe")
            payload = json.loads(path.read_text(encoding="utf-8"))
        except BatchScopeError:
            raise
        except (OSError, json.JSONDecodeError) as exc:
            raise BatchScopeError("allowance durable state is missing or corrupt") from exc
        return self._validate_loaded(payload, key=key)

    def _validate_loaded(self, payload: Any, *, key: bytes) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise BatchScopeError("allowance durable state is corrupt")
        seal = payload.get("seal")
        core = {field: value for field, value in payload.items() if field != "seal"}
        if payload.get("seal_key_id") != hashlib.sha256(key).hexdigest():
            raise SealKeyUnavailableError("allowance was sealed with a different key")
        expected = hmac.new(key, _SEAL_DOMAIN + self._canonical_bytes(core), "sha256").hexdigest()
        if not isinstance(seal, str) or not hmac.compare_digest(seal, expected):
            raise BatchScopeError("allowance HMAC seal verification failed")
        try:
            validate_contract(payload, "video_batch_allowance.schema.json")
        except ContractValidationError as exc:
            raise BatchScopeError("allowance durable state violates its contract") from exc
        if payload["consumed_credits"] != sum(item["credit_ceiling"] for item in payload["reservations"]):
            raise BatchScopeError("allowance consumed credits are corrupt")
        if payload["consumed_credits"] > payload["total_credit_ceiling"]:
            raise BudgetExceededError("allowance exceeds its approved ceiling")
        self._validate_history(payload)
        self._validate_against_quote(payload)
        return payload

    def _allowance_path(self, allowance_id: str) -> Path:
        if not isinstance(allowance_id, str) or not _ALLOWANCE_ID.fullmatch(allowance_id):
            raise AllowanceNotFoundError("invalid allowance identifier")
        return self._allowances / f"{allowance_id}.json"

    @staticmethod
    def _copy_json(payload: Mapping[str, Any]) -> dict[str, Any]:
        try:
            copied = json.loads(json.dumps(dict(payload), ensure_ascii=False, allow_nan=False))
        except (TypeError, ValueError, OverflowError) as exc:
            raise BatchScopeError("batch quote is not canonical JSON") from exc
        return copied

    @classmethod
    def _seal(cls, payload: dict[str, Any], key: bytes) -> None:
        payload.pop("seal", None)
        payload["seal"] = hmac.new(key, _SEAL_DOMAIN + cls._canonical_bytes(payload), "sha256").hexdigest()

    def _persist_quote(self, quote: Mapping[str, Any]) -> dict[str, Any]:
        result = self._quote_resolver.persist(copy.deepcopy(dict(quote)))
        identity = LocalQuoteResolver.identity(quote)
        if result is not None and result != identity:
            raise BatchScopeError("quote resolver returned a mismatched immutable identity")
        return identity

    def _resolve_quote(self, allowance: Mapping[str, Any]) -> dict[str, Any]:
        try:
            quote = self._copy_json(self._quote_resolver.resolve(copy.deepcopy(allowance["quote_identity"])))
            validate_batch_quote(quote)
        except (AttributeError, ContractValidationError, PlanningError, TypeError, ValueError, KeyError) as exc:
            raise BatchScopeError("trusted exact quote resolution failed") from exc
        identity = LocalQuoteResolver.identity(quote)
        if identity != allowance["quote_identity"]:
            raise BatchScopeError("resolved quote identity or fingerprint changed")
        return quote

    def _validate_against_quote(self, allowance: Mapping[str, Any]) -> None:
        quote = self._resolve_quote(allowance)
        expected = {
            "project_id": quote["project_id"], "quote_version": quote["quote_version"],
            "quote_fingerprint": quote["quote_fingerprint"], "source_sha256": quote["source_sha256"],
            "analysis_version": quote["analysis_version"], "design_version": quote["design_version"],
            "design_fingerprint": quote["design_fingerprint"], "creative_mode": quote["creative_mode"],
            "audio_policy": quote["audio_policy"], "destination": quote["output_destination"],
            "output_profile": quote["output_profile"], "capability_snapshot_fingerprint": quote["capability_snapshot_fingerprint"],
            "cost_basis": quote["cost_basis"], "total_credit_ceiling": quote["total_credit_ceiling"],
            "item_count": quote["item_count"], "task_count": quote["task_count"],
            "reserved_retry_count": quote["reserved_retry_count"],
            "requests": self._flatten_requests(quote),
        }
        if quote["creative_mode"] == "authorized_replication":
            expected["rights_receipt_id"] = quote["rights_receipt_id"]
            expected["rights_receipt_fingerprint"] = quote["rights_receipt_fingerprint"]
        if any(allowance.get(field) != value for field, value in expected.items()):
            raise BatchScopeError("allowance differs from the trusted immutable quote")

    def _atomic_write_at(self, directory_fd: int, name: str, payload: Mapping[str, Any], *, allowance_id: str, operation: str) -> None:
        if re.fullmatch(r"(?:ba_[a-f0-9]{32}|[a-f0-9]{64})\.json", name) is None:
            raise BatchScopeError("unsafe durable file name")
        temporary = f".{name}.{secrets.token_hex(8)}"
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=directory_fd)
        replaced = False
        try:
            os.fchmod(descriptor, 0o600)
            encoded = self._canonical_bytes(payload)
            _write_all(descriptor, encoded)
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = -1
            os.replace(temporary, name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
            replaced = True
            os.fsync(directory_fd)
            verify = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=directory_fd)
            try:
                metadata = os.fstat(verify)
                if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o600:
                    raise OSError("published durable file identity is unsafe")
            finally:
                os.close(verify)
        except Exception as exc:
            if descriptor >= 0:
                os.close(descriptor)
            try:
                os.unlink(temporary, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
            if replaced:
                raise AllowanceCommitIndeterminateError(allowance_id, operation) from exc
            raise

    def _atomic_write(self, path: Path, payload: Mapping[str, Any], *, allowance_id: str, operation: str) -> None:
        directory_fd = self._allowances_fd if path.parent == self._allowances else self._activations_fd
        self._atomic_write_at(directory_fd, path.name, payload, allowance_id=allowance_id, operation=operation)

    def _revalidate_rights(self, quote: Mapping[str, Any]) -> None:
        if self._project_store is None:
            raise BatchScopeError("activation requires trusted durable design revalidation")
        try:
            design = self._project_store.read_version(
                quote["project_id"], "redesign", quote["design_version"], "video_redesign.schema.json"
            )
            expected_design = {
                "project_id": quote["project_id"], "version": quote["design_version"],
                "design_fingerprint": quote["design_fingerprint"],
                "source_sha256": quote["source_sha256"],
                "analysis_version": quote["analysis_version"],
            }
            if any(design.get(field) != value for field, value in expected_design.items()):
                raise BatchScopeError("durable design binding changed")
            if quote["creative_mode"] == "original_redesign":
                return
            if self._rights_service is None:
                raise BatchScopeError("authorized replication requires trusted rights revalidation")
            receipt = self._project_store.find_version_by_field(
                quote["project_id"], "rights_receipt", field="receipt_id",
                value=quote["rights_receipt_id"], schema_name="video_rights_receipt.schema.json",
            )
            if canonical_fingerprint(receipt) != quote["rights_receipt_fingerprint"]:
                raise BatchScopeError("durable rights receipt fingerprint changed")
            if any(
                receipt.get(field) != quote[field]
                for field in ("receipt_id", "project_id", "source_sha256", "creative_mode", "design_fingerprint")
                if field != "receipt_id"
            ) or receipt.get("receipt_id") != quote["rights_receipt_id"]:
                raise BatchScopeError("durable rights receipt binding changed")
            payload = design["payload"]
            self._rights_service.assert_scope(receipt, required=set(payload["preserve"]), binding={
                "project_id": quote["project_id"], "source_sha256": quote["source_sha256"],
                "creative_mode": quote["creative_mode"], "design_fingerprint": quote["design_fingerprint"],
                "required_media": payload["required_media"], "purpose": payload["purpose"],
                "audience": payload["audience"], "territory": payload["territory"],
            })
        except BatchScopeError:
            raise
        except Exception as exc:
            raise BatchScopeError("rights receipt no longer covers exact batch scope") from exc

    def _allowance_names(self) -> list[str]:
        return sorted(name for name in os.listdir(self._allowances_fd) if re.fullmatch(r"ba_[a-f0-9]{32}\.json", name))

    def _all_allowances(self, key: bytes) -> list[dict[str, Any]]:
        return [self._load_name(name, key=key) for name in self._allowance_names()]

    @staticmethod
    def _exists_at(directory_fd: int, name: str) -> bool:
        try:
            os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            return True
        except FileNotFoundError:
            return False

    def _assert_root_identity(self) -> None:
        if any(getattr(self, field, None) is None for field in (
            "_parent_fd", "_root_fd", "_allowances_fd", "_activations_fd"
        )):
            raise BatchScopeError("allowance store is closed")
        current_parent = self._root.parent.lstat()
        pinned_parent = os.fstat(self._parent_fd)
        if (
            not stat.S_ISDIR(current_parent.st_mode)
            or (current_parent.st_dev, current_parent.st_ino) != (pinned_parent.st_dev, pinned_parent.st_ino)
            or (pinned_parent.st_dev, pinned_parent.st_ino) != (self._parent_identity.st_dev, self._parent_identity.st_ino)
        ):
            raise BatchScopeError("allowance parent identity changed")
        current = os.stat(self._root.name, dir_fd=self._parent_fd, follow_symlinks=False)
        pinned = os.fstat(self._root_fd)
        if (
            not stat.S_ISDIR(current.st_mode)
            or current.st_uid != os.getuid()
            or stat.S_IMODE(current.st_mode) != 0o700
            or (current.st_dev, current.st_ino) != (pinned.st_dev, pinned.st_ino)
            or (pinned.st_dev, pinned.st_ino) != (self._root_identity.st_dev, self._root_identity.st_ino)
        ):
            raise BatchScopeError("allowance root identity changed")
        for name, descriptor, expected in (
            ("allowances", self._allowances_fd, self._allowances_identity),
            ("activations", self._activations_fd, self._activations_identity),
        ):
            current_child = os.stat(name, dir_fd=self._root_fd, follow_symlinks=False)
            pinned_child = os.fstat(descriptor)
            if (
                not stat.S_ISDIR(current_child.st_mode)
                or current_child.st_uid != os.getuid()
                or stat.S_IMODE(current_child.st_mode) != 0o700
                or (current_child.st_dev, current_child.st_ino) != (pinned_child.st_dev, pinned_child.st_ino)
                or (pinned_child.st_dev, pinned_child.st_ino) != (expected.st_dev, expected.st_ino)
            ):
                raise BatchScopeError(f"allowance {name} directory identity changed")

    @staticmethod
    def _validate_history(allowance: Mapping[str, Any]) -> None:
        allowance_history = allowance["history"]
        if (
            not allowance_history
            or allowance_history[0] != {"state": "active", "at": allowance["activated_at"]}
            or any(event.get("state") == "active" for event in allowance_history[1:])
        ):
            raise BatchScopeError("allowance history must have exactly one initial active event")
        reservation_ids: set[str] = set()
        fingerprints: set[str] = set()
        tuples: set[tuple[str, int]] = set()
        histories: dict[str, list[Mapping[str, Any]]] = {}
        approved = {
            (request["shot_id"], request["attempt"], request["request_fingerprint"], request["credit_ceiling"])
            for request in allowance["requests"]
        }
        for reservation in allowance["reservations"]:
            reservation_id = reservation["reservation_id"]
            fingerprint = reservation["request_fingerprint"]
            identity = (reservation["shot_id"], reservation["attempt"])
            if reservation_id in reservation_ids or fingerprint in fingerprints or identity in tuples:
                raise BatchScopeError("reservation history contains duplicate identities")
            reservation_ids.add(reservation_id)
            fingerprints.add(fingerprint)
            tuples.add(identity)
            history = reservation["history"]
            if (
                (reservation["shot_id"], reservation["attempt"], fingerprint, reservation["credit_ceiling"]) not in approved
                or reservation.get("allowance_id") != allowance["allowance_id"]
            ):
                raise BatchScopeError("reservation is not an exact approved request")
            if not history or history[0] != {"state": "reserved", "at": reservation["reserved_at"]}:
                raise BatchScopeError("reservation history must begin at reserved")
            terminal = [event for event in history[1:] if event.get("state") in {"committed", "ambiguous"}]
            if reservation["state"] == "reserved" and (terminal or len(history) != 1):
                raise BatchScopeError("reserved entry has terminal history")
            if reservation["state"] in {"committed", "ambiguous"} and (
                len(history) != 2 or len(terminal) != 1 or terminal[0].get("state") != reservation["state"]
            ):
                raise BatchScopeError("terminal reservation history is inconsistent")
            if reservation["state"] == "committed" and terminal[0].get("submit_id") != reservation.get("submit_id"):
                raise BatchScopeError("committed submit identity differs from history")
            if reservation["state"] == "ambiguous":
                expected_action = "query" if reservation.get("submit_id") else "manual_review"
                if (
                    reservation.get("required_action") != expected_action
                    or terminal[0].get("required_action") != expected_action
                    or terminal[0].get("error_code") != reservation.get("error_code")
                    or terminal[0].get("submit_id") != reservation.get("submit_id")
                ):
                    raise BatchScopeError("ambiguous recovery action is inconsistent")
            histories[reservation_id] = history
        consumed_events = {reservation_id: 0 for reservation_id in reservation_ids}
        for event in allowance_history[1:]:
            linked = event.get("reservation_id")
            if linked not in reservation_ids:
                raise BatchScopeError("allowance history references an unknown reservation")
            index = consumed_events[linked]
            history = histories[linked]
            if index >= len(history) or event != {**history[index], "reservation_id": linked}:
                raise BatchScopeError("allowance and reservation histories disagree or are reordered")
            consumed_events[linked] += 1
        if any(consumed_events[reservation_id] != len(histories[reservation_id]) for reservation_id in reservation_ids):
            raise BatchScopeError("allowance history is truncated")
        exhausted = len(allowance["reservations"]) == len(allowance["requests"])
        if (allowance["state"] == "exhausted") != exhausted:
            raise BatchScopeError("allowance exhausted state does not match consumed requests")

    @staticmethod
    def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
        return json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

    @contextmanager
    def _exclusive_lock(self) -> Iterator[None]:
        with self._thread_lock:
            if self._closed:
                raise BatchScopeError("allowance store is closed")
            self._assert_root_identity()
            fcntl.flock(self._root_fd, fcntl.LOCK_EX)
            try:
                self._assert_root_identity()
                yield
                self._assert_root_identity()
            finally:
                fcntl.flock(self._root_fd, fcntl.LOCK_UN)


__all__ = [
    "AllowanceAlreadyActivatedError", "AllowanceCommitIndeterminateError", "AllowanceNotFoundError", "BatchScopeError", "FileSealKeyStore",
    "BudgetExceededError", "ReservationConsumedError", "VideoBatchAllowance",
    "SealKeyUnavailableError",
]
