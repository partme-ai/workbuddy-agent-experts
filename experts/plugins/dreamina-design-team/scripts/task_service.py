"""Closed, query-only Dreamina task automation and verified downloads."""
from __future__ import annotations
import hashlib
import os
import re
import secrets
import stat
import time
from pathlib import Path
from collections.abc import Mapping
from scripts.output_redactor import redact_value

IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
FILTERS = {"gen_status", "aigc_type", "session"}
STATUS_MAP = {"querying": "querying", "queued": "querying", "pending": "querying",
              "processing": "querying", "running": "querying", "generating": "querying",
              "success": "success", "succeeded": "success", "completed": "success",
              "fail": "failed", "failed": "failed", "failure": "failed", "error": "failed"}
MAX_ARTIFACT_BYTES = 512 * 1024 * 1024

class TaskService:
    def __init__(self, adapter, *, sleeper=time.sleep):
        self.adapter = adapter
        self.sleeper = sleeper

    @staticmethod
    def _open_download_directory(target: Path) -> tuple[int, int, str]:
        if not target.is_absolute() or target.name in {"", ".", ".."}:
            raise ValueError("download directory must be an absolute child path")
        parent_fd = os.open(target.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0))
        try:
            entry = os.stat(target.name, dir_fd=parent_fd, follow_symlinks=False)
            directory_fd = os.open(target.name, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
        except Exception:
            os.close(parent_fd)
            raise
        pinned = os.fstat(directory_fd)
        if ((entry.st_dev, entry.st_ino) != (pinned.st_dev, pinned.st_ino)
                or not stat.S_ISDIR(pinned.st_mode) or pinned.st_uid != os.getuid()
                or stat.S_IMODE(pinned.st_mode) != 0o700):
            os.close(directory_fd); os.close(parent_fd)
            raise ValueError("download directory must be user-owned mode 0700")
        return parent_fd, directory_fd, target.name

    @staticmethod
    def _assert_directory_entry(parent_fd: int, name: str, directory_fd: int) -> None:
        pinned = os.fstat(directory_fd)
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if ((pinned.st_dev, pinned.st_ino) != (current.st_dev, current.st_ino)
                or not stat.S_ISDIR(current.st_mode) or current.st_uid != os.getuid()
                or stat.S_IMODE(current.st_mode) != 0o700):
            raise ValueError("download directory changed during verification")

    def query(self, submit_id: str, *, poll_seconds: int = 0, download_dir: str | None = None) -> dict[str, object]:
        if not IDENTIFIER.fullmatch(str(submit_id)): raise ValueError("unsafe submit_id")
        if isinstance(poll_seconds, bool) or not isinstance(poll_seconds, int) or not 0 <= poll_seconds <= 300: raise ValueError("poll_seconds must be between 0 and 300")
        parent_fd = directory_fd = None
        directory_name = None
        target = None
        before: set[str] = set()
        if download_dir:
            target = Path(download_dir)
            parent_fd, directory_fd, directory_name = self._open_download_directory(target)
            before = set(os.listdir(directory_fd))
        try:
            # The CLI has no --poll flag, so poll client-side via the injected
            # sleeper. Only the query is repeated; the run is not resubmitted.
            result = None
            payload: Mapping[str, object] = {}
            status_value: str | None = None
            for attempt in range(poll_seconds + 1):
                result = self.adapter.run(["query_result", "--submit_id", submit_id])
                if isinstance(result.exit_code, bool) or not isinstance(result.exit_code, int) or result.exit_code != 0: raise ValueError("query_result returned nonzero exit code")
                payload = result.payload if isinstance(result.payload, Mapping) else {}
                raw_status = payload.get("gen_status")
                status_value = STATUS_MAP.get(str(raw_status).strip().lower()) if isinstance(raw_status, str) else None
                if status_value is None: raise ValueError("query_result returned unknown external status")
                if status_value != "querying": break
                if attempt < poll_seconds: self.sleeper(1)
            if target is not None and status_value == "success":
                result = self.adapter.run(["query_result", "--submit_id", submit_id, "--download_dir", str(target)])
                if isinstance(result.exit_code, bool) or not isinstance(result.exit_code, int) or result.exit_code != 0: raise ValueError("query_result returned nonzero exit code")
                payload = result.payload if isinstance(result.payload, Mapping) else {}
            payload = redact_value(payload)
            payload = dict(payload); payload["gen_status"] = status_value
            artifacts = self._verified_artifacts(directory_fd, before, Path(download_dir), parent_fd, directory_name) if directory_fd is not None else []
            return {"submit_id": submit_id, "provenance": "externally-queried", "exit_code": 0,
                    "status": status_value, "result": payload, "artifacts": artifacts}
        finally:
            if directory_fd is not None: os.close(directory_fd)
            if parent_fd is not None: os.close(parent_fd)

    @staticmethod
    def _verified_artifacts(directory_fd: int, before: set[str], target: Path,
                            parent_fd: int, directory_name: str) -> list[dict[str, object]]:
        artifacts = []
        seen_digests: set[str] = set()
        TaskService._assert_directory_entry(parent_fd, directory_name, directory_fd)
        names = sorted(set(os.listdir(directory_fd)) - before)
        TaskService._assert_directory_entry(parent_fd, directory_name, directory_fd)
        for name in names:
            if "/" in name or name in {".", ".."}: raise ValueError("unsafe downloaded artifact name")
            if re.fullmatch(r"\.verified-[a-f0-9]{32}\.tmp", name):
                try: os.unlink(name, dir_fd=directory_fd); os.fsync(directory_fd)
                except FileNotFoundError: pass
                continue
            canonical = re.fullmatch(r"artifact-([a-f0-9]{64})(\.(?:mp4|png|jpg))", name)
            if canonical:
                receipt = TaskService._verify_canonical(directory_fd, name, canonical.group(1), target)
                if receipt["sha256"] not in seen_digests:
                    artifacts.append(receipt); seen_digests.add(str(receipt["sha256"]))
                continue
            descriptor = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=directory_fd)
            try:
                metadata = os.fstat(descriptor)
                if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid() or metadata.st_nlink != 1: raise ValueError("downloaded artifact must be a private regular file")
                published_name, digest_value, size, mime = TaskService._publish_verified_copy(
                    directory_fd, descriptor, metadata)
                after = os.fstat(descriptor)
                current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                stable = ("st_dev", "st_ino", "st_size", "st_uid", "st_nlink", "st_mtime_ns", "st_ctime_ns")
                if any(getattr(metadata, field) != getattr(after, field) or getattr(after, field) != getattr(current, field) for field in stable):
                    raise ValueError("downloaded artifact changed while staging")
                if digest_value in seen_digests:
                    continue
                artifacts.append({"path": str(target / published_name), "mime_type": mime, "size_bytes": size,
                                  "sha256": digest_value, "provenance": "externally-queried"})
                seen_digests.add(digest_value)
            finally: os.close(descriptor)
        TaskService._assert_directory_entry(parent_fd, directory_name, directory_fd)
        return artifacts

    @staticmethod
    def _publish_verified_copy(directory_fd: int, source_fd: int,
                               source_before: os.stat_result) -> tuple[str, str, int, str]:
        """Copy verified bytes to an exclusive temp and no-replace digest name."""
        temporary = f".verified-{secrets.token_hex(16)}.tmp"
        output_fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=directory_fd)
        try:
            os.lseek(source_fd, 0, os.SEEK_SET)
            copied = 0; digest = hashlib.sha256(); prefix = b""
            while True:
                chunk = os.read(source_fd, 1024 * 1024)
                if not chunk: break
                prefix += chunk[:max(0, 16-len(prefix))]
                digest.update(chunk)
                view = memoryview(chunk)
                while view:
                    written = os.write(output_fd, view)
                    if written <= 0: raise OSError("short artifact write")
                    view = view[written:]
                copied += len(chunk)
                if copied > MAX_ARTIFACT_BYTES: raise ValueError("downloaded artifact size is invalid")
            source_after = os.fstat(source_fd)
            stable = ("st_dev", "st_ino", "st_size", "st_uid", "st_nlink", "st_mtime_ns", "st_ctime_ns")
            if copied == 0 or any(getattr(source_before, field) != getattr(source_after, field) for field in stable):
                raise ValueError("artifact changed while staging")
            mime = "image/png" if prefix.startswith(b"\x89PNG\r\n\x1a\n") else "image/jpeg" if prefix.startswith(b"\xff\xd8\xff") else "video/mp4" if len(prefix) >= 12 and prefix[4:8] == b"ftyp" else None
            if mime is None: raise ValueError("downloaded artifact type is unsupported")
            digest_value = digest.hexdigest()
            extension = {"video/mp4": ".mp4", "image/png": ".png", "image/jpeg": ".jpg"}[mime]
            final_name = f"artifact-{digest_value}{extension}"
            os.fsync(output_fd)
            os.fchmod(output_fd, 0o400)
            staged = os.fstat(output_fd)
            if staged.st_size != copied or stat.S_IMODE(staged.st_mode) != 0o400:
                raise ValueError("staged artifact verification failed")
            linked = True
            try:
                os.link(temporary, final_name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd, follow_symlinks=False)
            except FileExistsError:
                linked = False
                TaskService._verify_canonical(directory_fd, final_name, digest_value, Path("."))
            os.fsync(directory_fd)
            final = os.stat(final_name, dir_fd=directory_fd, follow_symlinks=False)
            if linked and (final.st_dev, final.st_ino, final.st_size) != (staged.st_dev, staged.st_ino, copied):
                raise ValueError("published artifact identity mismatch")
            return final_name, digest_value, copied, mime
        finally:
            os.close(output_fd)
            try: os.unlink(temporary, dir_fd=directory_fd); os.fsync(directory_fd)
            except FileNotFoundError: pass

    @staticmethod
    def _verify_canonical(directory_fd: int, name: str, expected_digest: str,
                          target: Path) -> dict[str, object]:
        descriptor = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=directory_fd)
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid() or before.st_nlink != 1 or stat.S_IMODE(before.st_mode) != 0o400:
                raise ValueError("content-addressed artifact collision")
            digest = hashlib.sha256(); size = 0; prefix = b""
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk: break
                prefix += chunk[:max(0, 16-len(prefix))]; digest.update(chunk); size += len(chunk)
                if size > MAX_ARTIFACT_BYTES: raise ValueError("content-addressed artifact collision")
            after = os.fstat(descriptor); current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if digest.hexdigest() != expected_digest or size == 0 or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) or (after.st_dev, after.st_ino) != (current.st_dev, current.st_ino):
                raise ValueError("content-addressed artifact collision")
            mime = "image/png" if prefix.startswith(b"\x89PNG") else "image/jpeg" if prefix.startswith(b"\xff\xd8\xff") else "video/mp4" if len(prefix) >= 12 and prefix[4:8] == b"ftyp" else None
            if mime is None: raise ValueError("content-addressed artifact collision")
            expected_extension = {"video/mp4": ".mp4", "image/png": ".png", "image/jpeg": ".jpg"}[mime]
            if not name.endswith(expected_extension):
                raise ValueError("content-addressed artifact collision")
            return {"path": str(target / name), "mime_type": mime, "size_bytes": size,
                    "sha256": expected_digest, "provenance": "externally-queried"}
        finally: os.close(descriptor)

    def verify_download_dir(self, download_dir: str) -> list[dict[str, object]]:
        """Reconcile artifacts left after a crash at the download boundary."""
        target = Path(download_dir)
        parent_fd, descriptor, name = self._open_download_directory(target)
        try: return self._verified_artifacts(descriptor, set(), target, parent_fd, name)
        finally: os.close(descriptor); os.close(parent_fd)

    def list_tasks(self, filters: Mapping[str, object], *, limit: int = 20) -> dict[str, object]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100: raise ValueError("limit must be between 1 and 100")
        unknown = set(filters) - FILTERS
        if unknown: raise ValueError(f"unsupported task filters: {sorted(unknown)}")
        argv = ["list_task"]
        for key in ("gen_status", "aigc_type", "session"):
            if key in filters: argv += [f"--{key}", str(filters[key])]
        argv += ["--limit", str(limit)]; result = self.adapter.run(argv)
        if result.exit_code != 0: raise ValueError("list_task returned nonzero exit code")
        return {"exit_code": result.exit_code, "result": redact_value(result.payload if isinstance(result.payload, Mapping) else {})}
