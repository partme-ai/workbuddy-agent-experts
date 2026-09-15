"""Argv-only, bounded execution for enrolled local media tools."""

from __future__ import annotations

import hashlib
import json
import os
import selectors
import signal
import struct
import subprocess
import sys
import time
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from scripts.trusted_media_tools import TrustedMediaToolStore


DEFAULT_MAX_OUTPUT_BYTES = 4 * 1024 * 1024
MAX_DECODED_FRAME_BYTES = 64 * 1024 * 1024


class MediaAdapterError(RuntimeError):
    """Base error for local media execution."""


class MediaTimeoutError(MediaAdapterError):
    """A media process exceeded its one permitted process lifetime."""


class MediaOutputError(MediaAdapterError):
    """A media process emitted invalid, failed, or oversized output."""


def _validate_complete_png(payload: bytes) -> tuple[int, int]:
    """Validate a complete, CRC-correct PNG and return its declared dimensions."""
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise MediaOutputError("ffmpeg frame output is not a valid PNG")
    offset = 8
    chunks: list[bytes] = []
    idat_parts: list[bytes] = []
    width = height = 0
    channels = 0
    while offset < len(payload):
        if len(payload) - offset < 12:
            raise MediaOutputError("ffmpeg frame PNG is truncated")
        length = struct.unpack(">I", payload[offset:offset + 4])[0]
        end = offset + 12 + length
        if end > len(payload):
            raise MediaOutputError("ffmpeg frame PNG chunk is truncated")
        chunk_type = payload[offset + 4:offset + 8]
        chunk_data = payload[offset + 8:offset + 8 + length]
        expected_crc = struct.unpack(">I", payload[offset + 8 + length:end])[0]
        if zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF != expected_crc:
            raise MediaOutputError("ffmpeg frame PNG checksum is invalid")
        chunks.append(chunk_type)
        if len(chunks) == 1:
            if chunk_type != b"IHDR" or length != 13:
                raise MediaOutputError("ffmpeg frame PNG lacks a valid IHDR")
            width, height = struct.unpack(">II", chunk_data[:8])
            if width <= 0 or height <= 0:
                raise MediaOutputError("ffmpeg frame PNG dimensions are invalid")
            bit_depth, color_type, compression, filtering, interlace = chunk_data[8:]
            channel_counts = {0: 1, 2: 3, 4: 2, 6: 4}
            if bit_depth != 8 or color_type not in channel_counts \
                    or compression != 0 or filtering != 0 or interlace != 0:
                raise MediaOutputError("ffmpeg frame PNG format is unsupported")
            channels = channel_counts[color_type]
        if chunk_type == b"IDAT":
            idat_parts.append(chunk_data)
        offset = end
        if chunk_type == b"IEND":
            if length != 0 or offset != len(payload):
                raise MediaOutputError("ffmpeg frame PNG has an invalid IEND")
            break
    if not chunks or chunks[-1] != b"IEND" or b"IDAT" not in chunks:
        raise MediaOutputError("ffmpeg frame PNG is incomplete")
    expected_bytes = height * (1 + width * channels)
    if expected_bytes <= 0 or expected_bytes > MAX_DECODED_FRAME_BYTES:
        raise MediaOutputError("ffmpeg frame PNG decoded size is invalid")
    try:
        decoder = zlib.decompressobj()
        pixels = decoder.decompress(b"".join(idat_parts), expected_bytes + 1)
        if len(pixels) > expected_bytes:
            raise MediaOutputError("ffmpeg frame PNG pixel payload exceeds declared dimensions")
        remaining = expected_bytes + 1 - len(pixels)
        pixels += decoder.flush(remaining)
    except MediaOutputError:
        raise
    except (ValueError, zlib.error) as exc:
        raise MediaOutputError("ffmpeg frame PNG pixels are not decodable") from exc
    if len(pixels) != expected_bytes or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise MediaOutputError("ffmpeg frame PNG pixel payload is invalid")
    stride = 1 + width * channels
    if any(pixels[offset] > 4 for offset in range(0, len(pixels), stride)):
        raise MediaOutputError("ffmpeg frame PNG row filter is invalid")
    return width, height


@dataclass(frozen=True)
class MediaResult:
    """Bounded stdout and stderr from one media process."""

    exit_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class _BinaryMediaResult:
    """Bounded binary stdout and bounded text stderr from one media process."""

    exit_code: int
    stdout: bytes
    stderr: str


