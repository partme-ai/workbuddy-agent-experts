"""Dreamina Design handoff for codex-dreamina-3d.

Talks to codex-dreamina-design via argv + JSON only. The orchestrator never
imports the design plugin's modules. All operations go through the public
receipt interface (capabilities, quote, approve, submit, query, download).

The handoff refuses to send DCC scene data: only the validated preview
receipt reference (artifact_id + sha256), the user prompt, and the quote
inputs are transmitted.

The submit ID returned by the design plugin is persisted to the job ledger
before any "submission success" report is made. A duplicate submit returns
the previously-stored submit ID; no new paid action is taken.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 60.0


class DesignHandoffError(RuntimeError):
    pass


class MissingDesignPluginError(DesignHandoffError):
    pass


class WebPrerequisiteError(DesignHandoffError):
    pass


class QuoteMismatchError(DesignHandoffError):
    pass


class ApprovalRejectedError(DesignHandoffError):
    pass


class UnknownStateError(DesignHandoffError):
    pass


class ArtifactMismatchError(DesignHandoffError):
    pass


def verify_result_artifact(artifact: dict, *, approved_roots: Sequence[str] | None = None) -> dict:
    """Require and independently verify a downloaded result artifact.

    The path is resolved before any check and, when ``approved_roots`` is
    supplied, the resolved path must sit inside one of them. Resolving first is
    what makes the check meaningful: ``is_symlink()`` only inspects the final
    component, so a symlinked *intermediate* directory would otherwise let the
    artifact escape the approved download root. Containment is evaluated on
    resolved paths on both sides, which keeps this correct on hosts where the
    temp directory itself is reached through a link (for example ``/tmp`` ->
    ``/private/tmp`` on macOS).
    """
    if not isinstance(artifact, dict):
        raise ArtifactMismatchError("succeeded result has no artifact object")
    raw_path = artifact.get("path")
    declared_hash = artifact.get("sha256")
    if not isinstance(raw_path, str) or not raw_path:
        raise ArtifactMismatchError("succeeded result artifact is missing path")
    if not isinstance(declared_hash, str) or len(declared_hash) != 64 or any(
        char not in "0123456789abcdef" for char in declared_hash
    ):
        raise ArtifactMismatchError("succeeded result artifact is missing a lowercase sha256")

    path = Path(raw_path).resolve()
    if not path.is_file():
        raise ArtifactMismatchError(f"result artifact is not a regular file: {path}")

    if approved_roots:
        allowed = [Path(root).expanduser().resolve() for root in approved_roots]
        if not any(path == root or root in path.parents for root in allowed):
            raise ArtifactMismatchError(
                f"result artifact {path} is outside the approved download roots {allowed}"
            )

    size = path.stat().st_size
    if size <= 0:
        raise ArtifactMismatchError(f"result artifact is empty: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    actual_hash = digest.hexdigest()
    if actual_hash != declared_hash:
        raise ArtifactMismatchError(
            f"declared sha256 {declared_hash} != on-disk {actual_hash} for {path}"
        )
    return {"path": str(path), "sha256": actual_hash, "bytes": size}


def _new_temp_request_path(request_dir: Path, label: str) -> Path:
    fd, name = tempfile.mkstemp(prefix=f"design_{label}_", suffix=".json", dir=str(request_dir))
    os.close(fd)
    return Path(name)


def _run_design(
    *,
    executable: str,
    mode: str,
    payload: dict,
    request_dir: Path,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    output_path: Path | None = None,
) -> tuple[subprocess.CompletedProcess, Path, Path]:
    """Run the design adapter and return (proc, request_path, receipt_path)."""
    if not executable or not Path(executable).exists():
        raise MissingDesignPluginError(f"design plugin executable not found: {executable!r}")
    request_path = _new_temp_request_path(request_dir, mode)
    receipt_path = request_path.with_suffix(".receipt.json")
    request_path.write_text(json.dumps(payload))
    argv = [executable, "--mode", mode, "--request", str(request_path), "--receipt", str(receipt_path), "--state-dir", str(request_dir)]
    if output_path is not None:
        argv.extend(["--output", str(output_path)])
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired as exc:
        # Convert timeout into an Unknown-state signal so the caller can
        # route to a query-only path.
        raise UnknownStateError(f"design adapter {mode!r} timed out after {timeout_seconds}s") from exc
    return proc, request_path, receipt_path


def _read_receipt(receipt_path: Path) -> dict:
    if not receipt_path.is_file():
        raise DesignHandoffError("design adapter produced no receipt")
    try:
        return json.loads(receipt_path.read_text())
    except json.JSONDecodeError as exc:
        raise DesignHandoffError(f"design receipt not valid JSON: {exc}")


def design_handoff(
    *,
    executable: str,
    mode: str,
    payload: dict,
    request_dir: Path,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    output_path: Path | None = None,
) -> dict:
    """Invoke the public Dreamina Design receipt interface.

    The mode is one of: ``capabilities``, ``quote``, ``approve``, ``submit``,
    ``query``, ``download``. Failures are classified into specific subclasses
    so the orchestrator can route them to the correct ledger transition.
    """
    request_dir.mkdir(parents=True, exist_ok=True)
    proc, _request_path, receipt_path = _run_design(
        executable=executable,
        mode=mode,
        payload=payload,
        request_dir=request_dir,
        timeout_seconds=timeout_seconds,
        output_path=output_path,
    )
    receipt = _read_receipt(receipt_path) if receipt_path.is_file() else {}

    if mode == "capabilities":
        if proc.returncode != 0 and "web_login_required" in json.dumps(receipt):
            raise WebPrerequisiteError("Dreamina web login required before capability resolution")
        caps = receipt.get("capabilities") or []
        if not caps:
            raise DesignHandoffError(f"design plugin returned no capabilities: {receipt}")
        return receipt

    if mode == "quote":
        if proc.returncode != 0 or not receipt:
            raise QuoteMismatchError(f"quote rejected: {receipt or proc.stderr}")
        # Verify the returned quote echoes every quote-binding input.
        inputs = payload.get("quote_inputs") or {}
        for key in ("model", "resolution", "ratio", "duration_seconds"):
            if key not in receipt:
                raise QuoteMismatchError(f"quote missing {key!r}: {receipt}")
            if str(receipt[key]) != str(inputs.get(key)):
                raise QuoteMismatchError(
                    f"quote {key!r}={receipt[key]!r} differs from inputs {inputs.get(key)!r}"
                )
        if "mismatch_marker" in receipt:
            raise QuoteMismatchError(f"quote contained mismatch_marker: {receipt['mismatch_marker']!r}")
        return receipt

    if mode == "approve":
        status = receipt.get("status")
        if status == "approved":
            return receipt
        raise ApprovalRejectedError(f"approval {status!r}")

    if mode == "submit":
        if proc.returncode == 3 and receipt.get("status") == "duplicate":
            # Reuse the previously stored submit id; never create a new paid action.
            return {"design_submit_id": receipt.get("existing_submit_id"), "status": "duplicate"}
        if proc.returncode != 0 or not receipt.get("design_submit_id"):
            if receipt.get("status") == "unknown" or proc.returncode == 2:
                raise UnknownStateError(f"submit returned unknown: {receipt}")
            raise DesignHandoffError(f"submit failed: {receipt or proc.stderr}")
        return receipt

    if mode == "query":
        status = receipt.get("status")
        if status == "unknown" or proc.returncode == 2:
            raise UnknownStateError(f"query returned unknown: {receipt}")
        if status == "succeeded":
            receipt["artifact"] = verify_result_artifact(receipt.get("artifact"))
            return receipt
        raise DesignHandoffError(f"unexpected query result: {receipt}")

    if mode == "download":
        if proc.returncode != 0 or output_path is None or not output_path.is_file():
            raise DesignHandoffError("download failed")
        return verify_result_artifact(
            {"path": str(output_path), "sha256": payload.get("expected_sha256")}
        )

    raise DesignHandoffError(f"unsupported mode: {mode!r}")


def build_multimodal_request(
    *,
    preview_artifact_id: str,
    preview_sha256: str,
    prompt: str,
    quote_inputs: dict,
) -> dict:
    """Compose a normalized multimodal request for the design plugin.

    The request deliberately omits any DCC scene path, source code, or
    internal plugin objects; only the validated preview receipt reference
    (immutable artifact id + sha256), the user prompt, and the quote inputs
    cross the boundary.
    """
    return {
        "preview": {
            "artifact_id": preview_artifact_id,
            "sha256": preview_sha256,
        },
        "prompt": prompt,
        "quote_inputs": dict(quote_inputs),
    }


__all__ = [
    "DesignHandoffError",
    "MissingDesignPluginError",
    "WebPrerequisiteError",
    "QuoteMismatchError",
    "ApprovalRejectedError",
    "UnknownStateError",
    "ArtifactMismatchError",
    "verify_result_artifact",
    "design_handoff",
    "build_multimodal_request",
]
