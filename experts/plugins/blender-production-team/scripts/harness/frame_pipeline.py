"""Closed contracts and deterministic helpers for durable animation frame jobs."""

from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

from .errors import HarnessError


RENDER_FIELDS = {
    "frameStart", "frameEnd", "frameStep", "width", "height",
    "imageFormat", "colorMode", "colorDepth", "includeAudio",
}
COMPOSE_FIELDS = {"sourceJobId", "codec", "crf", "preset", "pixelFormat", "includeAudio"}
PRESETS = {"ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower"}


def expected_frames(frame_start: int, frame_end: int, frame_step: int = 1) -> list[int]:
    if type(frame_start) is not int or type(frame_end) is not int or type(frame_step) is not int:
        raise HarnessError("INVALID_ARGUMENT", "frameStart, frameEnd and frameStep must be integers")
    if frame_start > frame_end or not 1 <= frame_step <= 1000:
        raise HarnessError("INVALID_ARGUMENT", "frame range or frameStep is invalid")
    frames = list(range(frame_start, frame_end + 1, frame_step))
    if len(frames) > 100000:
        raise HarnessError("INVALID_ARGUMENT", "frame sequence exceeds 100000 frames")
    return frames


def validate_render_parameters(parameters: dict) -> dict:
    if not isinstance(parameters, dict) or set(parameters) - RENDER_FIELDS:
        raise HarnessError("INVALID_ARGUMENT", "render frame parameters contain unsupported fields")
    start = parameters.get("frameStart")
    end = parameters.get("frameEnd")
    step = parameters.get("frameStep", 1)
    frames = expected_frames(start, end, step)
    width, height = parameters.get("width", 1920), parameters.get("height", 1080)
    if any(type(value) is not int or not 2 <= value <= 16384 or value % 2 for value in (width, height)):
        raise HarnessError("INVALID_ARGUMENT", "width and height must be even integers from 2 to 16384")
    image_format = str(parameters.get("imageFormat", "PNG")).upper()
    if image_format not in {"PNG", "OPEN_EXR_MULTILAYER"}:
        raise HarnessError("INVALID_ARGUMENT", "imageFormat must be PNG or OPEN_EXR_MULTILAYER")
    color_mode = str(parameters.get("colorMode", "RGBA")).upper()
    if color_mode not in {"RGB", "RGBA"}:
        raise HarnessError("INVALID_ARGUMENT", "colorMode must be RGB or RGBA")
    default_depth = "16"
    color_depth = str(parameters.get("colorDepth", default_depth))
    allowed_depths = {"8", "16"} if image_format == "PNG" else {"16", "32"}
    if color_depth not in allowed_depths:
        raise HarnessError("INVALID_ARGUMENT", f"unsupported colorDepth for {image_format}")
    include_audio = parameters.get("includeAudio", True)
    if type(include_audio) is not bool:
        raise HarnessError("INVALID_ARGUMENT", "includeAudio must be boolean")
    return {
        "frameStart": start,
        "frameEnd": end,
        "frameStep": step,
        "frames": frames,
        "width": width,
        "height": height,
        "imageFormat": image_format,
        "extension": "png" if image_format == "PNG" else "exr",
        "colorMode": color_mode,
        "colorDepth": color_depth,
        "includeAudio": include_audio,
    }


def validate_compose_parameters(parameters: dict) -> dict:
    if not isinstance(parameters, dict) or set(parameters) - COMPOSE_FIELDS:
        raise HarnessError("INVALID_ARGUMENT", "compose parameters contain unsupported fields")
    source = parameters.get("sourceJobId")
    if not isinstance(source, str) or re.fullmatch(r"job_[A-Za-z0-9_-]{1,80}", source) is None:
        raise HarnessError("INVALID_ARGUMENT", "sourceJobId must start with job_")
    codec = str(parameters.get("codec", "H264")).upper()
    if codec != "H264":
        raise HarnessError("INVALID_ARGUMENT", "codec must be H264")
    crf = parameters.get("crf", 20)
    if type(crf) is not int or not 0 <= crf <= 51:
        raise HarnessError("INVALID_ARGUMENT", "crf must be an integer from 0 to 51")
    preset = str(parameters.get("preset", "medium")).lower()
    if preset not in PRESETS:
        raise HarnessError("INVALID_ARGUMENT", "unsupported H264 preset")
    pixel_format = str(parameters.get("pixelFormat", "yuv420p")).lower()
    if pixel_format != "yuv420p":
        raise HarnessError("INVALID_ARGUMENT", "pixelFormat must be yuv420p")
    include_audio = parameters.get("includeAudio", True)
    if type(include_audio) is not bool:
        raise HarnessError("INVALID_ARGUMENT", "includeAudio must be boolean")
    return {"sourceJobId": source, "codec": codec, "crf": crf, "preset": preset,
            "pixelFormat": pixel_format, "includeAudio": include_audio}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _frame_header_valid(path: Path, manifest: dict) -> bool:
    format_name = manifest.get("format")
    with path.open("rb") as stream:
        header = stream.read(26)
    if format_name == "PNG" and all(key in manifest for key in ("width", "height", "colorMode")):
        if len(header) < 26 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            return False
        width, height = struct.unpack(">II", header[16:24])
        expected_color = 6 if manifest["colorMode"] == "RGBA" else 2
        return width == manifest["width"] and height == manifest["height"] and header[25] == expected_color
    if format_name == "OPEN_EXR_MULTILAYER":
        return header[:4] == b"\x76\x2f\x31\x01"
    return True


