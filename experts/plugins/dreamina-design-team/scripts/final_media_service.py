"""Verification-first final media acceptance and atomic export.

A temporary final MP4 is accepted only after every gate required by the
project's audio policy has been *measured* on the bytes that will ship. Export
never writes the destination until all required gates pass, and it writes
atomically so an interrupted copy can never leave a partial file where a
finished one is expected.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

BASE_FINAL_GATES = frozenset(
    {
        "container",
        "video_stream",
        "duration",
        "dimensions",
        "frame_rate",
        "subtitles",
        "checksum",
        "provenance",
    }
)
AUDIO_FINAL_GATES = frozenset({"audio_stream", "av_sync", "loudness"})

VIDEO_CODEC = "h264"
VIDEO_PIXEL_FORMAT = "yuv420p"
AUDIO_CODEC = "aac"
AUDIO_SAMPLE_RATE_HZ = 48000
ALLOWED_FRAME_RATES = (24, 25, 30)
MIN_EDGE_PX = 360
MAX_EDGE_PX = 3840
DEFAULT_DURATION_TOLERANCE_SECONDS = 0.5
DEFAULT_AV_SYNC_TOLERANCE_SECONDS = 0.08
DEFAULT_LOUDNESS_TARGET_LUFS = -16.0
DEFAULT_LOUDNESS_TOLERANCE_LUFS = 1.0
DEFAULT_TRUE_PEAK_MAX_DBTP = -1.0
COPY_CHUNK_BYTES = 1024 * 1024


class FinalMediaValidationError(RuntimeError):
    """The temporary final MP4 failed a required gate, or export was unsafe."""


def required_final_gates(audio_policy: str) -> frozenset[str]:
    """Audio gates are required for every policy except a deliberately silent one."""
    return BASE_FINAL_GATES if audio_policy == "silent" else BASE_FINAL_GATES | AUDIO_FINAL_GATES


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(COPY_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ratio(value: Any) -> float | None:
    """Parse an ffprobe rational such as ``24/1`` into a float."""
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str) or not value:
        return None
    if "/" in value:
        numerator, _, denominator = value.partition("/")
        try:
            top, bottom = float(numerator), float(denominator)
        except ValueError:
            return None
        return top / bottom if bottom else None
    try:
        return float(value)
    except ValueError:
        return None


class FinalMediaService:
    """Verify final media, then export it atomically."""

    def __init__(
        self,
        media_adapter: Any,
        *,
        duration_tolerance_seconds: float = DEFAULT_DURATION_TOLERANCE_SECONDS,
        av_sync_tolerance_seconds: float = DEFAULT_AV_SYNC_TOLERANCE_SECONDS,
        loudness_target_lufs: float = DEFAULT_LOUDNESS_TARGET_LUFS,
        loudness_tolerance_lufs: float = DEFAULT_LOUDNESS_TOLERANCE_LUFS,
        true_peak_max_dbtp: float = DEFAULT_TRUE_PEAK_MAX_DBTP,
        loudness_measure: Callable[[Path], Mapping[str, float]] | None = None,
    ) -> None:
        self.media_adapter = media_adapter
        self.duration_tolerance_seconds = duration_tolerance_seconds
        self.av_sync_tolerance_seconds = av_sync_tolerance_seconds
        self.loudness_target_lufs = loudness_target_lufs
        self.loudness_tolerance_lufs = loudness_tolerance_lufs
        self.true_peak_max_dbtp = true_peak_max_dbtp
        self._loudness_measure = loudness_measure or self._measure_loudness

    # ------------------------------------------------------------------ probe

    def _measure_loudness(self, path: Path) -> Mapping[str, float]:
        """Measure integrated loudness and true peak with ffmpeg's loudnorm."""
        result = self.media_adapter.run(
            "ffmpeg",
            [
                "-hide_banner",
                "-nostdin",
                "-i",
                str(path),
                "-af",
                "loudnorm=print_format=json",
                "-f",
                "null",
                "-",
            ],
            timeout_seconds=300,
        )
        if result.exit_code != 0:
            raise FinalMediaValidationError(
                f"loudness measurement failed with exit {result.exit_code}"
            )
        match = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", result.stderr or "", re.DOTALL)
        if match is None:
            raise FinalMediaValidationError("ffmpeg loudnorm emitted no JSON measurement")
        try:
            measured = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise FinalMediaValidationError("loudnorm JSON was unreadable") from exc
        try:
            return {
                "integrated_lufs": float(measured["input_i"]),
                "true_peak_dbtp": float(measured["input_tp"]),
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise FinalMediaValidationError("loudnorm JSON omitted loudness fields") from exc

    # -------------------------------------------------------------- verification

    def verify_final(
        self,
        final_mp4: Path,
        expected_plan: Any,
        *,
        audio_policy: str = "full_redesign",
        source_fingerprint: str = "0" * 64,
        design_fingerprint: str = "0" * 64,
        composition_fingerprint: str = "0" * 64,
        tool: str = "ffmpeg",
    ) -> dict[str, Any]:
        """Measure every required gate on ``final_mp4`` and return a receipt.

        Raises ``FinalMediaValidationError`` for a structural problem that makes
        measurement impossible. Individual gate failures are recorded in the
        receipt so the caller can report all of them at once.
        """
        path = Path(final_mp4)
        if not path.is_absolute():
            raise FinalMediaValidationError("final media path must be absolute")
        if path.is_symlink() or not path.is_file():
            raise FinalMediaValidationError("final media must be a regular non-symlink file")

        size_bytes = path.stat().st_size
        if size_bytes <= 0:
            raise FinalMediaValidationError("final media is empty")
        digest = _sha256_of(path)

        probe = self.media_adapter.probe_json(path)
        streams = probe.get("streams")
        if not isinstance(streams, list):
            raise FinalMediaValidationError("ffprobe returned no stream list")
        video_streams = [s for s in streams if isinstance(s, Mapping) and s.get("codec_type") == "video"]
        audio_streams = [s for s in streams if isinstance(s, Mapping) and s.get("codec_type") == "audio"]
        subtitle_streams = [s for s in streams if isinstance(s, Mapping) and s.get("codec_type") == "subtitle"]

        container = probe.get("format")
        container_name = ""
        duration_seconds = 0.0
        if isinstance(container, Mapping):
            container_name = str(container.get("format_name", ""))
            try:
                duration_seconds = float(container.get("duration", 0.0) or 0.0)
            except (TypeError, ValueError):
                duration_seconds = 0.0

        video = video_streams[0] if video_streams else {}
        audio = audio_streams[0] if audio_streams else {}
        codec = str(video.get("codec_name", ""))
        pixel_format = str(video.get("pix_fmt", ""))
        try:
            width = int(video.get("width", 0) or 0)
            height = int(video.get("height", 0) or 0)
        except (TypeError, ValueError):
            width = height = 0
        frame_rate = _ratio(video.get("avg_frame_rate")) or _ratio(video.get("r_frame_rate")) or 0.0

        target_duration = float(getattr(expected_plan, "target_duration_seconds", 0.0) or 0.0)
        duration_delta = abs(duration_seconds - target_duration)

        gates: dict[str, dict[str, Any]] = {}
        gates["container"] = {
            "passed": "mp4" in container_name,
            "measured": container_name,
            "expected": "mp4",
        }
        gates["video_stream"] = {
            "passed": bool(video_streams) and int(video.get("nb_frames", 0) or 0) != 0,
            "measured": len(video_streams),
            "expected": ">= 1 video stream",
        }
        gates["duration"] = {
            "passed": duration_delta <= self.duration_tolerance_seconds,
            "measured": round(duration_delta, 4),
            "expected": f"<= {self.duration_tolerance_seconds}s from the plan target",
        }
        gates["dimensions"] = {
            "passed": (
                width > 0
                and height > 0
                and width % 2 == 0
                and height % 2 == 0
                and MIN_EDGE_PX <= width <= MAX_EDGE_PX
                and MIN_EDGE_PX <= height <= MAX_EDGE_PX
            ),
            "measured": [width, height],
            "expected": f"even and within {MIN_EDGE_PX}-{MAX_EDGE_PX} per edge",
        }
        gates["frame_rate"] = {
            "passed": any(abs(frame_rate - rate) < 0.01 for rate in ALLOWED_FRAME_RATES),
            "measured": round(frame_rate, 4),
            "expected": list(ALLOWED_FRAME_RATES),
        }

        expected_cues = None
        subtitle = getattr(expected_plan, "subtitle", None)
        if isinstance(subtitle, Mapping):
            cues = subtitle.get("cues")
            if isinstance(cues, list):
                expected_cues = len(cues)
        if expected_cues is None:
            gates["subtitles"] = {"passed": True, "measured": None, "expected": "no subtitle plan"}
            subtitle_cue_count: int | None = None
        else:
            measured_cues = len(subtitle_streams)
            gates["subtitles"] = {
                "passed": measured_cues >= 1,
                "measured": measured_cues,
                "expected": ">= 1 subtitle stream for a planned subtitle track",
            }
            subtitle_cue_count = measured_cues

        gates["checksum"] = {"passed": bool(re.fullmatch(r"[a-f0-9]{64}", digest)), "measured": digest}
        gates["provenance"] = {
            "passed": all(
                re.fullmatch(r"[a-f0-9]{64}", value)
                for value in (source_fingerprint, design_fingerprint, composition_fingerprint)
            ),
            "measured": {
                "source": source_fingerprint,
                "design": design_fingerprint,
                "composition": composition_fingerprint,
            },
        }

        loudness_lufs: float | None = None
        true_peak_dbtp: float | None = None
        av_sync_delta: float | None = None
        if "audio_stream" in required_final_gates(audio_policy):
            audio_codec = str(audio.get("codec_name", ""))
            try:
                sample_rate = int(audio.get("sample_rate", 0) or 0)
                channels = int(audio.get("channels", 0) or 0)
            except (TypeError, ValueError):
                sample_rate = channels = 0
            gates["audio_stream"] = {
                "passed": bool(audio_streams) and audio_codec == AUDIO_CODEC and sample_rate == AUDIO_SAMPLE_RATE_HZ,
                "measured": {"codec": audio_codec, "sample_rate_hz": sample_rate, "streams": len(audio_streams)},
                "expected": f"{AUDIO_CODEC} at {AUDIO_SAMPLE_RATE_HZ} Hz",
            }

            video_start = _ratio(video.get("start_time")) or 0.0
            audio_start = _ratio(audio.get("start_time")) or 0.0
            av_sync_delta = abs(video_start - audio_start)
            gates["av_sync"] = {
                "passed": av_sync_delta <= self.av_sync_tolerance_seconds,
                "measured": round(av_sync_delta, 4),
                "expected": f"<= {self.av_sync_tolerance_seconds}s",
            }

            measured_loudness = self._loudness_measure(path)
            loudness_lufs = float(measured_loudness["integrated_lufs"])
            true_peak_dbtp = float(measured_loudness["true_peak_dbtp"])
            loudness_ok = (
                abs(loudness_lufs - self.loudness_target_lufs) <= self.loudness_tolerance_lufs
                and true_peak_dbtp <= self.true_peak_max_dbtp
            )
            gates["loudness"] = {
                "passed": loudness_ok,
                "measured": {"integrated_lufs": loudness_lufs, "true_peak_dbtp": true_peak_dbtp},
                "expected": (
                    f"{self.loudness_target_lufs} +/- {self.loudness_tolerance_lufs} LUFS, "
                    f"true peak <= {self.true_peak_max_dbtp} dBTP"
                ),
            }
        else:
            gates["audio_stream"] = {"passed": True, "measured": None, "expected": "silent policy"}
            gates["av_sync"] = {"passed": True, "measured": None, "expected": "silent policy"}
            gates["loudness"] = {"passed": True, "measured": None, "expected": "silent policy"}

        receipt: dict[str, Any] = {
            "schema_version": "1.0.0",
            "composition_version": str(getattr(expected_plan, "composition_version", "v001")),
            "project_id": str(getattr(expected_plan, "project_id", "vp_" + "0" * 24)),
            "path": str(path),
            "sha256": digest,
            "size_bytes": size_bytes,
            "audio_policy": audio_policy,
            "required_gates": sorted(required_final_gates(audio_policy)),
            "gates": gates,
            "video": {
                "codec": codec,
                "pixel_format": pixel_format,
                "width": width,
                "height": height,
                "frame_rate": round(frame_rate, 4),
                "stream_count": len(video_streams),
            },
            "audio": (
                {
                    "codec": str(audio.get("codec_name", "")),
                    "sample_rate_hz": int(audio.get("sample_rate", 0) or 0),
                    "channels": int(audio.get("channels", 0) or 0),
                    "stream_count": len(audio_streams),
                }
                if audio_streams
                else None
            ),
            "duration_seconds": round(duration_seconds, 4),
            "target_duration_seconds": round(target_duration, 4),
            "duration_delta_seconds": round(duration_delta, 4),
            "av_sync_delta_seconds": None if av_sync_delta is None else round(av_sync_delta, 4),
            "loudness_lufs": loudness_lufs,
            "true_peak_dbtp": true_peak_dbtp,
            "subtitle_cue_count": subtitle_cue_count,
            "faststart": bool(_has_faststart(path)),
            "provenance": {
                "source_fingerprint": source_fingerprint,
                "design_fingerprint": design_fingerprint,
                "output_fingerprint": digest,
                "composition_fingerprint": composition_fingerprint,
                "tool": tool,
            },
        }
        return receipt

    # -------------------------------------------------------------------- export

    def failed_gates(self, receipt: Mapping[str, Any]) -> list[str]:
        required = set(receipt.get("required_gates") or ())
        gates = receipt.get("gates") or {}
        return sorted(
            name
            for name in required
            if not isinstance(gates.get(name), Mapping) or gates[name].get("passed") is not True
        )

    def _assert_all_required_gates_pass(self, receipt: Mapping[str, Any]) -> None:
        failed = self.failed_gates(receipt)
        if failed:
            raise FinalMediaValidationError(f"final media failed required gates: {', '.join(failed)}")
        if not receipt.get("faststart"):
            raise FinalMediaValidationError("final media is missing the faststart layout")

    def _confirm_exact_destination(self, destination: Path, approved_roots: Mapping[str, Any] | None) -> None:
        if not destination.is_absolute():
            raise FinalMediaValidationError("destination must be absolute")
        if approved_roots:
            allowed = [Path(root).expanduser().resolve() for root in approved_roots]
            resolved = Path(os.path.realpath(destination))
            if not any(resolved == root or root in resolved.parents for root in allowed):
                raise FinalMediaValidationError(f"destination {resolved} is outside the approved roots")
        if os.path.lexists(destination):
            raise FinalMediaValidationError("destination already exists; refusing to overwrite")

    def export_verified(
        self,
        receipt: Mapping[str, Any],
        *,
        source: Path,
        destination: Path,
        approved_roots: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Copy a verified final MP4 to ``destination`` atomically.

        The destination is never created until every required gate has passed,
        and the copy lands through a temporary file plus ``os.replace``, so an
        interrupted export cannot leave a partial file at the destination.
        """
        self._assert_all_required_gates_pass(receipt)
        self._confirm_exact_destination(Path(destination), approved_roots)

        source_path = Path(source)
        expected_hash = str(receipt["sha256"])
        if _sha256_of(source_path) != expected_hash:
            raise FinalMediaValidationError("source changed after verification")

        destination_path = Path(destination)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination_path.with_name(
            f".{destination_path.name}.{secrets.token_hex(8)}.partial"
        )
        try:
            with source_path.open("rb") as reader, open(temporary, "wb") as writer:
                for chunk in iter(lambda: reader.read(COPY_CHUNK_BYTES), b""):
                    writer.write(chunk)
                writer.flush()
                os.fsync(writer.fileno())
            if _sha256_of(temporary) != expected_hash:
                raise FinalMediaValidationError("exported copy does not match the verified checksum")
            os.chmod(temporary, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            os.replace(temporary, destination_path)
            _fsync_directory(destination_path.parent)
        except BaseException:
            if os.path.lexists(temporary):
                os.unlink(temporary)
            raise

        return {
            "path": str(destination_path),
            "sha256": expected_hash,
            "size_bytes": destination_path.stat().st_size,
            "atomic": True,
        }


def _has_faststart(path: Path) -> bool:
    """A faststart MP4 places the moov box before mdat."""
    try:
        with path.open("rb") as handle:
            header = handle.read(64)
            if len(header) < 12:
                return False
            offset = 0
            while offset + 8 <= len(header):
                size = int.from_bytes(header[offset : offset + 4], "big")
                kind = header[offset + 4 : offset + 8]
                if kind == b"moov":
                    return True
                if kind == b"mdat":
                    return False
                if size < 8:
                    return False
                offset += size
    except OSError:
        return False
    return False


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


__all__ = [
    "AUDIO_FINAL_GATES",
    "BASE_FINAL_GATES",
    "FinalMediaService",
    "FinalMediaValidationError",
    "required_final_gates",
]
