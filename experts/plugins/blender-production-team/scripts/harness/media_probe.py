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


def probe_video(path: Path, ffprobe: Path, *, runner=subprocess.run, timeout: float = 30.0,
                 check_audio: bool = False) -> dict:
    """Probe a video file for codec, resolution, framerate and optionally audio.

    When *check_audio* is True, the result includes an ``audio`` key with
    ``codec`` and ``sample_rate`` (or ``None`` if no audio stream is present).
    """
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
    # Audio stream probe (optional)
    if check_audio:
        audio_cmd = [
            str(ffprobe), "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=codec_name,sample_rate",
            "-of", "json", str(path),
        ]
        audio_proc = runner(audio_cmd, capture_output=True, text=True,
                            timeout=timeout, check=False, shell=False)
        try:
            audio_payload = json.loads(audio_proc.stdout)
            audio_streams = audio_payload.get("streams", [])
            if audio_streams:
                result["audio"] = {
                    "codec": str(audio_streams[0].get("codec_name", "")).lower(),
                    "sample_rate": int(audio_streams[0].get("sample_rate", 0)),
                }
            else:
                result["audio"] = None
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            result["audio"] = None
    return result