class SubprocessMediaRunner:
    """Stream a subprocess with independent byte caps and process-group cleanup."""

    def run(
        self,
        argv: Sequence[str],
        *,
        shell: bool,
        env: Mapping[str, str],
        timeout_seconds: int,
        stdout_cap: int,
        stderr_cap: int,
        start_new_session: bool,
        terminate_process_group: bool,
        pass_fds: Sequence[int] = (),
    ) -> tuple[int, str, str]:
        exit_code, stdout, stderr = self._run_bytes(
            argv,
            shell=shell,
            env=env,
            timeout_seconds=timeout_seconds,
            stdout_cap=stdout_cap,
            stderr_cap=stderr_cap,
            start_new_session=start_new_session,
            terminate_process_group=terminate_process_group,
            pass_fds=pass_fds,
        )
        return (
            exit_code,
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
        )

    def run_binary(
        self,
        argv: Sequence[str],
        *,
        shell: bool,
        env: Mapping[str, str],
        timeout_seconds: int,
        stdout_cap: int,
        stderr_cap: int,
        start_new_session: bool,
        terminate_process_group: bool,
        pass_fds: Sequence[int] = (),
    ) -> tuple[int, bytes, str]:
        """Stream bounded binary stdout without applying text decoding."""
        exit_code, stdout, stderr = self._run_bytes(
            argv,
            shell=shell,
            env=env,
            timeout_seconds=timeout_seconds,
            stdout_cap=stdout_cap,
            stderr_cap=stderr_cap,
            start_new_session=start_new_session,
            terminate_process_group=terminate_process_group,
            pass_fds=pass_fds,
        )
        return exit_code, stdout, stderr.decode("utf-8", errors="replace")

    def _run_bytes(
        self,
        argv: Sequence[str],
        *,
        shell: bool,
        env: Mapping[str, str],
        timeout_seconds: int,
        stdout_cap: int,
        stderr_cap: int,
        start_new_session: bool,
        terminate_process_group: bool,
        pass_fds: Sequence[int] = (),
    ) -> tuple[int, bytes, bytes]:
        process = subprocess.Popen(  # noqa: S603
            list(argv),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=shell,
            env=dict(env),
            start_new_session=start_new_session,
            pass_fds=tuple(pass_fds),
        )
        selector = None
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        deadline = time.monotonic() + timeout_seconds
        try:
            assert process.stdout is not None and process.stderr is not None
            selector = selectors.DefaultSelector()
            selector.register(process.stdout, selectors.EVENT_READ, ("stdout", stdout_cap))
            selector.register(process.stderr, selectors.EVENT_READ, ("stderr", stderr_cap))
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("media process timed out")
                for key, _ in selector.select(timeout=min(remaining, 0.1)):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    stream, cap = key.data
                    if len(buffers[stream]) + len(chunk) > cap:
                        raise MediaOutputError(f"media process {stream} exceeded {cap} bytes")
                    buffers[stream].extend(chunk)
            exit_code = process.wait(timeout=max(0.1, deadline - time.monotonic()))
        finally:
            active_exception = sys.exc_info()[0] is not None
            cleanup_error = None
            try:
                if process.poll() is None:
                    self._terminate(process, terminate_process_group)
            except BaseException as exc:  # Cleanup must not mask the operation failure.
                cleanup_error = exc
            for pipe in (process.stdout, process.stderr):
                if pipe is not None:
                    try:
                        pipe.close()
                    except BaseException as exc:
                        cleanup_error = cleanup_error or exc
            if selector is not None:
                try:
                    selector.close()
                except BaseException as exc:
                    cleanup_error = cleanup_error or exc
            if cleanup_error is not None and not active_exception:
                raise cleanup_error
        return exit_code, bytes(buffers["stdout"]), bytes(buffers["stderr"])

    @staticmethod
    def _terminate(process: subprocess.Popen, process_group: bool) -> None:
        first_error = None
        try:
            if process_group:
                os.killpg(process.pid, signal.SIGTERM)
            else:
                process.terminate()
        except ProcessLookupError:
            pass
        except BaseException as exc:
            first_error = exc
        try:
            process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            try:
                if process_group:
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
            except BaseException as exc:
                first_error = first_error or exc
            try:
                process.wait(timeout=1.0)
            except BaseException as exc:
                first_error = first_error or exc
        except BaseException as exc:
            first_error = first_error or exc
            try:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=1.0)
            except BaseException as fallback_exc:
                first_error = first_error or fallback_exc
        if first_error is not None:
            raise first_error


