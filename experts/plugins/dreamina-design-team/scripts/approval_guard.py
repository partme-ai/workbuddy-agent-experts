"""Approval guard for Dreamina Design (Task 5).

Wraps ``approval_receipt`` persistence with session boundaries, replay
detection, expiry enforcement, and strict non-secret storage.

Storage guarantees:

* Credential-shaped keys (``token``, ``api_key``, ``password``, …) are
  silently stripped before persistence.
* Account-snapshot keys (``account_id``, ``membership_tier``,
  ``credits_balance``) cause the receipt to be rejected outright —
  they must never reach the ledger.
* Prompts marked private (or any field whose name contains a private
  field token) are redacted before write.
* All writes are atomic (write-to-temp + rename) so a crash never
  leaves a half-written receipt.
* Receipts survive process restart; the same ``ApprovalGuard`` instance
  can be reconstructed from the root directory.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import tempfile
import fcntl
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from scripts.image_service import build_request_fingerprint


# Silently stripped before persistence. These are common credential
# shapes that callers may forward accidentally.
STRIPPED_KEYS = {
    "token",
    "secret",
    "api_key",
    "apikey",
    "access_key",
    "session_token",
    "cookie",
    "private_key",
    "password",
    "auth",
    "authorization",
}

# Rejected outright. These are account-snapshot fields that the plugin
# never accepts in an approval receipt.
REJECTED_KEYS = {
    "account_id",
    "membership_tier",
    "credits_balance",
    "account_snapshot",
}


class ApprovalGuardError(Exception):
    """Base class for approval guard errors."""


class SessionExistsError(ApprovalGuardError):
    """A session with this label already exists."""


class SessionNotFoundError(ApprovalGuardError):
    """The requested session does not exist."""


class RequestChangedError(ApprovalGuardError):
    """The replayed request does not match the originally approved one."""


class ApprovalReplayMismatchError(ApprovalGuardError):
    """The recorded receipt's fingerprint does not match the request."""


class ApprovalExpiredError(ApprovalGuardError):
    """The approval receipt's expires_at is in the past."""


class SecretFieldError(ApprovalGuardError):
    """A forbidden account-snapshot field was supplied."""


class ApprovalConsumedError(ApprovalGuardError):
    """An approval was already consumed by a paid submission attempt."""


SESSION_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\- ]{0,63}$")
SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed


def _scrub(value: Any, private_tokens: tuple[str, ...]) -> Any:
    """Recursively strip forbidden keys and redact private tokens."""
    if isinstance(value, Mapping):
        cleaned: dict[str, Any] = {}
        for key, inner in value.items():
            lkey = str(key).lower()
            if lkey in {k.lower() for k in REJECTED_KEYS}:
                raise SecretFieldError(f"forbidden account field in receipt: {key}")
            if lkey in {k.lower() for k in STRIPPED_KEYS}:
                # Silently strip credential-shaped keys.
                continue
            if any(token and token in str(key).lower() for token in private_tokens):
                cleaned[key] = "[REDACTED]"
                continue
            cleaned[key] = _scrub(inner, private_tokens)
        return cleaned
    if isinstance(value, list):
        return [_scrub(item, private_tokens) for item in value]
    return value


