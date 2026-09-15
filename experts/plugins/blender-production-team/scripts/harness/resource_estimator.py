"""Resource estimation for hypothetical job submissions.

The estimate is a pure function of (kind, parameters).  No I/O, no Blender
session, no side effects.  The result conforms to
``schemas/resource_estimate_receipt.schema.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

from .errors import HarnessError

_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "resource_estimate_receipt.schema.json"

# Baseline cost constants (empirical).  Numbers are deliberately conservative
# so a caller can plan with headroom.
_BYTES_PER_PIXEL_PNG = 4          # RGBA
_BYTES_PER_PIXEL_EXR = 12         # 32-bit half x 3 channels (conservative)
_SECONDS_PER_MEGAPIXEL = 0.08     # rendering cost on reference hardware
_BASE_MEMORY_BYTES = 512 * 1024 * 1024  # 512 MiB Blender baseline
_MEMORY_PER_MEGAPIXEL = 4 * 1024 * 1024  # 4 MiB per megapixel


def _estimate_export(parameters: dict) -> dict:
    """EXPORT is nearly free -- only the export write."""
    return {
        "estimatedDiskBytes": 10 * 1024 * 1024,   # 10 MiB rough upper bound
        "estimatedDurationSeconds": 2.0,
        "estimatedPeakMemoryBytes": _BASE_MEMORY_BYTES,
        "warnings": ["Export size depends on scene complexity; this is a rough upper bound"],
    }


def _estimate_render_still(parameters: dict) -> dict:
    width = int(parameters.get("width", 512))
    height = int(parameters.get("height", 512))
    pixels = width * height
    megapixels = pixels / 1_000_000
    return {
        "estimatedDiskBytes": pixels * _BYTES_PER_PIXEL_PNG + 4096,  # PNG + header
        "estimatedDurationSeconds": round(megapixels * _SECONDS_PER_MEGAPIXEL, 3),
        "estimatedPeakMemoryBytes": int(_BASE_MEMORY_BYTES + megapixels * _MEMORY_PER_MEGAPIXEL),
        "warnings": [],
    }


def _estimate_bake(parameters: dict) -> dict:
    return {
        "estimatedDiskBytes": 50 * 1024 * 1024,  # 50 MiB typical cache
        "estimatedDurationSeconds": 30.0,
        "estimatedPeakMemoryBytes": _BASE_MEMORY_BYTES * 2,
        "warnings": ["Bake cost depends heavily on simulation complexity"],
    }


def _estimate_animation_frames(parameters: dict) -> dict:
    start = int(parameters.get("frameStart", 1))
    end = int(parameters.get("frameEnd", 1))
    step = int(parameters.get("frameStep", 1))
    if start > end:
        raise HarnessError("INVALID_ARGUMENT", "frameStart must be <= frameEnd")
    if step < 1:
        raise HarnessError("INVALID_ARGUMENT", "frameStep must be >= 1")
    frame_count = max(1, (end - start) // step + 1)
    width = int(parameters.get("width", 1920))
    height = int(parameters.get("height", 1080))
    pixels = width * height
    megapixels = pixels / 1_000_000
    per_frame_disk = pixels * _BYTES_PER_PIXEL_PNG + 4096
    per_frame_seconds = megapixels * _SECONDS_PER_MEGAPIXEL
    return {
        "estimatedDiskBytes": frame_count * per_frame_disk,
        "estimatedDurationSeconds": round(frame_count * per_frame_seconds, 3),
        "estimatedPeakMemoryBytes": int(_BASE_MEMORY_BYTES + megapixels * _MEMORY_PER_MEGAPIXEL),
        "warnings": [] if frame_count <= 100 else
                    ["Large frame count; disk and time estimates are proportional"],
    }


def _estimate_compose(parameters: dict) -> dict:
    return {
        "estimatedDiskBytes": 100 * 1024 * 1024,  # 100 MiB for encoded video
        "estimatedDurationSeconds": 15.0,
        "estimatedPeakMemoryBytes": _BASE_MEMORY_BYTES,
        "warnings": ["Compose cost depends on resolution and codec settings"],
    }


_ESTIMATORS = {
    "EXPORT": _estimate_export,
    "RENDER_STILL": _estimate_render_still,
    "BAKE_POINT_CACHES": _estimate_bake,
    "RENDER_ANIMATION_FRAMES": _estimate_animation_frames,
    "COMPOSE_VIDEO": _estimate_compose,
}


def estimate(kind: str, parameters: dict) -> dict:
    """Return a resource-estimate receipt for a hypothetical job.

    The result conforms to ``resource_estimate_receipt.schema.json``.
    """
    kind = str(kind).upper()
    if kind not in _ESTIMATORS:
        raise HarnessError("INVALID_ARGUMENT", f"unsupported job kind: {kind}")
    if not isinstance(parameters, dict):
        raise HarnessError("INVALID_ARGUMENT", "parameters must be an object")
    receipt = _ESTIMATORS[kind](parameters)
    receipt["kind"] = kind
    receipt["parameters"] = dict(parameters)
    return receipt
