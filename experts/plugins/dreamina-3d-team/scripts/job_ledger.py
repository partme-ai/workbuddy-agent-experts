"""End-to-end job ledger for codex-dreamina-3d.

The ledger enforces the state machine defined in
docs/Codex-Dreamina-3D-Plugin-Architecture.md and the spec:

  Draft -> DccSelected -> PreviewSpecified -> PreviewValidated ->
  CapabilityResolved -> Quoted -> Approved -> Submitted -> Querying ->
  Completed | Failed | Unknown

Updates are atomic (write-to-temp + fsync + os.replace) with a monotonic
revision. Only non-secret IDs, hashes, states, timestamps, and error
categories are stored; any attempt to transition through an illegal edge or
to change a quote-binding field without invalidating the quote is rejected
closed.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "1.0.0"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_KEYS = {"token", "api_key", "apikey", "password", "secret", "authorization", "credit_card"}


class JobState(str, Enum):
    DRAFT = "Draft"
    DCC_SELECTED = "DccSelected"
    PREVIEW_SPECIFIED = "PreviewSpecified"
    PREVIEW_VALIDATED = "PreviewValidated"
    CAPABILITY_RESOLVED = "CapabilityResolved"
    QUOTED = "Quoted"
    APPROVED = "Approved"
    SUBMITTED = "Submitted"
    QUERYING = "Querying"
    COMPLETED = "Completed"
    FAILED = "Failed"
    UNKNOWN = "Unknown"


# State machine: who is allowed to transition where.
ALLOWED_TRANSITIONS: dict[JobState, frozenset[JobState]] = {
    JobState.DRAFT: frozenset({JobState.DCC_SELECTED, JobState.FAILED}),
    JobState.DCC_SELECTED: frozenset({JobState.PREVIEW_SPECIFIED, JobState.FAILED}),
    JobState.PREVIEW_SPECIFIED: frozenset({JobState.PREVIEW_VALIDATED, JobState.FAILED}),
    JobState.PREVIEW_VALIDATED: frozenset({JobState.CAPABILITY_RESOLVED, JobState.PREVIEW_SPECIFIED, JobState.FAILED}),
    JobState.CAPABILITY_RESOLVED: frozenset({JobState.QUOTED, JobState.FAILED}),
    JobState.QUOTED: frozenset({JobState.APPROVED, JobState.PREVIEW_VALIDATED, JobState.FAILED}),
    JobState.APPROVED: frozenset({JobState.SUBMITTED, JobState.PREVIEW_VALIDATED, JobState.FAILED}),
    JobState.SUBMITTED: frozenset({JobState.QUERYING, JobState.UNKNOWN, JobState.FAILED}),
    # Query-only: once submitted, the job may never return to Submitted, so a
    # restarted orchestrator cannot re-submit a paid action.
    JobState.QUERYING: frozenset({JobState.COMPLETED, JobState.UNKNOWN, JobState.FAILED}),
    JobState.COMPLETED: frozenset(),
    JobState.FAILED: frozenset(),
    JobState.UNKNOWN: frozenset({JobState.QUERYING, JobState.FAILED}),
}


class InvalidTransitionError(RuntimeError):
    pass


class StaleReceiptError(RuntimeError):
    pass


class LedgerCorruptError(RuntimeError):
    pass


class BudgetExceededError(RuntimeError):
    """Raised before approval when an automatic policy's quote exceeds its cap."""


class ExecutionMode(str, Enum):
    """Controls whether a job pauses for every review or runs within one envelope."""

    INTERACTIVE = "interactive"
    AUTO_WITH_BUDGET = "auto_with_budget"
    AUTO_EXACT_REQUEST = "auto_exact_request"
    REVIEW_ONLY = "review_only"


