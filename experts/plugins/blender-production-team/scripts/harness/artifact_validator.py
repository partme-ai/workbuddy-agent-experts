"""Artifact hashing and generalized receipt creation."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .errors import HarnessError


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_receipt(
    path: Path,
    *,
    format_name: str,
    session_id: str,
    scene_revision: int,
    snapshot_id: str,
    parameters: dict | None = None,
    restoration: str = "confirmed",
    warnings: list[str] | None = None,
    checks: list[str] | None = None,
) -> dict:
    path = Path(path).resolve()
    if not path.is_file() or path.stat().st_size <= 0:
        raise HarnessError("ARTIFACT_INVALID", f"artifact is missing or empty: {path}")
    return {
        "protocolVersion": "codex-blender/v1",
        "producer": {"name": "codex-blender", "version": "0.3.0"},
        "sessionId": session_id,
        "sceneRevision": int(scene_revision),
        "snapshotId": snapshot_id,
        "path": str(path),
        "sha256": sha256_file(path),
        "format": format_name,
        "bytes": path.stat().st_size,
        "parameters": dict(parameters or {}),
        "validation": {"status": "passed", "checks": list(checks or ["exists", "non_empty", "sha256"])},
        "restoration": {"status": restoration},
        "warnings": list(warnings or []),
    }