class MediaAdapter:
    """Resolve only enrolled tools and execute a fresh verified copy per call."""

    def __init__(
        self,
        tool_store: TrustedMediaToolStore,
        *,
        runner=None,
        max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
        max_frame_output_bytes: int = MAX_DECODED_FRAME_BYTES,
    ) -> None:
        if isinstance(max_frame_output_bytes, bool) or not isinstance(max_frame_output_bytes, int) \
                or not 1 <= max_frame_output_bytes <= MAX_DECODED_FRAME_BYTES:
            raise ValueError("max_frame_output_bytes must be within the supported decoded-frame cap")
        self._tool_store = tool_store
        self._runner = runner or SubprocessMediaRunner()
        self.max_output_bytes = max_output_bytes
        self.max_frame_output_bytes = max_frame_output_bytes
        self.env = self._minimal_environment()

    def trusted_identity(self, kind: str) -> dict[str, str]:
        """Reverify one enrollment and expose only its fixed kind/path/digest identity."""
        tools = self._tool_store.load_required({kind})
        tool = tools[kind]
        try:
            return {"kind": kind, "path": tool.source_path, "sha256": tool.sha256}
        finally:
            self._tool_store.release(tool)

    def run(self, kind: str, argv: Sequence[str], *, timeout_seconds: int,
            pass_fds: Sequence[int] = ()) -> MediaResult:
        """Execute one enrolled kind with an argv-only, bounded process."""
        if isinstance(argv, (str, bytes)) or not all(isinstance(arg, str) for arg in argv):
            raise TypeError("argv must be a sequence of strings")
        if not isinstance(timeout_seconds, int) or isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive integer")
        tools = self._tool_store.load_required({kind})
        tool = tools[kind]
        try:
            try:
                exit_code, stdout, stderr = self._runner.run(
                    [tool.staged_path, *argv],
                    shell=False,
                    env=self.env,
                    timeout_seconds=timeout_seconds,
                    stdout_cap=self.max_output_bytes,
                    stderr_cap=self.max_output_bytes,
                    start_new_session=True,
                    terminate_process_group=True,
                    pass_fds=pass_fds,
                )
            except (TimeoutError, subprocess.TimeoutExpired) as exc:
                raise MediaTimeoutError(
                    f"{kind} timed out after {timeout_seconds}s; operation NOT resubmitted"
                ) from exc
            return MediaResult(exit_code=exit_code, stdout=stdout, stderr=stderr)
        finally:
            self._tool_store.release(tool)

    def _run_binary(
        self, kind: str, argv: Sequence[str], *, timeout_seconds: int,
        pass_fds: Sequence[int] = (), stdout_cap: int | None = None
    ) -> _BinaryMediaResult:
        """Execute one enrolled kind with bounded binary stdout for frame decoding."""
        if isinstance(argv, (str, bytes)) or not all(isinstance(arg, str) for arg in argv):
            raise TypeError("argv must be a sequence of strings")
        if not isinstance(timeout_seconds, int) or isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive integer")
        tools = self._tool_store.load_required({kind})
        tool = tools[kind]
        try:
            try:
                exit_code, stdout, stderr = self._runner.run_binary(
                    [tool.staged_path, *argv],
                    shell=False,
                    env=self.env,
                    timeout_seconds=timeout_seconds,
                    stdout_cap=self.max_frame_output_bytes if stdout_cap is None else stdout_cap,
                    stderr_cap=self.max_output_bytes,
                    start_new_session=True,
                    terminate_process_group=True,
                    pass_fds=pass_fds,
                )
            except (TimeoutError, subprocess.TimeoutExpired) as exc:
                raise MediaTimeoutError(
                    f"{kind} timed out after {timeout_seconds}s; operation NOT resubmitted"
                ) from exc
            return _BinaryMediaResult(exit_code=exit_code, stdout=stdout, stderr=stderr)
        finally:
            self._tool_store.release(tool)

    def probe_json(self, path: Path, *, source_fd: int | None = None) -> dict[str, object]:
        """Run ffprobe and require exactly one JSON object on stdout."""
        source = Path(path)
        if not source.is_absolute():
            raise MediaOutputError("ffprobe source path must be absolute")
        if source_fd is not None:
            os.lseek(source_fd, 0, os.SEEK_SET)
        source_arg = f"/dev/fd/{source_fd}" if source_fd is not None else str(source)
        result = self.run(
            "ffprobe",
            ["-v", "error", "-show_streams", "-show_format", "-of", "json", source_arg],
            timeout_seconds=30,
            pass_fds=() if source_fd is None else (source_fd,),
        )
        if result.exit_code != 0:
            raise MediaOutputError(
                f"ffprobe failed with exit {result.exit_code}: {result.stderr.strip()}"
            )
        decoder = json.JSONDecoder()
        text = result.stdout.lstrip()
        try:
            payload, end = decoder.raw_decode(text)
        except json.JSONDecodeError as exc:
            raise MediaOutputError("ffprobe did not emit valid JSON") from exc
        if text[end:].strip():
            raise MediaOutputError("ffprobe emitted more than one JSON document")
        if not isinstance(payload, dict):
            raise MediaOutputError("ffprobe JSON output must be an object")
        return payload

    def verify_video_frames(self, path: Path, duration_seconds: float, *,
                            source_fd: int | None = None) -> dict[str, object]:
        """Decode and fingerprint one bounded image at both clip anchors."""
        if not Path(path).is_absolute() or duration_seconds <= 0:
            raise MediaOutputError("video frame verification input is invalid")
        positions = {"start_anchor": 0.0, "end_anchor": max(0.0, duration_seconds - 0.05)}
        decoded: dict[str, object] = {}
        source_arg = f"/dev/fd/{source_fd}" if source_fd is not None else str(path)
        for name, position in positions.items():
            if source_fd is not None:
                os.lseek(source_fd, 0, os.SEEK_SET)
            result = self._run_binary("ffmpeg", ["-v", "error", "-ss", f"{position:.3f}",
                "-i", source_arg, "-map", "0:v:0", "-frames:v", "1",
                "-f", "image2pipe", "-vcodec", "png", "-"], timeout_seconds=30,
                pass_fds=() if source_fd is None else (source_fd,),
                stdout_cap=self.max_frame_output_bytes)
            if result.exit_code != 0:
                raise MediaOutputError(f"ffmpeg frame decode failed with exit {result.exit_code}")
            frame = result.stdout
            _validate_complete_png(frame)
            decoded[name] = {"requested_at_seconds": round(position, 3),
                             "sha256": hashlib.sha256(frame).hexdigest(),
                             "size_bytes": len(frame)}
        return {"readable": True, **decoded}

    def verify_image(self, path: Path, *, source_fd: int | None = None) -> dict[str, object]:
        """Decode one image through enrolled ffmpeg and return its canonical PNG identity."""
        source = Path(path)
        if not source.is_absolute():
            raise MediaOutputError("image verification path must be absolute")
        if source_fd is not None:
            os.lseek(source_fd, 0, os.SEEK_SET)
        source_arg = f"/dev/fd/{source_fd}" if source_fd is not None else str(source)
        result = self._run_binary("ffmpeg", ["-v", "error", "-i", source_arg,
            "-map", "0:v:0", "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
            timeout_seconds=30, pass_fds=() if source_fd is None else (source_fd,),
            stdout_cap=self.max_frame_output_bytes)
        if result.exit_code != 0:
            raise MediaOutputError(f"ffmpeg image decode failed with exit {result.exit_code}")
        width, height = _validate_complete_png(result.stdout)
        return {"sha256": hashlib.sha256(result.stdout).hexdigest(),
                "size_bytes": len(result.stdout), "width": width, "height": height}

    @staticmethod
    def _minimal_environment() -> dict[str, str]:
        allowed = ("HOME", "TMPDIR", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR")
        env = {key: os.environ[key] for key in allowed if key in os.environ}
        env["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"
        return env


__all__ = [
    "DEFAULT_MAX_OUTPUT_BYTES",
    "MediaAdapter",
    "MediaAdapterError",
    "MediaOutputError",
    "MediaResult",
    "MediaTimeoutError",
    "SubprocessMediaRunner",
]
