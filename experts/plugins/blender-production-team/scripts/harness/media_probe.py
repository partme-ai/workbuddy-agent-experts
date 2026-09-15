"""Independent ffprobe validation for exported MP4 files."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .errors import HarnessError


def _rate(value: str) -> float:
    numerator, separator, denominator = str(value).partition("/")
    if separator:
        divisor = float(denominator)
        return float(numerator) / divisor if divisor else 0.0
    return float(numerator)


def probe_video(path: Path, ffprobe: Path, *, runner=subprocess.run, timeout: float = 30.0) -> dict:
    command = [
        str(ffprobe), "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height,avg_frame_rate:format=duration",
        "-of", "json", str(path),
    ]
    process = runner(command, capture_output=True, text=True, timeout=timeout, check=False, shell=False)
    if process.returncode != 0:
        raise HarnessError("MEDIA_INVALID", process.stderr.strip() or "ffprobe failed")
    try:
        payload = json.loads(process.stdout)
        stream = payload["streams"][0]
        result = {
            "codec": str(stream["codec_name"]).lower(),
            "width": int(stream["width"]),
            "height": int(stream["height"]),
            "fps": _rate(stream["avg_frame_rate"]),
            "duration_seconds": float(payload["format"]["duration"]),
        }
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HarnessError("MEDIA_INVALID", f"ffprobe response is incomplete: {exc}") from exc
    if result["codec"] not in {"h264", "avc1"}:
        raise HarnessError("MEDIA_INVALID", f"expected H.264, got {result['codec']}")
    if result["width"] <= 0 or result["height"] <= 0 or result["width"] % 2 or result["height"] % 2:
        raise HarnessError("MEDIA_INVALID", "video dimensions must be positive and even")
    if result["fps"] <= 0 or result["duration_seconds"] <= 0:
        raise HarnessError("MEDIA_INVALID", "video fps and duration must be positive")
    return result