@dataclass(frozen=True)
class ExecutionPolicy:
    """Non-secret, immutable authorization envelope for a 3D generation job."""

    mode: ExecutionMode
    max_charge: Decimal | None = None
    permit_one_submission: bool = False
    permit_reference_upload: bool = False
    permit_unquoted_exact_request: bool = False
    download_root: str | None = None

    @classmethod
    def auto_with_budget(
        cls,
        max_charge: str | Decimal,
        permit_one_submission: bool,
        permit_reference_upload: bool,
        permit_unquoted_exact_request: bool = False,
        download_root: str | None = None,
    ) -> "ExecutionPolicy":
        try:
            amount = Decimal(str(max_charge))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("max_charge must be decimal") from exc
        if not amount.is_finite() or amount < 0:
            raise ValueError("max_charge must be non-negative")
        if not permit_one_submission:
            raise ValueError("auto_with_budget requires permit_one_submission")
        return cls(
            ExecutionMode.AUTO_WITH_BUDGET,
            max_charge=amount,
            permit_one_submission=True,
            permit_reference_upload=bool(permit_reference_upload),
            permit_unquoted_exact_request=bool(permit_unquoted_exact_request),
            download_root=download_root,
        )

    @classmethod
    def auto_exact_request(
        cls,
        *,
        permit_one_submission: bool,
        permit_reference_upload: bool,
        download_root: str | None = None,
    ) -> "ExecutionPolicy":
        """Authorize one exact request when the provider has no quote API."""
        if not permit_one_submission:
            raise ValueError("auto_exact_request requires permit_one_submission")
        return cls(
            ExecutionMode.AUTO_EXACT_REQUEST,
            max_charge=None,
            permit_one_submission=True,
            permit_reference_upload=bool(permit_reference_upload),
            permit_unquoted_exact_request=True,
            download_root=download_root,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the policy without account, credential, or prompt content."""
        return {
            "mode": self.mode.value,
            "max_charge": str(self.max_charge) if self.max_charge is not None else None,
            "permit_one_submission": self.permit_one_submission,
            "permit_reference_upload": self.permit_reference_upload,
            "permit_unquoted_exact_request": self.permit_unquoted_exact_request,
            "download_root": self.download_root,
        }


@dataclass(frozen=True)
class QuoteInputs:
    prompt: str
    model: str
    resolution: str
    ratio: str
    duration_seconds: float
    reference_artifact_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "model": self.model,
            "resolution": self.resolution,
            "ratio": self.ratio,
            "duration_seconds": self.duration_seconds,
            "reference_artifact_ids": list(self.reference_artifact_ids),
        }


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _scrub(value: Any) -> None:
    """Walk a value and raise LedgerCorruptError if any forbidden key is present."""
    if isinstance(value, dict):
        for k, v in value.items():
            if k.lower() in FORBIDDEN_KEYS:
                raise LedgerCorruptError(f"forbidden key in ledger payload: {k!r}")
            _scrub(v)
    elif isinstance(value, list):
        for item in value:
            _scrub(item)


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def new_job(job_id: str, execution_policy: ExecutionPolicy | None = None) -> dict:
    if not re.match(r"^[a-z0-9][a-z0-9_-]{2,63}$", job_id):
        raise ValueError("job_id must be a lowercase kebab-case identifier")
    now = _utcnow()
    return {
        "schema_version": SCHEMA_VERSION,
        "job_id": job_id,
        "state": JobState.DRAFT.value,
        "revision": 1,
        "created_at": now,
        "updated_at": now,
        "selected_companion": None,
        "preview": None,
        "quote_inputs": None,
        "quote": None,
        "approval": None,
        "submit": None,
        "result": None,
        "submission_intent": None,
        "error_category": None,
        "execution_policy": (execution_policy or ExecutionPolicy(ExecutionMode.INTERACTIVE)).to_dict(),
        "history": [],
    }


def load_ledger(path: Path) -> dict:
    """Load and structurally validate a ledger file. Raises on corruption."""
    raw = path.read_text(encoding="utf-8")
    payload = json.loads(raw)  # may raise JSONDecodeError
    if not isinstance(payload, dict):
        raise LedgerCorruptError("ledger root must be an object")
    for required in ("schema_version", "job_id", "state", "revision"):
        if required not in payload:
            raise LedgerCorruptError(f"missing ledger field: {required}")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise LedgerCorruptError(f"unsupported ledger schema_version: {payload['schema_version']!r}")
    _scrub(payload)
    return payload


class JobLedger:
    """A read/write handle to a job ledger file.

    All writes go through ``write``/``transition``; both perform atomic
    replace. ``transition`` checks the state-machine edges.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> dict:
        if not self.path.is_file():
            raise FileNotFoundError(self.path)
        return load_ledger(self.path)

    def write(self, payload: dict) -> None:
        if self.path.is_file():
            existing = load_ledger(self.path)
            policy_locked = existing.get("quote") is not None or existing.get("submission_intent") is not None
            if policy_locked and payload.get("execution_policy") != existing.get("execution_policy"):
                raise InvalidTransitionError("execution policy is immutable after quoting begins")
        _scrub(payload)
        _atomic_write(self.path, payload)

    def transition(self, target: JobState, **fields: Any) -> dict:
        payload = self.read() if self.path.is_file() else new_job("uninitialized")
        current = JobState(payload["state"])
        if target not in ALLOWED_TRANSITIONS.get(current, frozenset()):
            raise InvalidTransitionError(
                f"cannot transition from {current.value} to {target.value}"
            )
        now = _utcnow()
        history = list(payload.get("history") or [])
        history.append({
            "from_state": current.value,
            "to_state": target.value,
            "at": now,
        })
        # Coerce dataclass-like values to plain dicts so json serialization works.
        for key, value in fields.items():
            if hasattr(value, "to_dict"):
                fields[key] = value.to_dict()
        payload.update(fields)
        payload["state"] = target.value
        payload["revision"] = int(payload.get("revision", 1)) + 1
        payload["updated_at"] = now
        payload["history"] = history
        self.write(payload)
        return payload

    def invalidate_quote(
        self,
        *,
        reason: str,
        new_preview_hash: str | None = None,
    ) -> dict:
        """Walk the job back to PreviewValidated (or PreviewSpecified if the
        preview hash itself changed) whenever a quote-binding input changed.

        Raises StaleReceiptError if the supplied preview hash is not a valid
        SHA-256 hex string.
        """
        payload = self.read()
        current = JobState(payload["state"])
        if current not in {JobState.QUOTED, JobState.APPROVED}:
            raise InvalidTransitionError(
                f"cannot invalidate quote from {current.value}; must be Quoted or Approved"
            )
        if new_preview_hash is not None and not SHA256_PATTERN.fullmatch(new_preview_hash):
            raise StaleReceiptError(f"new_preview_hash must be 64 lowercase hex chars (got {new_preview_hash!r})")

        if new_preview_hash is not None:
            preview = dict(payload.get("preview") or {})
            preview["sha256"] = new_preview_hash
            payload["preview"] = preview
            target = JobState.PREVIEW_SPECIFIED
        else:
            target = JobState.PREVIEW_VALIDATED

        now = _utcnow()
        history = list(payload.get("history") or [])
        history.append({
            "from_state": current.value,
            "to_state": target.value,
            "at": now,
            "note": f"quote invalidated: {reason}",
        })
        payload["quote_inputs"] = None
        payload["quote"] = None
        payload["approval"] = None
        payload["submit"] = None
        payload["state"] = target.value
        payload["revision"] = int(payload.get("revision", 1)) + 1
        payload["updated_at"] = now
        payload["error_category"] = "quote_changed"
        payload["history"] = history
        self.write(payload)
        return payload

    def record_quote(self, quote_inputs: QuoteInputs, quote: Mapping[str, Any]) -> dict:
        """Persist a quote only when it is within an automatic-run budget cap."""
        payload = self.read()
        if JobState(payload["state"]) is not JobState.CAPABILITY_RESOLVED:
            raise InvalidTransitionError("quote can only be recorded from CapabilityResolved")
        policy = payload.get("execution_policy") or {}
        if policy.get("mode") == ExecutionMode.AUTO_WITH_BUDGET.value:
            max_charge = Decimal(str(policy.get("max_charge")))
            try:
                observed_amount = Decimal(str(quote.get("amount")))
            except (InvalidOperation, ValueError) as exc:
                raise BudgetExceededError("automatic quote must include a decimal amount") from exc
            if not observed_amount.is_finite() or observed_amount > max_charge:
                raise BudgetExceededError(
                    f"quote amount {observed_amount} exceeds automatic budget {max_charge}"
                )
        return self.transition(JobState.QUOTED, quote_inputs=quote_inputs, quote=dict(quote))


__all__ = [
    "SCHEMA_VERSION",
    "ALLOWED_TRANSITIONS",
    "JobState",
    "InvalidTransitionError",
    "StaleReceiptError",
    "LedgerCorruptError",
    "BudgetExceededError",
    "ExecutionMode",
    "ExecutionPolicy",
    "QuoteInputs",
    "JobLedger",
    "new_job",
    "load_ledger",
]