class ApprovalGuard:
    """Session-scoped approval receipt registry with non-secret persistence."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)
        self._sessions_dir = self._root / "sessions"
        self._sessions_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------
    def create_session(self, *, label: str) -> str:
        if not SESSION_LABEL_PATTERN.fullmatch(label):
            raise ValueError(f"invalid session label: {label!r}")
        with self._exclusive_lock():
            index_path = self._sessions_dir / "index.json"
            index = self._load_json(index_path, default={"labels": {}})
            if label in index["labels"]:
                raise SessionExistsError(f"session already exists: {label}")
            session_id = secrets.token_urlsafe(12)
            index["labels"][label] = session_id
            self._atomic_write(index_path, index)
            session_dir = self._sessions_dir / session_id
            session_dir.mkdir(parents=True, exist_ok=False)
            meta = {
                "session_id": session_id,
                "label": label,
                "created_at": _now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            self._atomic_write(session_dir / "session.json", meta)
            return session_id

    def list_sessions(self) -> list[str]:
        index = self._load_json(self._sessions_dir / "index.json", default={"labels": {}})
        return sorted(index["labels"].values())

    def select_session(self, session_id: str) -> dict[str, Any]:
        session_dir = self._session_dir(session_id)
        if not (session_dir / "session.json").is_file():
            raise SessionNotFoundError(session_id)
        return self._load_json(session_dir / "session.json")

    def delete_session(self, session_id: str) -> None:
        session_dir = self._session_dir(session_id)
        with self._exclusive_lock():
            if not (session_dir / "session.json").is_file():
                raise SessionNotFoundError(session_id)
            for entry in sorted(session_dir.rglob("*"), reverse=True):
                if entry.is_symlink():
                    entry.unlink()
                elif entry.is_file():
                    entry.unlink()
                elif entry.is_dir():
                    entry.rmdir()
            session_dir.rmdir()
            index = self._load_json(self._sessions_dir / "index.json", default={"labels": {}})
            for label, sid in list(index["labels"].items()):
                if sid == session_id:
                    del index["labels"][label]
                    break
            self._atomic_write(self._sessions_dir / "index.json", index)

    # ------------------------------------------------------------------
    # Approval recording and replay
    # ------------------------------------------------------------------
    def record_approval(
        self,
        session_id: str,
        *,
        request: Mapping[str, Any],
        receipt: Mapping[str, Any],
        private_fields: Iterable[str] = (),
        fingerprint_builder: Callable[[Mapping[str, Any]], str] = build_request_fingerprint,
    ) -> str:
        session_dir = self._session_dir(session_id)
        if not (session_dir / "session.json").is_file():
            raise SessionNotFoundError(session_id)
        fingerprint = fingerprint_builder(dict(request))
        private_tokens = tuple(str(token).lower() for token in private_fields)
        scrubbed = _scrub(dict(receipt), private_tokens)
        # Preserve the caller-supplied request_fingerprint rather than
        # silently rewriting it; that lets assert_approval_for detect a
        # mismatched receipt on replay.
        scrubbed.setdefault("request_fingerprint", fingerprint)
        issued_at = _now()
        scrubbed["approved_at"] = issued_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        if scrubbed.get("request_fingerprint") != fingerprint:
            raise ApprovalReplayMismatchError(
                f"approval fingerprint mismatch: expected {fingerprint}"
            )
        for required in ("approver", "acknowledged_cost", "acknowledged_scope"):
            if not scrubbed.get(required):
                raise ApprovalReplayMismatchError(f"approval missing required field: {required}")
        if scrubbed["acknowledged_cost"] not in {"credits", "membership", "free"}:
            raise ApprovalReplayMismatchError("acknowledged_cost is not supported")
        self._validate_scope(request, scrubbed["acknowledged_scope"])
        approval_id = secrets.token_urlsafe(24)
        scrubbed["approval_id"] = approval_id
        scrubbed["consumed_at"] = None
        max_expiry = issued_at + timedelta(minutes=5)
        requested_expiry = scrubbed.get("expires_at")
        if requested_expiry:
            try:
                parsed_expiry = _parse_iso(str(requested_expiry))
            except ValueError as exc:
                raise ApprovalReplayMismatchError("expires_at is not valid RFC 3339") from exc
            if parsed_expiry > max_expiry:
                raise ApprovalReplayMismatchError("approval expiry exceeds five-minute maximum")
        else:
            scrubbed["expires_at"] = max_expiry.strftime("%Y-%m-%dT%H:%M:%SZ")
        # Also redact any explicit private field values from the original request
        # that callers flagged. We never persist the raw value, only the redaction
        # marker.
        if any(field in request for field in private_fields):
            scrubbed["redacted_fields"] = sorted(private_fields)
        receipt_path = session_dir / "approvals" / f"{fingerprint}.json"
        with self._exclusive_lock():
            existing = self._load_json(receipt_path)
            if existing and not existing.get("consumed_at"):
                raise SessionExistsError(
                    "an unconsumed approval already exists for this exact request"
                )
            self._atomic_write(receipt_path, scrubbed)
        return approval_id

    def consume_approval(
        self,
        session_id: str,
        *,
        request: Mapping[str, Any],
        approval_id: str,
        fingerprint_builder: Callable[[Mapping[str, Any]], str] = build_request_fingerprint,
    ) -> dict[str, Any]:
        """Atomically validate and consume a single-use approval."""
        session_dir = self._session_dir(session_id)
        fingerprint = fingerprint_builder(dict(request))
        receipt_path = session_dir / "approvals" / f"{fingerprint}.json"
        with self._exclusive_lock():
            if not receipt_path.is_file():
                raise RequestChangedError(
                    f"no approval recorded for request fingerprint {fingerprint}"
                )
            receipt = self._load_json(receipt_path)
            if not secrets.compare_digest(str(receipt.get("approval_id", "")), approval_id):
                raise ApprovalReplayMismatchError("approval_id does not match issued approval")
            if receipt.get("request_fingerprint") != fingerprint:
                raise ApprovalReplayMismatchError(
                    f"approval fingerprint mismatch: expected {fingerprint}"
                )
            if receipt.get("consumed_at"):
                raise ApprovalConsumedError("approval was already consumed")
            expires_at = receipt.get("expires_at")
            if expires_at and _parse_iso(expires_at) <= _now():
                raise ApprovalExpiredError(f"approval expired at {expires_at}")
            receipt["consumed_at"] = _now().strftime("%Y-%m-%dT%H:%M:%SZ")
            self._atomic_write(receipt_path, receipt)
            return receipt

    def assert_approval_for(self, session_id: str, *, request: Mapping[str, Any]) -> dict[str, Any]:
        session_dir = self._session_dir(session_id)
        if not (session_dir / "session.json").is_file():
            raise SessionNotFoundError(session_id)
        fingerprint = build_request_fingerprint(dict(request))
        receipt_path = session_dir / "approvals" / f"{fingerprint}.json"
        if not receipt_path.is_file():
            raise RequestChangedError(
                f"no approval recorded for request fingerprint {fingerprint}"
            )
        receipt = self._load_json(receipt_path)
        if receipt.get("request_fingerprint") != fingerprint:
            raise ApprovalReplayMismatchError(
                f"approval fingerprint mismatch: expected {fingerprint}"
            )
        expires_at = receipt.get("expires_at")
        if expires_at:
            try:
                expiry = _parse_iso(expires_at)
            except ValueError as exc:
                raise ApprovalReplayMismatchError(f"invalid expires_at: {expires_at}") from exc
            if expiry <= _now():
                raise ApprovalExpiredError(f"approval expired at {expires_at}")
        return receipt

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @staticmethod
    def _load_json(path: Path, default: Any = None) -> Any:
        if not path.is_file():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _session_dir(self, session_id: str) -> Path:
        if not SESSION_ID_PATTERN.fullmatch(session_id):
            raise ValueError(f"unsafe session_id: {session_id!r}")
        candidate = self._sessions_dir / session_id
        if candidate.is_symlink():
            raise ValueError(f"session path must not be a symlink: {session_id!r}")
        resolved_parent = candidate.parent.resolve()
        if resolved_parent != self._sessions_dir.resolve():
            raise ValueError(f"session path escapes sessions root: {session_id!r}")
        return candidate

    @staticmethod
    def _validate_scope(request: Mapping[str, Any], scope: Any) -> None:
        if not isinstance(scope, Mapping):
            raise ApprovalReplayMismatchError("acknowledged_scope must be an object")
        allowed = {"count", "model", "resolution", "ratio", "duration_seconds"}
        unknown = set(scope) - allowed
        if unknown:
            raise ApprovalReplayMismatchError(
                f"acknowledged_scope contains unsupported fields: {sorted(unknown)}"
            )
        expected = {
            "count": int(request.get("count", 1)),
            "model": request.get("model"),
            "resolution": request.get("resolution_type", request.get("video_resolution")),
            "ratio": request.get("ratio"),
            "duration_seconds": request.get("duration_seconds"),
        }
        for key, value in expected.items():
            if value is not None and scope.get(key) != value:
                raise ApprovalReplayMismatchError(
                    f"acknowledged_scope.{key} does not match the exact request"
                )
            if value is None and key in scope:
                raise ApprovalReplayMismatchError(
                    f"acknowledged_scope.{key} must be omitted when absent from request"
                )

    @staticmethod
    def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix=path.name, dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    @contextmanager
    def _exclusive_lock(self):
        lock_path = self._root / ".approval.lock"
        with open(lock_path, "a+b") as handle:
            os.chmod(lock_path, 0o600)
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


__all__ = [
    "ApprovalExpiredError",
    "ApprovalConsumedError",
    "ApprovalGuard",
    "ApprovalReplayMismatchError",
    "RequestChangedError",
    "SecretFieldError",
    "SessionExistsError",
    "SessionNotFoundError",
]
