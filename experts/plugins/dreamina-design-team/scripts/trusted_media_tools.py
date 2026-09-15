"""Enrollment and private staging for trusted local media executables."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from scripts.native_approval import NativeApprovalProvider


MEDIA_TOOL_KINDS = frozenset({"ffmpeg", "ffprobe", "whisper", "narration"})
_DIGEST = re.compile(r"^[a-f0-9]{64}$")


class TrustedMediaToolError(PermissionError):
    """A media executable or its protected trust record is invalid."""


@dataclass(frozen=True)
class TrustedMediaTool:
    """A verified executable copied into a private per-process directory."""

    kind: str
    source_path: str
    sha256: str
    staged_path: str


class TrustedMediaToolStore:
    """Persist approved tool digests and create verified execution copies."""

    def __init__(self, path: Path | None = None, staging_root: Path | None = None) -> None:
        self.path = path or (
            Path.home() / ".config" / "codex-dreamina-design" / "trusted-media-tools.json"
        )
        self._staging_root = Path(staging_root) if staging_root is not None else None

    def enroll(self, kind: str, path: Path, approval_provider=None) -> dict[str, str | int]:
        """Approve and persist the identity of one fixed-purpose media tool."""
        self._validate_kinds({kind})
        source = Path(path)
        canonical, owner_uid, digest = self._inspect_source(kind, source)
        provider = approval_provider or NativeApprovalProvider()
        provider.confirm_media_tool_enrollment(
            kind=kind,
            path=canonical,
            owner_uid=owner_uid,
            sha256=digest,
        )
        tools = self._load_config(allow_missing=True)
        record = {"source_path": canonical, "owner_uid": owner_uid, "sha256": digest}
        tools[kind] = record
        self._atomic_write({"version": 1, "tools": tools})
        return record.copy()

    def load_required(self, kinds: Iterable[str]) -> dict[str, TrustedMediaTool]:
        """Load, re-hash, and privately stage every requested enrolled tool."""
        required = set(kinds)
        self._validate_kinds(required)
        tools = self._load_config()
        missing = required.difference(tools)
        if missing:
            raise TrustedMediaToolError(
                "required media tools are not enrolled: " + ", ".join(sorted(missing))
            )
        loaded: dict[str, TrustedMediaTool] = {}
        try:
            for kind in sorted(required):
                record = tools[kind]
                loaded[kind] = self._stage(
                    kind,
                    str(record["source_path"]),
                    int(record["owner_uid"]),
                    str(record["sha256"]),
                )
            return loaded
        except Exception:
            for tool in loaded.values():
                self.release(tool)
            raise

    @staticmethod
    def release(tool: TrustedMediaTool) -> None:
        """Remove a private staged executable after its process lifetime."""
        shutil.rmtree(Path(tool.staged_path).parent, ignore_errors=True)

    @staticmethod
    def _validate_kinds(kinds: set[str]) -> None:
        if not kinds.issubset(MEDIA_TOOL_KINDS):
            unknown = kinds.difference(MEDIA_TOOL_KINDS)
            raise TrustedMediaToolError("unsupported media tool kind: " + ", ".join(sorted(unknown)))

    @staticmethod
    def _inspect_source(kind: str, source: Path) -> tuple[str, int, str]:
        if not source.is_absolute() or source.is_symlink():
            raise TrustedMediaToolError(
                "media tool enrollment requires an absolute regular non-symlink file"
            )
        try:
            source_stat = source.stat()
        except OSError as exc:
            raise TrustedMediaToolError("media tool does not exist") from exc
        if not stat.S_ISREG(source_stat.st_mode) or not source_stat.st_mode & 0o111:
            raise TrustedMediaToolError("media tool must be a regular executable file")
        canonical = source.resolve(strict=True)
        system_say = kind == "narration" and str(canonical) == "/usr/bin/say" and source_stat.st_uid == 0
        if (source_stat.st_uid != os.getuid() and not system_say) or source_stat.st_mode & 0o022:
            raise TrustedMediaToolError("media tool owner or write permissions are not trusted")
        for parent in canonical.parents:
            if parent.stat().st_mode & 0o022:
                raise TrustedMediaToolError(f"group/world-writable media tool parent: {parent}")
        digest, opened_stat = _digest_opened_file(canonical)
        if (opened_stat.st_dev, opened_stat.st_ino) != (source_stat.st_dev, source_stat.st_ino):
            raise TrustedMediaToolError("media tool changed during enrollment")
        return str(canonical), opened_stat.st_uid, digest

    def _load_config(self, *, allow_missing: bool = False) -> dict[str, dict[str, str | int]]:
        self._ensure_private_config_directory(create=allow_missing)
        if not self.path.exists():
            if allow_missing:
                return {}
            raise TrustedMediaToolError("trusted media tools are not enrolled")
        if self.path.is_symlink() or not self.path.is_file():
            raise TrustedMediaToolError("trusted media tool config must be a regular file")
        config_stat = self.path.stat()
        if config_stat.st_uid != os.getuid() or stat.S_IMODE(config_stat.st_mode) != 0o600:
            raise TrustedMediaToolError("trusted media tool config must be user-owned mode 0600")
        parent = self.path.parent
        if (
            parent.is_symlink()
            or parent.stat().st_uid != os.getuid()
            or stat.S_IMODE(parent.stat().st_mode) != 0o700
        ):
            raise TrustedMediaToolError(
                "trusted media tool config directory must be user-owned mode 0700"
            )
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TrustedMediaToolError("trusted media tool config is invalid") from exc
        if not isinstance(payload, dict) or set(payload) != {"version", "tools"}:
            raise TrustedMediaToolError("trusted media tool config has unexpected fields")
        if payload["version"] != 1 or not isinstance(payload["tools"], dict):
            raise TrustedMediaToolError("trusted media tool config version is invalid")
        tools: dict[str, dict[str, str | int]] = {}
        for kind, record in payload["tools"].items():
            self._validate_kinds({kind})
            if not isinstance(record, dict) or set(record) != {
                "source_path",
                "owner_uid",
                "sha256",
            }:
                raise TrustedMediaToolError("trusted media tool record has unexpected fields")
            source_path = record["source_path"]
            owner_uid = record["owner_uid"]
            digest = record["sha256"]
            if not isinstance(source_path, str) or not Path(source_path).is_absolute():
                raise TrustedMediaToolError("trusted media tool source path is invalid")
            if not isinstance(digest, str) or _DIGEST.fullmatch(digest) is None:
                raise TrustedMediaToolError("trusted media tool digest is invalid")
            if not isinstance(owner_uid, int) or isinstance(owner_uid, bool):
                raise TrustedMediaToolError("trusted media tool owner UID is invalid")
            if owner_uid != os.getuid() and not (
                    kind == "narration" and source_path == "/usr/bin/say" and owner_uid == 0):
                raise TrustedMediaToolError("trusted media tool recorded owner does not match user")
            tools[kind] = {
                "source_path": source_path,
                "owner_uid": owner_uid,
                "sha256": digest,
            }
        return tools

    def _stage(
        self, kind: str, source_path: str, expected_owner_uid: int, expected_sha256: str
    ) -> TrustedMediaTool:
        source = Path(source_path)
        canonical, current_owner_uid, current_sha256 = self._inspect_source(kind, source)
        if (
            canonical != source_path
            or (expected_owner_uid != os.getuid() and not (
                kind == "narration" and source_path == "/usr/bin/say" and expected_owner_uid == 0))
            or current_owner_uid != expected_owner_uid
            or not hmac.compare_digest(current_sha256, expected_sha256)
        ):
            raise TrustedMediaToolError(
                f"trusted {kind} owner, digest, or path changed after enrollment"
            )
        if self._staging_root is not None:
            self._staging_root.mkdir(parents=True, exist_ok=True)
            os.chmod(self._staging_root, 0o700)
            private_root = Path(tempfile.mkdtemp(prefix=f"{kind}-", dir=self._staging_root))
        else:
            private_root = Path(tempfile.mkdtemp(prefix=f"dreamina-{kind}-"))
        os.chmod(private_root, 0o700)
        staged = private_root / kind
        try:
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            digest = hashlib.sha256()
            with os.fdopen(os.open(source, flags), "rb") as reader, staged.open("xb") as writer:
                while chunk := reader.read(1024 * 1024):
                    digest.update(chunk)
                    writer.write(chunk)
                writer.flush()
                os.fsync(writer.fileno())
            if not hmac.compare_digest(digest.hexdigest(), expected_sha256):
                raise TrustedMediaToolError(f"trusted {kind} changed while being staged")
            os.chmod(staged, 0o500)
            return TrustedMediaTool(kind, source_path, expected_sha256, str(staged))
        except Exception:
            shutil.rmtree(private_root, ignore_errors=True)
            raise

    def _atomic_write(self, payload: dict[str, object]) -> None:
        directory_fd = self._open_private_config_directory(create=True)
        tmp_name = f".trusted-media-tools.{secrets.token_hex(12)}"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        fd: int | None = None
        temp_created = False
        try:
            fd = os.open(tmp_name, flags, 0o600, dir_fd=directory_fd)
            temp_created = True
            os.fchmod(fd, 0o600)
            handle = os.fdopen(fd, "w", encoding="utf-8")
            fd = None  # Ownership transferred to the file object.
            with handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(
                tmp_name,
                self.path.name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
            )
            os.fsync(directory_fd)
        except Exception:
            if temp_created:
                try:
                    os.unlink(tmp_name, dir_fd=directory_fd)
                except FileNotFoundError:
                    pass
            raise
        finally:
            try:
                if fd is not None:
                    os.close(fd)
            finally:
                os.close(directory_fd)

    def _ensure_private_config_directory(self, *, create: bool) -> os.stat_result:
        parent = self.path.parent
        try:
            parent_stat = parent.lstat()
        except FileNotFoundError:
            if not create:
                raise TrustedMediaToolError("trusted media tool config directory does not exist")
            parent.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.mkdir(parent, 0o700)
            except FileExistsError:
                pass
            parent_stat = parent.lstat()
        if (
            not stat.S_ISDIR(parent_stat.st_mode)
            or parent_stat.st_uid != os.getuid()
            or stat.S_IMODE(parent_stat.st_mode) != 0o700
        ):
            raise TrustedMediaToolError(
                "trusted media tool config directory must be a user-owned non-symlink mode 0700 directory"
            )
        return parent_stat

    def _open_private_config_directory(self, *, create: bool) -> int:
        expected = self._ensure_private_config_directory(create=create)
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            directory_fd = os.open(self.path.parent, flags)
        except OSError as exc:
            raise TrustedMediaToolError("trusted media tool config directory is unsafe") from exc
        opened = os.fstat(directory_fd)
        if (
            (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino)
            or opened.st_uid != os.getuid()
            or stat.S_IMODE(opened.st_mode) != 0o700
        ):
            os.close(directory_fd)
            raise TrustedMediaToolError("trusted media tool config directory changed")
        return directory_fd


def _digest_opened_file(path: Path) -> tuple[str, os.stat_result]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    digest = hashlib.sha256()
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise TrustedMediaToolError("media tool could not be opened safely") from exc
    with os.fdopen(descriptor, "rb") as handle:
        opened_stat = os.fstat(handle.fileno())
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest(), opened_stat


__all__ = [
    "MEDIA_TOOL_KINDS",
    "TrustedMediaTool",
    "TrustedMediaToolError",
    "TrustedMediaToolStore",
]
