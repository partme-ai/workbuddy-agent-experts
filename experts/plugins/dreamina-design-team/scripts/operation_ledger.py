"""Operation ledger for Dreamina Design (Task 5).

Tracks ``OperationReceipt`` instances keyed by ``submit_id``, persisting
them atomically to disk so they survive process restarts. The ledger
also exposes:

* a cancel-support probe (argv-only CLI call);
* a query path that asks the CLI ``status <submit_id>`` before any new
  submission is attempted, preventing blind resubmission of ambiguous
  operations.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import fcntl
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.output_redactor import redact_value


TERMINAL_STATES = {"succeeded", "failed", "cancelled"}
SUBMIT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


class OperationLedgerError(Exception):
    """Base class for operation ledger errors."""


class OperationNotFoundError(OperationLedgerError):
    """The submit_id is not in the ledger."""


class AmbiguousSubmissionError(OperationLedgerError):
    """The submit_id already terminated; resubmission would be ambiguous."""


class CancelNotSupportedError(OperationLedgerError):
    """The dreamina CLI reports that cancellation is not supported."""


class DurableCommitIndeterminateError(OperationLedgerError):
    """A replace became visible but parent-directory durability is uncertain."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class OperationLedger:
    """Append-only ledger of operation receipts keyed by ``submit_id``."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)
        self._ops_dir = self._root / "operations"
        self._ops_dir.mkdir(parents=True, exist_ok=True)
        self._intents_dir = self._root / "submission_intents"
        self._intents_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._root / "index.json"
        self._batches_dir = self._root / "batches"
        self._batches_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------
    def begin_submission(
        self, *, session_id: str, mode: str, request_fingerprint: str,
        allowance_id: str | None = None, reservation_id: str | None = None,
    ) -> dict[str, Any]:
        if re.fullmatch(r"[a-f0-9]{64}", request_fingerprint) is None:
            raise ValueError("request_fingerprint must be a SHA-256 hex digest")
        path = self._intents_dir / f"{request_fingerprint}.json"
        with self._exclusive_lock():
            existing = self._load_json(path)
            if existing and existing.get("state") not in {"aborted"}:
                raise AmbiguousSubmissionError(
                    "a submission intent already exists; reconcile it before resubmitting"
                )
            intent = {
                "session_id": session_id,
                "mode": mode,
                "request_fingerprint": request_fingerprint,
                "state": "submitting",
                "created_at": _now_iso(),
                "submit_id": None,
            }
            if (allowance_id is None) != (reservation_id is None):
                raise ValueError("allowance_id and reservation_id must be provided together")
            if allowance_id is not None:
                intent["allowance_id"] = allowance_id
                intent["reservation_id"] = reservation_id
            self._atomic_write(path, intent)
            return intent

    def complete_submission_intent(
        self, *, request_fingerprint: str, submit_id: str | None,
        error_code: str | None = None, allowance_id: str | None = None,
        reservation_id: str | None = None,
    ) -> dict[str, Any]:
        path = self._intents_dir / f"{request_fingerprint}.json"
        with self._exclusive_lock():
            intent = self._load_json(path)
            if not intent:
                raise OperationNotFoundError(request_fingerprint)
            if allowance_id is not None or reservation_id is not None:
                if (intent.get("allowance_id"), intent.get("reservation_id")) != (allowance_id, reservation_id):
                    raise AmbiguousSubmissionError("submission result does not match its allowance reservation")
            intent["submit_id"] = submit_id
            intent["state"] = "accepted" if submit_id else "manual_review"
            intent["updated_at"] = _now_iso()
            if error_code:
                intent["last_error_code"] = error_code
            self._atomic_write(path, intent)
            return intent

    def abort_submission_intent(self, *, request_fingerprint: str, reason: str) -> None:
        path = self._intents_dir / f"{request_fingerprint}.json"
        with self._exclusive_lock():
            intent = self._load_json(path)
            if intent:
                intent["state"] = "aborted"
                intent["last_error_code"] = reason
                intent["updated_at"] = _now_iso()
                self._atomic_write(path, intent)

    def record(
        self,
        *,
        session_id: str,
        submit_id: str,
        mode: str,
        request_fingerprint: str,
        allowance_id: str | None = None,
        reservation_id: str | None = None,
    ) -> dict[str, Any]:
        with self._exclusive_lock():
            existing = self._read(submit_id)
            if existing is not None:
                raise AmbiguousSubmissionError(
                    f"submit_id {submit_id} is already recorded with state {existing['state']}; "
                    "query it before any new submission"
                )
            receipt = {
                "submit_id": submit_id,
                "session_id": session_id,
                "mode": mode,
                "request_fingerprint": request_fingerprint,
                "state": "queued",
                "submitted_at": _now_iso(),
                "updated_at": _now_iso(),
                "required_action": "wait",
                "history": [{"state": "queued", "at": _now_iso()}],
            }
            if (allowance_id is None) != (reservation_id is None):
                raise ValueError("allowance_id and reservation_id must be provided together")
            if allowance_id is not None:
                receipt["allowance_id"] = allowance_id
                receipt["reservation_id"] = reservation_id
            self._atomic_write(self._path_for(submit_id), receipt)
            self._index_add(submit_id, session_id)
            return receipt

    def update_state(
        self,
        *,
        submit_id: str,
        state: str,
        required_action: str | None = None,
        last_error_code: str | None = None,
    ) -> dict[str, Any]:
        with self._exclusive_lock():
            receipt = self._read(submit_id)
            if receipt is None:
                raise OperationNotFoundError(submit_id)
            if receipt.get("state") in TERMINAL_STATES and state != receipt.get("state"):
                raise AmbiguousSubmissionError(
                    f"terminal state {receipt['state']} cannot transition to {state}"
                )
            receipt["state"] = state
            receipt["updated_at"] = _now_iso()
            if required_action is not None:
                receipt["required_action"] = required_action
            if last_error_code is not None:
                receipt["last_error_code"] = last_error_code
            receipt.setdefault("history", []).append({"state": state, "at": _now_iso()})
            self._atomic_write(self._path_for(submit_id), receipt)
            return receipt

    def get(self, *, submit_id: str) -> dict[str, Any]:
        receipt = self._read(submit_id)
        if receipt is None:
            raise OperationNotFoundError(submit_id)
        return receipt

    def save_batch(self, *, project_id: str, batch_version: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Atomically persist executor state before its next external side effect."""
        if re.fullmatch(r"vp_[a-f0-9]{24}", project_id) is None or re.fullmatch(r"v[0-9]{3,}", batch_version) is None:
            raise ValueError("invalid batch identity")
        document = json.loads(json.dumps(redact_value(dict(payload))))
        with self._exclusive_lock():
            self._atomic_write(self._batches_dir / f"{project_id}-{batch_version}.json", document)
        return document

    def load_batch(self, *, project_id: str, batch_version: str) -> dict[str, Any] | None:
        """Load durable executor state after a process restart."""
        if re.fullmatch(r"vp_[a-f0-9]{24}", project_id) is None or re.fullmatch(r"v[0-9]{3,}", batch_version) is None:
            raise ValueError("invalid batch identity")
        value = self._load_json(self._batches_dir / f"{project_id}-{batch_version}.json")
        return value if isinstance(value, dict) else None

    # ------------------------------------------------------------------
    # CLI-driven discovery and querying
    # ------------------------------------------------------------------
    def discover_cancel_support(self, *, adapter: Any) -> bool:
        """Return false because the observed CLI contract has no cancel command."""
        return False

    def query(self, *, submit_id: str, adapter: Any) -> dict[str, Any]:
        if self._read(submit_id) is None:
            raise OperationNotFoundError(submit_id)
        from scripts.task_service import TaskService
        try:
            queried = TaskService(adapter).query(submit_id)
            cli_state = str(queried["status"])
        except (OSError, ValueError):
            return self.update_state(submit_id=submit_id, state="unknown",
                                     required_action="manual_review",
                                     last_error_code="INVALID_QUERY_RESULT")
        state_map = {
            "querying": ("queued", "wait"),
            "success": ("succeeded", "download"),
            "fail": ("failed", "report_failure"),
            "failed": ("failed", "report_failure"),
        }
        new_state, new_action = state_map.get(cli_state, ("unknown", "manual_review"))
        return self.update_state(
            submit_id=submit_id,
            state=new_state,
            required_action=new_action,
        )

    def cancel(self, *, submit_id: str, adapter: Any) -> dict[str, Any]:
        if self._read(submit_id) is None:
            raise OperationNotFoundError(submit_id)
        if not self.discover_cancel_support(adapter=adapter):
            raise CancelNotSupportedError(
                "dreamina CLI reports cancel_supported=false; cannot cancel"
            )
        result = adapter.run(["cancel", submit_id])
        payload = result.payload if isinstance(result.payload, Mapping) else {}
        new_state = str(payload.get("state", "cancelled"))
        return self.update_state(
            submit_id=submit_id,
            state=new_state,
            required_action="report_failure",
        )

    def poll_until_terminal(
        self,
        *,
        submit_id: str,
        adapter: Any,
        max_attempts: int = 30,
        interval_seconds: float = 1.0,
        sleep_fn: Any = time.sleep,
    ) -> dict[str, Any]:
        """Bounded query-only polling; it never invokes a generation command."""
        if max_attempts < 1 or max_attempts > 3600:
            raise ValueError("max_attempts must be between 1 and 3600")
        if interval_seconds < 0 or interval_seconds > 300:
            raise ValueError("interval_seconds must be between 0 and 300")
        for attempt in range(max_attempts):
            receipt = self.query(submit_id=submit_id, adapter=adapter)
            if receipt["state"] in TERMINAL_STATES:
                return receipt
            if attempt + 1 < max_attempts:
                sleep_fn(interval_seconds)
        return self.update_state(
            submit_id=submit_id,
            state="unknown",
            required_action="retry_query",
            last_error_code="POLL_LIMIT_REACHED",
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _path_for(self, submit_id: str) -> Path:
        if not SUBMIT_ID_PATTERN.fullmatch(submit_id):
            raise ValueError(f"unsafe submit_id: {submit_id!r}")
        return self._ops_dir / f"{submit_id}.json"

    def _read(self, submit_id: str) -> dict[str, Any] | None:
        path = self._path_for(submit_id)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _atomic_write(self, path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix=path.name, dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, path)
            directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory_fd)
            except OSError as exc:
                raise DurableCommitIndeterminateError("replace visible; directory fsync failed") from exc
            finally:
                os.close(directory_fd)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    @contextmanager
    def _exclusive_lock(self):
        lock_path = self._root / ".operation.lock"
        with open(lock_path, "a+b") as handle:
            os.chmod(lock_path, 0o600)
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _index_add(self, submit_id: str, session_id: str) -> None:
        index = self._load_json(self._index_path, default={"submits": {}})
        index["submits"][submit_id] = session_id
        self._atomic_write(self._index_path, index)

    @staticmethod
    def _load_json(path: Path, default: Any = None) -> Any:
        if not path.is_file():
            return default
        return json.loads(path.read_text(encoding="utf-8"))


__all__ = [
    "AmbiguousSubmissionError",
    "CancelNotSupportedError",
    "DurableCommitIndeterminateError",
    "OperationLedger",
    "OperationNotFoundError",
    "TERMINAL_STATES",
]
