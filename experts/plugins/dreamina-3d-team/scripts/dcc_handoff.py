"""DCC preview handoff for codex-dreamina-3d.

Talks to a codex-blender / codex-maya companion adapter via argv and JSON
contracts only. The companion's internal Python modules are NEVER imported;
the orchestrator treats the adapter as an opaque executable that consumes a
request file and emits a receipt file. The receipt is preserved verbatim and
the on-disk artifact is re-hashed independently.

Failure modes (no automatic retry):
  - adapter returns non-zero exit code              -> AdapterError
  - adapter reports unsupported media              -> UnsupportedMediaError
  - the on-disk artifact's hash no longer matches   -> StaleOutputError
  - the adapter times out, status query also times out / reports unknown
                                                     -> AdapterError(status='unknown')
  - the receipt's restoration.status != 'confirmed' -> AdapterError
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from handoff_validator import SUPPORTED_PRODUCERS, validate_artifact

DEFAULT_TIMEOUT_SECONDS = 120.0


@dataclass(frozen=True)
class PreviewSpec:
    scene: str
    camera_name: str
    frame_start: int
    frame_end: int
    output_label: str


@dataclass(frozen=True)
class InspectionResult:
    status: str
    scene: str | None = None

    @classmethod
    def from_dict(cls, payload: dict) -> "InspectionResult":
        return cls(status=str(payload.get("status", "unknown")), scene=payload.get("scene"))


class AdapterError(RuntimeError):
    def __init__(self, message: str, status: str | None = None) -> None:
        super().__init__(message)
        self.status = status


class UnsupportedMediaError(AdapterError):
    pass


class StaleOutputError(AdapterError):
    pass


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload))


def _run_adapter(
    executable: str,
    *,
    request_path: Path,
    receipt_path: Path,
    output_path: Path,
    timeout_seconds: float,
    inspect: bool = False,
    status_query: bool = False,
) -> subprocess.CompletedProcess:
    argv = [executable]
    if status_query:
        argv.extend(["--status", "--request", str(request_path), "--receipt", str(receipt_path)])
    else:
        argv.extend([
            "--request", str(request_path),
            "--receipt", str(receipt_path),
            "--output", str(output_path),
        ])
        if inspect:
            argv.append("--inspect")
    return subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


def inspect_scene(*, executable: str, scene: str, timeout_seconds: float = 30.0) -> InspectionResult:
    request_path = Path(tempfile_path_for("inspect"))
    receipt_path = request_path.with_suffix(".receipt.json")
    _write_json(request_path, {"scene": scene, "intent": "inspect"})
    proc = _run_adapter(
        executable,
        request_path=request_path,
        receipt_path=receipt_path,
        output_path=receipt_path,  # unused for inspect
        timeout_seconds=timeout_seconds,
        inspect=True,
    )
    if proc.returncode != 0:
        raise AdapterError(f"inspect failed: {proc.stderr.strip()}")
    payload = json.loads(receipt_path.read_text()) if receipt_path.is_file() else {"status": "unknown"}
    return InspectionResult.from_dict(payload)


def tempfile_path_for(label: str) -> Path:
    import tempfile
    fd, name = tempfile.mkstemp(prefix=f"dcc_handoff_{label}_", suffix=".json")
    Path(name).write_bytes(b"")
    return Path(name)


def request_preview_export(
    *,
    executable: str,
    spec: PreviewSpec,
    output_dir: str | Path,
    artifact_id: str,
    request_payload: dict | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[dict, str]:
    """Invoke the companion adapter to export a preview.

    Returns the (validated) receipt and the independently-recomputed sha256.
    Raises a classified AdapterError subclass on failure.
    """
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    request_path = output_dir_path / f"{artifact_id}.request.json"
    receipt_path = output_dir_path / f"{artifact_id}.receipt.json"
    output_path = output_dir_path / f"{artifact_id}.mp4"

    payload: dict[str, Any] = {
        "scene": spec.scene,
        "camera_name": spec.camera_name,
        "frame_range": {"start": spec.frame_start, "end": spec.frame_end},
        "artifact_id": artifact_id,
        "output_label": spec.output_label,
        "output_bytes": 4096,
    }
    if request_payload:
        payload.update(request_payload)
    _write_json(request_path, payload)

    try:
        proc = _run_adapter(
            executable,
            request_path=request_path,
            receipt_path=receipt_path,
            output_path=output_path,
            timeout_seconds=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        # Per the spec: on timeout, query the adapter status if supported;
        # never auto-retry the export.
        return _query_status(executable, output_dir_path, artifact_id, request_path, receipt_path, timeout_seconds)

    if proc.returncode != 0:
        stderr = proc.stderr.strip()
        # Some adapters encode errors inside the receipt JSON rather than stderr.
        try:
            receipt_probe = json.loads(receipt_path.read_text()) if receipt_path.is_file() else {}
        except json.JSONDecodeError:
            receipt_probe = {}
        if "unsupported" in stderr.lower() or "unsupported" in json.dumps(receipt_probe).lower():
            raise UnsupportedMediaError(stderr or "unsupported media")
        raise AdapterError(stderr or f"adapter exit {proc.returncode}")

    if not receipt_path.is_file():
        raise AdapterError("adapter produced no receipt")
    try:
        receipt = json.loads(receipt_path.read_text())
    except json.JSONDecodeError as exc:
        raise AdapterError(f"receipt is not valid JSON: {exc}")

    if receipt.get("producer_plugin") not in SUPPORTED_PRODUCERS:
        raise AdapterError(f"unknown producer_plugin in receipt: {receipt.get('producer_plugin')!r}")
    if receipt.get("restoration", {}).get("status") != "confirmed":
        raise AdapterError(f"adapter did not confirm restoration: {receipt.get('restoration')}")

    # The handoff MUST independently re-hash the artifact; never trust the
    # producer's declared hash without on-disk verification.
    if not output_path.is_file():
        raise AdapterError(f"expected output file missing: {output_path}")
    actual_hash = _sha256_of(output_path)
    declared_hash = receipt.get("sha256")
    if declared_hash is not None and declared_hash != actual_hash:
        raise StaleOutputError(
            f"receipt.sha256 {declared_hash} != on-disk {actual_hash}"
        )
    receipt["path"] = str(output_path)
    receipt["sha256"] = actual_hash
    receipt["bytes"] = output_path.stat().st_size

    errors = validate_artifact(receipt, output_path)
    if errors:
        if any("hash" in e or "size" in e or "sha256" in e for e in errors):
            raise StaleOutputError("; ".join(errors))
        if any("codec" in e or "duration" in e or "dimensions" in e for e in errors):
            raise UnsupportedMediaError("; ".join(errors))
        raise AdapterError("; ".join(errors))

    # Final stale-output gate: the adapter is not allowed to mutate the file
    # after we already accepted the receipt. Re-read the file once more.
    final_hash = _sha256_of(output_path)
    if final_hash != actual_hash:
        raise StaleOutputError(f"artifact hash changed after validation: {actual_hash} -> {final_hash}")

    return receipt, actual_hash


def _query_status(
    executable: str,
    output_dir_path: Path,
    artifact_id: str,
    request_path: Path,
    receipt_path: Path,
    timeout_seconds: float,
) -> tuple[dict, str]:
    """Ask the adapter for the status of a previously-timed-out export."""
    status_request = output_dir_path / f"{artifact_id}.status.request.json"
    status_request.write_text(json.dumps({"artifact_id": artifact_id}))
    try:
        proc = _run_adapter(
            executable,
            request_path=status_request,
            receipt_path=receipt_path,
            output_path=receipt_path,  # unused
            timeout_seconds=timeout_seconds,
            status_query=True,
        )
    except subprocess.TimeoutExpired:
        raise AdapterError("adapter status query timed out", status="unknown")
    if proc.returncode != 0:
        raise AdapterError(proc.stderr.strip() or "adapter status query failed", status="unknown")
    try:
        status = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        status = {"status": "unknown"}
    raise AdapterError(f"adapter reported {status.get('status', 'unknown')!r} after timeout", status=status.get("status", "unknown"))


__all__ = [
    "PreviewSpec",
    "InspectionResult",
    "AdapterError",
    "UnsupportedMediaError",
    "StaleOutputError",
    "inspect_scene",
    "request_preview_export",
]