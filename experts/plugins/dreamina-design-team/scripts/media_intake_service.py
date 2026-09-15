"""Fail-closed local source-video intake into private project storage."""

from __future__ import annotations

import hashlib
import fcntl
import os
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from scripts.json_contracts import canonical_fingerprint, validate_contract
from scripts.native_approval import NativeApprovalProvider
from scripts.video_project_store import VideoProjectStore


DEFAULT_MAX_SOURCE_BYTES = 2 * 1024 * 1024 * 1024
DEFAULT_MAX_DURATION_SECONDS = 1800.0


class MediaIntakeError(RuntimeError):
    """The source failed a local trust, type, or stability check."""


class MediaLimitError(MediaIntakeError):
    """The source must be segmented before it can be processed."""

    def __init__(self, reason: str) -> None:
        self.action = {"type": "segment_source", "reason": reason}
        super().__init__(f"segment_source: {reason}")


class MediaIntakeService:
    """Copy an approved source into one project after native confirmation."""

    def __init__(
        self,
        project_store: VideoProjectStore,
        media_adapter,
        approval_provider: NativeApprovalProvider | None = None,
        *,
        max_source_bytes: int = DEFAULT_MAX_SOURCE_BYTES,
        max_duration_seconds: float = DEFAULT_MAX_DURATION_SECONDS,
    ) -> None:
        self._store = project_store
        self._media_adapter = media_adapter
        self._approval_provider = approval_provider or NativeApprovalProvider()
        self._max_source_bytes = max_source_bytes
        self._max_duration_seconds = max_duration_seconds

    def intake(
        self,
        project_id: str,
        source_path: Path,
        approved_roots: Iterable[Path],
    ) -> dict[str, Any]:
        source = Path(source_path)
        if not source.is_absolute():
            raise MediaIntakeError("source path must be absolute")
        roots = self._approved_roots(approved_roots)
        self._require_inside(source, roots)
        try:
            before_path = source.lstat()
        except OSError as exc:
            raise MediaIntakeError("source cannot be inspected") from exc
        if stat.S_ISLNK(before_path.st_mode) or not stat.S_ISREG(before_path.st_mode):
            raise MediaIntakeError("source must be a regular non-symlink file")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(source, flags)
        except OSError as exc:
            raise MediaIntakeError("source cannot be opened without following links") from exc
        attempt_path: Path | None = None
        try:
            opened = os.fstat(descriptor)
            if (opened.st_dev, opened.st_ino) != (before_path.st_dev, before_path.st_ino):
                raise MediaIntakeError("source inode changed during open")
            if opened.st_size > self._max_source_bytes:
                raise MediaLimitError("source exceeds 2 GiB")
            mime_type = self._mime_type(descriptor)
            attempt_path, digest, copied_size = self._stage_attempt(project_id, descriptor)
            self._require_source_stable(source, descriptor, opened, copied_size)
            probe = self._media_adapter.probe_json(attempt_path)
            self._require_source_stable(source, descriptor, opened, copied_size)
            metadata = self._probe_metadata(probe)
            self._require_probe_agreement(mime_type, metadata["format_name"])
            duration = metadata["duration_seconds"]
            if duration > self._max_duration_seconds:
                raise MediaLimitError("source exceeds 1800 seconds")
            receipt_base = {
                "schema_version": "1.0",
                "project_id": project_id,
                "source_sha256": digest,
                "size_bytes": copied_size,
                "mime_type": mime_type,
                "video_codec": metadata["video_codec"],
                "width": metadata["width"],
                "height": metadata["height"],
                "fps": metadata["fps"],
                "duration_seconds": duration,
                "audio_streams": metadata["audio_streams"],
                "approved_roots_digest": canonical_fingerprint(
                    {"approved_roots": [str(root) for root in roots]}
                ),
            }
            self._approval_provider.confirm(
                {
                    "operation": "reference-video-source-intake",
                    "project_id": project_id,
                    "source_sha256": digest,
                    "purpose": "reference-video-processing",
                }
            )
            return self._publish_approved(
                project_id, attempt_path, digest, mime_type, copied_size, receipt_base
            )
        finally:
            os.close(descriptor)
            if attempt_path is not None:
                try:
                    attempt_path.unlink()
                except FileNotFoundError:
                    pass

    @staticmethod
    def _approved_roots(values: Iterable[Path]) -> tuple[Path, ...]:
        roots: list[Path] = []
        for value in values:
            root = Path(value)
            if not root.is_absolute() or root.is_symlink():
                raise MediaIntakeError("approved roots must be absolute non-symlink directories")
            try:
                resolved = root.resolve(strict=True)
            except OSError as exc:
                raise MediaIntakeError("approved root does not exist") from exc
            if not resolved.is_dir():
                raise MediaIntakeError("approved root must be a directory")
            roots.append(resolved)
        if not roots:
            raise MediaIntakeError("at least one approved root is required")
        return tuple(sorted(set(roots), key=str))

    @staticmethod
    def _require_inside(source: Path, roots: tuple[Path, ...]) -> None:
        try:
            resolved = source.resolve(strict=True)
        except OSError as exc:
            raise MediaIntakeError("source does not exist") from exc
        if source.is_symlink() or not any(resolved.is_relative_to(root) for root in roots):
            raise MediaIntakeError("source is outside approved roots or is a symlink")

    def _stage_attempt(
        self, project_id: str, source_descriptor: int
    ) -> tuple[Path, str, int]:
        source_root = self._store.project_root(project_id) / "source"
        source_root.mkdir(mode=0o700, exist_ok=True)
        os.chmod(source_root, 0o700)
        descriptor, temporary = tempfile.mkstemp(prefix=".intake-", dir=source_root)
        digest = hashlib.sha256()
        copied_size = 0
        try:
            os.fchmod(descriptor, 0o600)
            os.lseek(source_descriptor, 0, os.SEEK_SET)
            with os.fdopen(descriptor, "wb") as output:
                while True:
                    chunk = os.read(source_descriptor, 1024 * 1024)
                    if not chunk:
                        break
                    copied_size += len(chunk)
                    if copied_size > self._max_source_bytes:
                        raise MediaLimitError("source exceeds 2 GiB while copying")
                    digest.update(chunk)
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            return Path(temporary), digest.hexdigest(), copied_size
        except BaseException:
            try:
                os.close(descriptor)
            except OSError:
                pass
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    @staticmethod
    def _mime_type(descriptor: int) -> str:
        os.lseek(descriptor, 0, os.SEEK_SET)
        header = os.read(descriptor, 4096)
        if len(header) >= 12 and header[4:8] == b"ftyp":
            brand = header[8:12]
            return "video/quicktime" if brand == b"qt  " else "video/mp4"
        if header.startswith(b"\x1aE\xdf\xa3") and MediaIntakeService._ebml_doc_type(header) == "webm":
            return "video/webm"
        raise MediaIntakeError("source bytes are not a supported video container")

    @staticmethod
    def _ebml_doc_type(header: bytes) -> str | None:
        if not header.startswith(b"\x1aE\xdf\xa3"):
            return None
        header_size = MediaIntakeService._ebml_vint(header, 4, clear_marker=True)
        if header_size is None:
            return None
        declared_size, size_length = header_size
        cursor = 4 + size_length
        header_end = cursor + declared_size
        if header_end > len(header):
            return None
        while cursor < header_end:
            element_id = MediaIntakeService._ebml_vint(header, cursor, clear_marker=False)
            if element_id is None:
                return None
            identifier, identifier_length = element_id
            cursor += identifier_length
            element_size = MediaIntakeService._ebml_vint(header, cursor, clear_marker=True)
            if element_size is None:
                return None
            size, element_size_length = element_size
            cursor += element_size_length
            end = cursor + size
            if end > header_end:
                return None
            if identifier == 0x4282:
                try:
                    return header[cursor:end].decode("ascii").lower()
                except UnicodeDecodeError:
                    return None
            cursor = end
        return None

    @staticmethod
    def _ebml_vint(data: bytes, offset: int, *, clear_marker: bool) -> tuple[int, int] | None:
        if offset >= len(data) or data[offset] == 0:
            return None
        first = data[offset]
        mask = 0x80
        length = 1
        while length <= 8 and not first & mask:
            mask >>= 1
            length += 1
        if length > 8 or offset + length > len(data):
            return None
        value = first & (mask - 1) if clear_marker else first
        for index in range(1, length):
            value = (value << 8) | data[offset + index]
        if clear_marker and value == (1 << (7 * length)) - 1:
            return None
        return value, length

    @staticmethod
    def _require_source_stable(
        source: Path, descriptor: int, opened: os.stat_result, copied_size: int
    ) -> None:
        try:
            path_stat = source.lstat()
            descriptor_stat = os.fstat(descriptor)
        except OSError as exc:
            raise MediaIntakeError("source changed during intake") from exc
        identity = (opened.st_dev, opened.st_ino, opened.st_size)
        if (
            (path_stat.st_dev, path_stat.st_ino, path_stat.st_size) != identity
            or (descriptor_stat.st_dev, descriptor_stat.st_ino, descriptor_stat.st_size) != identity
            or copied_size != opened.st_size
        ):
            raise MediaIntakeError("source size or inode changed during intake")

    @staticmethod
    def _require_probe_agreement(mime_type: str, format_name: str) -> None:
        formats = {item.strip().lower() for item in format_name.split(",")}
        if mime_type == "video/webm":
            agrees = "webm" in formats
        else:
            iso_bmff_formats = formats.intersection({"mov", "mp4"})
            expected = "mov" if mime_type == "video/quicktime" else "mp4"
            agrees = iso_bmff_formats == {"mov", "mp4"} or expected in iso_bmff_formats
        if not agrees:
            raise MediaIntakeError("source bytes and ffprobe format disagree")

    def _publish_approved(
        self,
        project_id: str,
        attempt_path: Path,
        digest: str,
        mime_type: str,
        copied_size: int,
        receipt_base: dict[str, Any],
    ) -> dict[str, Any]:
        source_root = self._store.project_root(project_id) / "source"
        suffix = {"video/mp4": ".mp4", "video/quicktime": ".mov", "video/webm": ".webm"}[
            mime_type
        ]
        final = source_root / f"{digest}{suffix}"
        lock_descriptor = os.open(source_root / ".publish.lock", os.O_RDWR | os.O_CREAT, 0o600)
        try:
            os.fchmod(lock_descriptor, 0o600)
            fcntl.flock(lock_descriptor, fcntl.LOCK_EX)
            os.chmod(attempt_path, 0o400)
            try:
                os.link(attempt_path, final, follow_symlinks=False)
            except FileExistsError:
                pass
            self._verify_staged(final, digest, copied_size)
            directory = os.open(source_root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            receipt = {
                **receipt_base,
                "staged_path": str(final),
                "intake_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
            return self._store.write_version(
                project_id,
                "source_receipt",
                receipt,
                schema_name="source_receipt.schema.json",
            )
        finally:
            fcntl.flock(lock_descriptor, fcntl.LOCK_UN)
            os.close(lock_descriptor)

    @staticmethod
    def _verify_staged(path: Path, digest: str, expected_size: int) -> None:
        try:
            info = path.lstat()
            if (
                stat.S_ISLNK(info.st_mode)
                or not stat.S_ISREG(info.st_mode)
                or info.st_mode & 0o777 != 0o400
            ):
                raise MediaIntakeError("staged source is missing or changed")
            descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            try:
                opened = os.fstat(descriptor)
                actual = hashlib.sha256()
                bytes_read = 0
                while True:
                    chunk = os.read(descriptor, 1024 * 1024)
                    if not chunk:
                        break
                    bytes_read += len(chunk)
                    actual.update(chunk)
                opened_after = os.fstat(descriptor)
                path_after = path.lstat()
                expected_identity = (info.st_dev, info.st_ino, expected_size)
                if (
                    (info.st_dev, info.st_ino, info.st_size) != expected_identity
                    or (opened.st_dev, opened.st_ino, opened.st_size) != expected_identity
                    or (opened_after.st_dev, opened_after.st_ino, opened_after.st_size)
                    != expected_identity
                    or (path_after.st_dev, path_after.st_ino, path_after.st_size)
                    != expected_identity
                    or opened.st_mode & 0o777 != 0o400
                    or opened_after.st_mode & 0o777 != 0o400
                    or path_after.st_mode & 0o777 != 0o400
                    or bytes_read != expected_size
                ):
                    raise MediaIntakeError("staged source inode or size changed")
                if actual.hexdigest() != digest:
                    raise MediaIntakeError("staged source digest changed")
            finally:
                os.close(descriptor)
        except OSError as exc:
            raise MediaIntakeError("staged source is missing or changed") from exc

    @staticmethod
    def _probe_metadata(probe: dict[str, object]) -> dict[str, Any]:
        streams = probe.get("streams")
        file_format = probe.get("format")
        if not isinstance(streams, list) or not isinstance(file_format, dict):
            raise MediaIntakeError("ffprobe returned incomplete metadata")
        videos = [item for item in streams if isinstance(item, dict) and item.get("codec_type") == "video"]
        if not videos:
            raise MediaIntakeError("ffprobe found no video stream")
        video = videos[0]
        try:
            numerator, denominator = str(video.get("avg_frame_rate", "0/1")).split("/", 1)
            fps = float(numerator) / float(denominator)
            duration = float(file_format["duration"])
            result = {
                "format_name": str(file_format["format_name"]),
                "video_codec": str(video["codec_name"]),
                "width": int(video["width"]),
                "height": int(video["height"]),
                "fps": fps,
                "duration_seconds": duration,
                "audio_streams": [
                    {
                        "codec": str(item["codec_name"]),
                        "channels": int(item["channels"]),
                        "sample_rate": int(item["sample_rate"]),
                    }
                    for item in streams
                    if isinstance(item, dict) and item.get("codec_type") == "audio"
                ],
            }
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            raise MediaIntakeError("ffprobe returned invalid metadata") from exc
        if (
            not result["format_name"]
            or not result["video_codec"]
            or result["width"] < 1
            or result["height"] < 1
            or fps <= 0
            or duration < 0
            or any(
                not item["codec"] or item["channels"] < 1 or item["sample_rate"] < 1
                for item in result["audio_streams"]
            )
        ):
            raise MediaIntakeError("ffprobe metadata is outside valid bounds")
        return result


__all__ = [
    "DEFAULT_MAX_DURATION_SECONDS",
    "DEFAULT_MAX_SOURCE_BYTES",
    "MediaIntakeError",
    "MediaIntakeService",
    "MediaLimitError",
]
