"""Visual milestone geometry and receipt assembly."""

from __future__ import annotations

from pathlib import Path

from .artifact_validator import sha256_file
from .errors import HarnessError


def view_positions(minimum, maximum) -> dict[str, tuple[float, float, float]]:
    center = tuple((float(minimum[i]) + float(maximum[i])) / 2 for i in range(3))
    extent = max(float(maximum[i]) - float(minimum[i]) for i in range(3))
    distance = max(1.0, extent * 2.5)
    return {
        "front": (center[0], center[1] - distance, center[2]),
        "side": (center[0] + distance, center[1], center[2]),
        "top": (center[0], center[1], center[2] + distance),
    }


def build_milestone_receipt(
    milestone: str,
    *,
    scene_revision: int,
    snapshot_id: str,
    view_paths: dict[str, Path],
    scene_summary: dict,
    warnings: list[str] | None = None,
) -> dict:
    required = ("camera", "front", "side", "top")
    missing = [name for name in required if name not in view_paths]
    if missing:
        raise HarnessError("MILESTONE_INCOMPLETE", f"missing milestone views: {missing}")
    views = []
    ordered = list(required) + [name for name in ("first", "middle", "last") if name in view_paths]
    for name in ordered:
        path = Path(view_paths[name]).resolve()
        if not path.is_file() or path.stat().st_size <= 0:
            raise HarnessError("MILESTONE_INCOMPLETE", f"view is missing or empty: {path}")
        views.append({"name": name, "path": str(path), "sha256": sha256_file(path)})
    return {
        "protocolVersion": "codex-blender/v1",
        "milestone": milestone,
        "sceneRevision": int(scene_revision),
        "snapshotId": snapshot_id,
        "views": views,
        "sceneSummary": dict(scene_summary),
        "warnings": list(warnings or []),
    }
