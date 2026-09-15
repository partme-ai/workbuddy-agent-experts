"""Probe and hash a local preview artifact."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


class MediaProbeError(RuntimeError):
    pass


def _fps(value: str) -> float:
    numerator, separator, denominator = value.partition("/")
    if not separator:
        return float(value)
    divisor = float(denominator)
    if divisor == 0:
        raise MediaProbeError("ffprobe returned a zero fps denominator")
    return float(numerator) / divisor


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_media(path: Path, *, ffprobe: str | None = None) -> dict[str, Any]:
    """Return verified H.264 MP4 metadata and the final file hash."""
    target = path.resolve()
    if not target.is_file() or target.is_symlink():
        raise MediaProbeError(f"media is not a regular file: {path}")
    executable = ffprobe or shutil.which("ffprobe")
    if not executable:
        raise MediaProbeError("ffprobe is required and was not found")

    before = target.stat()
    process = subprocess.run(
        [
            executable, "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,width,height,avg_frame_rate:format=format_name,duration",
            "-of", "json", str(target),
        ],
        capture_output=True, text=True, timeout=30, check=False,
    )
    if process.returncode != 0:
        raise MediaProbeError(process.stderr.strip() or "ffprobe failed")
    try:
        payload = json.loads(process.stdout)
        stream = payload["streams"][0]
        media_format = payload["format"]
        result = {
            "codec": str(stream["codec_name"]).lower(),
            "container": "mp4" if "mp4" in str(media_format["format_name"]).lower() else str(media_format["format_name"]),
            "dimensions": {"width": int(stream["width"]), "height": int(stream["height"])},
            "fps": round(_fps(str(stream["avg_frame_rate"])), 6),
            "duration_seconds": float(media_format["duration"]),
            "bytes": before.st_size,
            "sha256": _sha256(target),
        }
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise MediaProbeError(f"invalid ffprobe response: {exc}") from exc

    after = target.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
    ):
        raise MediaProbeError("media changed while it was being probed")
    if result["codec"] != "h264" or result["container"] != "mp4":
        raise MediaProbeError("preview must be H.264 in an MP4 container")
    return result
