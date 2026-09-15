"""Durable submit-once orchestration for Blender preview to Seedance."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from design_handoff import ArtifactMismatchError, verify_result_artifact
from handoff_validator import validate_artifact
from job_ledger import ALLOWED_TRANSITIONS, JobLedger, JobState, QuoteInputs


class DesignClient(Protocol):
    def invoke(self, action: str, arguments: dict) -> dict: ...


@dataclass(frozen=True)
class OrchestrationResult:
    state: JobState
    blocked_reason: str | None
    actions: tuple[str, ...]
    artifact: dict | None = None


def _result(ledger: JobLedger, actions: list[str], blocked_reason=None, artifact=None):
    return OrchestrationResult(
        state=JobState(ledger.read()["state"]),
        blocked_reason=blocked_reason,
        actions=tuple(actions),
        artifact=artifact,
    )


def _invoke(client: DesignClient, actions: list[str], action: str, arguments: dict) -> dict:
    actions.append(action)
    result = client.invoke(action, arguments)
    if not isinstance(result, dict):
        raise RuntimeError(f"design action {action!r} returned a non-object")
    return result


def _request_fingerprint(request: dict, preview_sha256: str) -> str:
    bound = {"request": request, "preview_sha256": preview_sha256}
    encoded = json.dumps(bound, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_until_blocked(
    ledger: JobLedger,
    design_client: DesignClient,
    *,
    preview_receipt: dict,
    request: dict,
) -> OrchestrationResult:
    """Advance one job until completion or a real external/user gate."""
    actions: list[str] = []
    current_file = Path(str(preview_receipt.get("path", "")))
    errors = validate_artifact(preview_receipt, current_file)
    if errors:
        state = JobState(ledger.read()["state"])
        if JobState.FAILED in ALLOWED_TRANSITIONS[state]:
            ledger.transition(JobState.FAILED, error_category="hash_mismatch")
        return _result(ledger, actions, "PREVIEW_INVALID")

    state = JobState(ledger.read()["state"])
    if state is JobState.DRAFT:
        ledger.transition(
            JobState.DCC_SELECTED,
            selected_companion={
                "plugin_id": preview_receipt["producer_plugin"],
                "version": preview_receipt["producer_version"],
                "contract_version": preview_receipt["schema_version"],
            },
        )
        ledger.transition(
            JobState.PREVIEW_SPECIFIED,
            preview={
                "artifact_id": preview_receipt["artifact_id"],
                "sha256": preview_receipt["sha256"],
                "producer_plugin": preview_receipt["producer_plugin"],
                "producer_version": preview_receipt["producer_version"],
            },
        )
        ledger.transition(JobState.PREVIEW_VALIDATED, preview_hash_validated=True)
        state = JobState.PREVIEW_VALIDATED

    if state is JobState.PREVIEW_VALIDATED:
        status = _invoke(design_client, actions, "status", {})
        if status.get("ready") is not True:
            return _result(ledger, actions, "DESIGN_NOT_READY")
        account = _invoke(design_client, actions, "account", {})
        if account.get("ready") is not True:
            return _result(ledger, actions, "ACCOUNT_NOT_READY")
        ledger.transition(
            JobState.CAPABILITY_RESOLVED,
            resolved_capability={"model": request["model"]},
        )
        state = JobState.CAPABILITY_RESOLVED

    if state is JobState.CAPABILITY_RESOLVED:
        quote = _invoke(design_client, actions, "quote", dict(request))
        policy = ledger.read().get("execution_policy") or {}
        if quote.get("quote_available") is not True:
            if policy.get("max_charge") is not None or not policy.get("permit_unquoted_exact_request", False):
                return _result(ledger, actions, "QUOTE_UNAVAILABLE")
            quote = {"amount": "0", "currency": "UNQUOTED", "quote_available": False}
        quote_inputs = QuoteInputs(
            prompt=str(request["prompt"]),
            model=str(request["model"]),
            resolution=str(request["resolution"]),
            ratio=str(request.get("ratio") or "16:9"),
            duration_seconds=float(request["duration_seconds"]),
            reference_artifact_ids=(str(preview_receipt["artifact_id"]),),
        )
        ledger.record_quote(quote_inputs, quote)
        ledger.transition(JobState.APPROVED, approved_by="policy", approved_at=ledger.read()["updated_at"])
        state = JobState.APPROVED

    if state is JobState.APPROVED:
        policy = ledger.read().get("execution_policy") or {}
        if not policy.get("permit_one_submission") or not policy.get("permit_reference_upload"):
            return _result(ledger, actions, "SUBMISSION_NOT_AUTHORIZED")
        fingerprint = _request_fingerprint(request, preview_receipt["sha256"])
        payload = ledger.read()
        intent = payload.get("submission_intent")
        if intent is not None:
            return _result(ledger, actions, "SUBMISSION_RECONCILIATION_REQUIRED")
        payload["submission_intent"] = {"request_fingerprint": fingerprint, "status": "pending"}
        ledger.write(payload)
        submit = _invoke(
            design_client,
            actions,
            "submit",
            {**request, "preview": {"path": str(current_file), "sha256": preview_receipt["sha256"]}},
        )
        submit_id = submit.get("submit_id")
        if not isinstance(submit_id, str) or not submit_id:
            payload = ledger.read()
            payload["submission_intent"]["status"] = "unknown"
            ledger.write(payload)
            return _result(ledger, actions, "SUBMISSION_UNKNOWN")
        ledger.transition(
            JobState.SUBMITTED,
            submission_intent={"request_fingerprint": fingerprint, "status": "accepted"},
            submit={
                "design_submit_id": submit_id,
                "submitted_at": ledger.read()["updated_at"],
                "design_status": "submitted",
            },
        )
        state = JobState.SUBMITTED

    if state is JobState.SUBMITTED:
        ledger.transition(JobState.QUERYING)
        state = JobState.QUERYING
    elif state is JobState.UNKNOWN:
        ledger.transition(JobState.QUERYING)
        state = JobState.QUERYING

    if state is JobState.QUERYING:
        submit_id = ledger.read()["submit"]["design_submit_id"]
        query_arguments = {"submit_id": submit_id}
        for key in ("poll_seconds", "download_dir", "approved_roots"):
            if key in request:
                query_arguments[key] = request[key]
        query = _invoke(design_client, actions, "query", query_arguments)
        remote_status = str(query.get("status", "unknown")).lower()
        if remote_status in {"querying", "submitted", "running"}:
            return _result(ledger, actions)
        if remote_status == "unknown":
            ledger.transition(JobState.UNKNOWN, error_category="unknown")
            return _result(ledger, actions, "REMOTE_UNKNOWN")
        if remote_status in {"failed", "fail"}:
            ledger.transition(JobState.FAILED, error_category="design_error")
            return _result(ledger, actions, "REMOTE_FAILED")
        if remote_status in {"success", "succeeded"}:
            policy = ledger.read().get("execution_policy") or {}
            download_root = policy.get("download_root")
            approved_roots = [str(download_root)] if download_root else None
            try:
                artifact = verify_result_artifact(
                    query.get("artifact"), approved_roots=approved_roots
                )
            except ArtifactMismatchError:
                ledger.transition(JobState.FAILED, error_category="hash_mismatch")
                return _result(ledger, actions, "FINAL_ARTIFACT_INVALID")
            ledger.transition(
                JobState.COMPLETED,
                result={
                    "artifact_id": f"{submit_id}_result",
                    "sha256": artifact["sha256"],
                    "path": artifact["path"],
                },
            )
            return _result(ledger, actions, artifact=artifact)
        ledger.transition(JobState.UNKNOWN, error_category="unknown")
        return _result(ledger, actions, "REMOTE_UNKNOWN")

    return _result(ledger, actions)


__all__ = ["DesignClient", "OrchestrationResult", "run_until_blocked"]
