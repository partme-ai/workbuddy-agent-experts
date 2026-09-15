"""Containment, type, and size policy for local Dreamina upload inputs."""

from __future__ import annotations

import atexit
import hashlib
import os
import shutil
import stat
import tempfile
import uuid
import weakref
from pathlib import Path
from typing import Any, Iterable, Mapping


class ReferencePolicyError(ValueError):
    """A local upload reference violates the explicit approval boundary."""


IMAGE_ROLES = {"subject", "style", "frame"}
DEFAULT_MAX_IMAGE_BYTES = 50 * 1024 * 1024
DEFAULT_MAX_MEDIA_BYTES = 512 * 1024 * 1024


def _detect_mime(header: bytes) -> str | None:
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith((b"RIFF",)) and header[8:12] == b"WEBP":
        return "image/webp"
    if len(header) >= 12 and header[4:8] == b"ftyp":
        return "video/mp4"
    if header.startswith(b"ID3") or header.startswith((b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")):
        return "audio/mpeg"
    if header.startswith(b"RIFF") and header[8:12] == b"WAVE":
        return "audio/wav"
    return None


class ReferencePolicy:
    """Validate upload files against user-approved filesystem roots."""

    def __init__(
        self,
        *,
        approved_roots: Iterable[Path],
        max_image_bytes: int = DEFAULT_MAX_IMAGE_BYTES,
        max_media_bytes: int = DEFAULT_MAX_MEDIA_BYTES,
        durable_root: Path | None = None,
    ) -> None:
        self._roots = tuple(Path(root).resolve(strict=True) for root in approved_roots)
        if not self._roots or any(not root.is_dir() for root in self._roots):
            raise ValueError("approved_roots must contain existing directories")
        if max_image_bytes <= 0 or max_media_bytes <= 0:
            raise ValueError("reference size limits must be positive")
        self._max_image_bytes = max_image_bytes
        self._max_media_bytes = max_media_bytes
        handles: list[int] = []
        self._root_handles: tuple[int, ...] = ()
        self._durable_handle = None
        self._durable_root = Path(durable_root).resolve() if durable_root is not None else None
        try:
            for root in self._roots:
                handles.append(self._pin_directory(root, private=False))
            self._root_handles = tuple(handles)
            if self._durable_root is not None:
                self._durable_root.mkdir(mode=0o700, parents=True, exist_ok=True)
                self._durable_handle = self._pin_directory(self._durable_root, private=True)
            self._staging_root = Path(tempfile.mkdtemp(prefix="dreamina-references-"))
            os.chmod(self._staging_root, 0o700)
            atexit.register(shutil.rmtree, self._staging_root, True)
            self._finalizer = weakref.finalize(self, shutil.rmtree, self._staging_root, True)
        except Exception:
            self._root_handles = ()
            for handle in reversed(handles):
                try:
                    os.close(handle)
                except OSError:
                    pass
            if self._durable_handle is not None:
                os.close(self._durable_handle)
                self._durable_handle = None
            raise

    def validate(self, reference: Mapping[str, Any]) -> dict[str, Any]:
        normalized, resolved, source_fd, source_stat = self._inspect(reference)
        staged = self._staging_root / f"{uuid.uuid4().hex}{resolved.suffix.lower()}"
        with os.fdopen(source_fd, "rb") as reader, staged.open("xb") as writer:
            self._copy_stream(reader, writer)
            writer.flush()
            os.fsync(writer.fileno())
        self._assert_source_identity(resolved, source_stat)
        os.chmod(staged, 0o400)
        normalized["source_path"] = normalized["path"]
        normalized["path"] = str(staged)
        return normalized

    def validate_for_quote(self, reference: Mapping[str, Any]) -> dict[str, Any]:
        """Publish and validate a private content-addressed durable reference."""
        if self._durable_root is None:
            raise ReferencePolicyError("durable_root is required for quote references")
        normalized, resolved, source_fd, source_stat = self._inspect(reference)
        root_fd = -1
        temp_name: str | None = None
        try:
            root_fd = self._verified_durable_handle()
            target_name = f"{normalized['sha256']}{resolved.suffix.lower()}"
            try:
                winner_fd = os.open(target_name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=root_fd)
            except FileNotFoundError:
                winner_fd = -1
            except OSError as exc:
                raise ReferencePolicyError("durable reference collision is unsafe") from exc
            if winner_fd >= 0:
                self._verify_winner(winner_fd, target_name, normalized)
                normalized["path"] = str(self._durable_root / target_name)
                return normalized
            temp_name = f".reference-{uuid.uuid4().hex}"
            temp_fd = os.open(temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o400, dir_fd=root_fd)
            owned_source_fd = source_fd
            source_fd = -1
            with os.fdopen(owned_source_fd, "rb") as reader, os.fdopen(temp_fd, "wb") as writer:
                self._copy_stream(reader, writer)
                writer.flush()
                os.fsync(writer.fileno())
            self._assert_source_identity(resolved, source_stat)
            verify_fd = os.open(temp_name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=root_fd)
            try:
                copied_stat = os.fstat(verify_fd)
                if copied_stat.st_size != normalized["size_bytes"] or self._sha256_fd(verify_fd) != normalized["sha256"]:
                    raise ReferencePolicyError("reference changed during durable publication")
            finally:
                os.close(verify_fd)
            try:
                os.link(temp_name, target_name, src_dir_fd=root_fd, dst_dir_fd=root_fd, follow_symlinks=False)
            except FileExistsError:
                pass
            os.fsync(root_fd)
            try:
                os.unlink(temp_name, dir_fd=root_fd)
            except FileNotFoundError:
                pass
            temp_name = None
            winner_fd = os.open(target_name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=root_fd)
            self._verify_winner(winner_fd, target_name, normalized)
            normalized["path"] = str(self._durable_root / target_name)
            return normalized
        except OSError as exc:
            raise ReferencePolicyError("durable reference publication failed") from exc
        finally:
            if temp_name is not None and root_fd >= 0:
                try:
                    os.unlink(temp_name, dir_fd=root_fd)
                except FileNotFoundError:
                    pass
            if source_fd >= 0:
                os.close(source_fd)

    def _verify_winner(self, winner_fd: int, target_name: str, normalized: Mapping[str, Any]) -> None:
        try:
            winner_stat = os.fstat(winner_fd)
            if not stat.S_ISREG(winner_stat.st_mode) or stat.S_IMODE(winner_stat.st_mode) != 0o400 or winner_stat.st_uid != os.getuid():
                raise ReferencePolicyError("durable reference is not an owned private regular file")
            if winner_stat.st_size != normalized["size_bytes"] or self._sha256_fd(winner_fd) != normalized["sha256"]:
                raise ReferencePolicyError("durable reference digest or size mismatch")
            self._verified_durable_handle()
            path_stat = os.stat(target_name, dir_fd=self._durable_handle, follow_symlinks=False)
            if (path_stat.st_dev, path_stat.st_ino, path_stat.st_size, stat.S_IMODE(path_stat.st_mode)) != (winner_stat.st_dev, winner_stat.st_ino, winner_stat.st_size, 0o400):
                raise ReferencePolicyError("durable reference changed during validation")
        except OSError as exc:
            raise ReferencePolicyError("durable reference changed during validation") from exc
        finally:
            os.close(winner_fd)

    def _inspect(self, reference: Mapping[str, Any]) -> tuple[dict[str, Any], Path, int, os.stat_result]:
        raw_path = Path(str(reference.get("path", "")))
        if not raw_path.is_absolute() or raw_path.is_symlink():
            raise ReferencePolicyError("reference path must be an absolute non-symlink path")
        try:
            resolved = raw_path.resolve(strict=True)
        except OSError as exc:
            raise ReferencePolicyError(f"reference file is unavailable: {raw_path}") from exc
        if not resolved.is_file():
            raise ReferencePolicyError("reference must be a regular file without symlink traversal")
        if not any(_is_within(resolved, root) for root in self._roots):
            raise ReferencePolicyError("reference escapes approved roots")
        fd = self._open_approved(resolved)
        opened_stat = os.fstat(fd)
        current_stat = resolved.stat()
        if (opened_stat.st_dev, opened_stat.st_ino) != (current_stat.st_dev, current_stat.st_ino):
            os.close(fd)
            raise ReferencePolicyError("reference changed while it was being opened")
        if not stat.S_ISREG(opened_stat.st_mode) or opened_stat.st_uid != os.getuid() or stat.S_IMODE(opened_stat.st_mode) & 0o022:
            os.close(fd)
            raise ReferencePolicyError("reference ownership or mode is unsafe")
        size = opened_stat.st_size
        declared_size = reference.get("size_bytes")
        if declared_size is not None and int(declared_size) != size:
            os.close(fd)
            raise ReferencePolicyError("reference size_bytes does not match the file")
        digest = hashlib.sha256()
        header = b""
        with os.fdopen(os.dup(fd), "rb") as reader:
            while True:
                chunk = reader.read(1024 * 1024)
                if not chunk:
                    break
                if not header:
                    header = chunk[:32]
                digest.update(chunk)
        after_read = os.fstat(fd)
        if (after_read.st_dev, after_read.st_ino, after_read.st_size, after_read.st_mtime_ns, stat.S_IFMT(after_read.st_mode)) != (
            opened_stat.st_dev, opened_stat.st_ino, opened_stat.st_size, opened_stat.st_mtime_ns, stat.S_IFMT(opened_stat.st_mode)
        ):
            os.close(fd)
            raise ReferencePolicyError("reference changed while it was being read")
        os.lseek(fd, 0, os.SEEK_SET)
        mime = _detect_mime(header)
        if mime is None:
            os.close(fd)
            raise ReferencePolicyError("reference media type is not recognized")
        role = str(reference.get("role", "")).lower()
        if role in IMAGE_ROLES and not mime.startswith("image/"):
            os.close(fd)
            raise ReferencePolicyError(f"role {role} requires an image")
        if role == "audio" and not mime.startswith("audio/"):
            os.close(fd)
            raise ReferencePolicyError("audio role requires an audio file")
        if role == "reference" and not mime.startswith("video/"):
            os.close(fd)
            raise ReferencePolicyError("reference role requires a video file")
        limit = self._max_image_bytes if mime.startswith("image/") else self._max_media_bytes
        if size > limit:
            os.close(fd)
            raise ReferencePolicyError(f"reference exceeds byte limit {limit}")
        normalized = dict(reference)
        normalized["path"] = str(resolved)
        normalized["mime_type"] = mime
        normalized["size_bytes"] = size
        normalized["sha256"] = digest.hexdigest()
        return normalized, resolved, fd, opened_stat

    def close(self) -> None:
        self._finalizer()
        handles, self._root_handles = self._root_handles, ()
        for handle in handles:
            try:
                os.close(handle)
            except OSError:
                pass
        if self._durable_handle is not None:
            try:
                os.close(self._durable_handle)
            except OSError:
                pass
            self._durable_handle = None

    @staticmethod
    def _pin_directory(path: Path, *, private: bool) -> int:
        handle = os.open(path, os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0))
        metadata = os.fstat(handle)
        expected = 0o700 if private else stat.S_IMODE(metadata.st_mode)
        mode = stat.S_IMODE(metadata.st_mode)
        if metadata.st_uid != os.getuid() or (private and mode != expected) or (not private and mode & 0o022):
            os.close(handle)
            raise ReferencePolicyError("reference directory ownership or mode is unsafe")
        return handle

    def _open_approved(self, path: Path) -> int:
        for root, root_fd in zip(self._roots, self._root_handles):
            try:
                parts = path.relative_to(root).parts
            except ValueError:
                continue
            if not parts or any(part in {"", ".", ".."} for part in parts):
                continue
            directory_fd = os.dup(root_fd)
            try:
                for part in parts[:-1]:
                    next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0), dir_fd=directory_fd)
                    os.close(directory_fd)
                    directory_fd = next_fd
                return os.open(parts[-1], os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=directory_fd)
            except OSError:
                pass
            finally:
                os.close(directory_fd)
        raise ReferencePolicyError("reference file cannot be opened beneath an approved root")

    def _verified_durable_handle(self) -> int:
        if self._durable_handle is None or self._durable_root is None:
            raise ReferencePolicyError("durable_root is required for quote references")
        pinned = os.fstat(self._durable_handle)
        current = os.stat(self._durable_root, follow_symlinks=False)
        if (pinned.st_dev, pinned.st_ino) != (current.st_dev, current.st_ino):
            raise ReferencePolicyError("durable root changed after authorization")
        if pinned.st_uid != os.getuid() or stat.S_IMODE(pinned.st_mode) != 0o700:
            raise ReferencePolicyError("durable root ownership or mode is unsafe")
        return self._durable_handle

    @staticmethod
    def _copy_stream(reader: Any, writer: Any) -> None:
        while chunk := reader.read(1024 * 1024):
            writer.write(chunk)

    @staticmethod
    def _sha256_fd(fd: int) -> str:
        os.lseek(fd, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        while chunk := os.read(fd, 1024 * 1024):
            digest.update(chunk)
        os.lseek(fd, 0, os.SEEK_SET)
        return digest.hexdigest()

    @staticmethod
    def _assert_source_identity(path: Path, expected: os.stat_result) -> None:
        current = os.stat(path, follow_symlinks=False)
        if (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns, current.st_uid, stat.S_IMODE(current.st_mode)) != (
            expected.st_dev, expected.st_ino, expected.st_size, expected.st_mtime_ns, expected.st_uid, stat.S_IMODE(expected.st_mode)
        ):
            raise ReferencePolicyError("reference changed during durable publication")


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = ["ReferencePolicy", "ReferencePolicyError"]
