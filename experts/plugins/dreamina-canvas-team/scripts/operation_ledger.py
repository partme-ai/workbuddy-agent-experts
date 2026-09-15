"""Non-secret operation ledger for dreamina-canvas async submissions.

Persists only the minimum set of non-secret fields, in mode 0600 files
under <root>/operations/<profile-and-environment>/<submitId>.json.

Reconcile rules:

- Missing record + resubmittable=true → escalate to a human; never
  auto-retry.
- Missing record + no resubmittable fact → treat as "accepted by server",
  never as "absent".
- in_progress / completed → continue observing via operation status /
  wait, never call node run with a new submitId.
- Empty submitId is rejected up front.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

REQUIRED_NON_SECRET_FIELDS = (
    "projectId",
    "nodeId",
    "submitId",
    "last_known_state",
    "resubmittable",
    "request_fingerprint",
    "exit_code",
    "timestamp",
)

FORBIDDEN_FIELDS = (
    "access_token",
    "refresh_token",
    "cookie",
    "signed_url",
    "signedUrl",
    "creditConfirmationToken",
    "credit_confirmation_token",
    "storage_id",
    "storageId",
)


@dataclass
class OperationReceipt:
    project_id: str
    node_id: str
    submit_id: str
    last_known_state: str
    resubmittable: bool
    request_fingerprint: str
    exit_code: int
    timestamp: str
    extra: dict = field(default_factory=dict)


class RecoveryDecision:
    RESUME = "resume"
    ESCALATE = "escalate"
    TERMINAL_SUCCESS = "terminal_success"
    TERMINAL_FAILURE = "terminal_failure"
    REJECT_EMPTY_SUBMIT_ID = "reject_empty_submit_id"


def decide(receipt: OperationReceipt | None, submit_id: str) -> tuple[str, str]:
    """Return (action, reason)."""
    if not submit_id:
        return (RecoveryDecision.REJECT_EMPTY_SUBMIT_ID, "submitId is empty")
    if receipt is None:
        # No record on this machine; the caller must check whether
        # resubmittable=true is present in the server response. Without
        # that fact we treat as accepted.
        return (RecoveryDecision.RESUME, "no local record; treat as accepted by server")
    if receipt.last_known_state == "in_progress":
        return (RecoveryDecision.RESUME, "in_progress; continue with operation wait")
    if receipt.last_known_state == "completed":
        return (RecoveryDecision.TERMINAL_SUCCESS, "completed; switch to download")
    if receipt.last_known_state == "failed":
        return (RecoveryDecision.TERMINAL_FAILURE, "failed; surface to user")
    if receipt.last_known_state == "absent" and receipt.resubmittable:
        return (
            RecoveryDecision.ESCALATE,
            "absent + resubmittable=true; never auto-retry, escalate to user",
        )
    if receipt.last_known_state == "absent":
        return (RecoveryDecision.RESUME, "absent without resubmittable; treat as accepted")
    return (RecoveryDecision.RESUME, f"unknown state {receipt.last_known_state!r}; resume")


def persist(receipt: OperationReceipt, root: Path, profile_env: str) -> Path:
    """Atomically write the receipt to <root>/operations/<profile_env>/<submitId>.json."""
    if not receipt.submit_id:
        raise ValueError("submitId is empty; refusing to persist a non-identifiable receipt")
    raw = asdict(receipt)
    # Map dataclass field names to the canonical non-secret field names
    data = {
        "projectId": raw["project_id"],
        "nodeId": raw["node_id"],
        "submitId": raw["submit_id"],
        "last_known_state": raw["last_known_state"],
        "resubmittable": raw["resubmittable"],
        "request_fingerprint": raw["request_fingerprint"],
        "exit_code": raw["exit_code"],
        "timestamp": raw["timestamp"],
        "extra": raw["extra"],
    }
    for forbidden in FORBIDDEN_FIELDS:
        if forbidden in data or forbidden in data.get("extra", {}):
            raise ValueError(f"forbidden field {forbidden!r} in receipt; refusing to persist")
    target_dir = root / "operations" / profile_env
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{receipt.submit_id}.json"
    fd, tmp_path = tempfile.mkstemp(dir=str(target_dir), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, target)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    return target