def inspect_frame_sequence(manifest: dict, approved_root: Path) -> dict:
    if not isinstance(manifest, dict):
        raise HarnessError("ARTIFACT_INVALID", "frame sequence manifest must be an object")
    expected = expected_frames(manifest.get("frameStart"), manifest.get("frameEnd"), manifest.get("frameStep", 1))
    entries = manifest.get("frames", [])
    if not isinstance(entries, list):
        raise HarnessError("ARTIFACT_INVALID", "frame sequence entries must be an array")
    by_frame = {entry.get("frame"): entry for entry in entries if isinstance(entry, dict)}
    root = Path(approved_root).resolve()
    complete, missing, corrupt = [], [], []
    for frame in expected:
        entry = by_frame.get(frame)
        if entry is None:
            missing.append(frame)
            continue
        try:
            path = Path(entry["path"])
            if path.is_symlink():
                raise ValueError("symlink")
            resolved = path.resolve()
            resolved.relative_to(root)
        except (KeyError, TypeError, ValueError):
            corrupt.append(frame)
            continue
        if not resolved.is_file():
            missing.append(frame)
        elif (resolved.stat().st_size != entry.get("bytes") or sha256_file(resolved) != entry.get("sha256")
              or not _frame_header_valid(resolved, manifest)):
            corrupt.append(frame)
        else:
            complete.append(frame)
    return {"expected": expected, "complete": complete, "missing": missing, "corrupt": corrupt,
            "ready": len(complete) == len(expected)}


def frames_requiring_render(manifest: dict, approved_root: Path) -> list[int]:
    inspection = inspect_frame_sequence(manifest, approved_root)
    return sorted(inspection["missing"] + inspection["corrupt"])


def write_concat_manifest(manifest: dict, approved_root: Path, target: Path) -> Path:
    inspection = inspect_frame_sequence(manifest, approved_root)
    if not inspection["ready"]:
        raise HarnessError("FRAME_SEQUENCE_INCOMPLETE", "cannot compose an incomplete frame sequence")
    fps = manifest.get("fps")
    if not isinstance(fps, (int, float)) or isinstance(fps, bool) or fps <= 0:
        raise HarnessError("ARTIFACT_INVALID", "frame sequence fps must be positive")
    step = manifest.get("frameStep", 1)
    duration = step / float(fps)
    entries = {entry["frame"]: entry for entry in manifest["frames"]}
    paths = [Path(entries[frame]["path"]).resolve() for frame in inspection["expected"]]
    if any("\n" in str(path) or "\r" in str(path) for path in paths):
        raise HarnessError("ARTIFACT_INVALID", "frame paths must not contain newlines")

    def quote(path):
        return str(path).replace("'", "'\\''")

    lines = ["ffconcat version 1.0"]
    for path in paths:
        lines.extend([f"file '{quote(path)}'", f"duration {duration:.9f}"])
    # The concat demuxer requires the final image twice to honor its duration.
    lines.append(f"file '{quote(paths[-1])}'")
    target = Path(target)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def build_compose_command(ffmpeg: Path, concat_file: Path, target: Path, parameters: dict,
                          *, audio_path: Path | None = None, fps: int | float | None = None,
                          frame_count: int | None = None) -> list[str]:
    normalized = validate_compose_parameters(parameters)
    command = [str(ffmpeg), "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file)]
    if audio_path is not None and normalized["includeAudio"]:
        command.extend(["-i", str(audio_path)])
    if not isinstance(fps, (int, float)) or isinstance(fps, bool) or fps <= 0:
        raise HarnessError("INVALID_ARGUMENT", "compose fps must be positive")
    if type(frame_count) is not int or frame_count < 1:
        raise HarnessError("INVALID_ARGUMENT", "compose frame_count must be positive")
    command.extend(["-r", f"{float(fps):g}", "-c:v", "libx264", "-crf", str(normalized["crf"]), "-preset", normalized["preset"],
                    "-pix_fmt", normalized["pixelFormat"], "-tag:v", "avc1", "-frames:v", str(frame_count)])
    if audio_path is not None and normalized["includeAudio"]:
        command.extend(["-c:a", "aac", "-shortest"])
    command.extend(["-movflags", "+faststart", str(target)])
    return command
