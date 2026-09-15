"""Bind a live Dreamina capability snapshot to the enrolled CLI inode."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any

from scripts.dreamina_adapter import DreaminaAdapter
from scripts.json_contracts import canonical_fingerprint, validate_contract
from scripts.trusted_cli import TrustedCliError, TrustedCliStore


class TrustedCapabilityProvider:
    """Capture read-only capabilities from the exact enrolled CLI bytes."""

    def __init__(self, trusted_cli: TrustedCliStore) -> None:
        self._trusted_cli = trusted_cli

    def capture(self) -> dict[str, Any]:
        enrollment = self._trusted_cli.load()
        path = Path(enrollment["cli_path"])
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(path, flags)
        except OSError as exc:
            raise TrustedCliError("enrolled CLI cannot be opened safely") from exc
        adapter = None
        private_root = None
        try:
            metadata = os.fstat(fd)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid not in {0, os.getuid()} or stat.S_IMODE(metadata.st_mode) & 0o022:
                raise TrustedCliError("enrolled CLI identity is unsafe")
            digest = hashlib.sha256()
            while chunk := os.read(fd, 1024 * 1024):
                digest.update(chunk)
            after_read = os.fstat(fd)
            identity = lambda value: (value.st_dev, value.st_ino, value.st_size, stat.S_IMODE(value.st_mode), value.st_uid, value.st_mtime_ns)
            if identity(after_read) != identity(metadata):
                raise TrustedCliError("enrolled CLI changed while hashing")
            sha256 = digest.hexdigest()
            if sha256 != enrollment["cli_sha256"]:
                raise TrustedCliError("enrolled CLI digest changed")
            os.lseek(fd, 0, os.SEEK_SET)
            private_root = Path(tempfile.mkdtemp(prefix="dreamina-capability-"))
            os.chmod(private_root, 0o700)
            staged = private_root / "dreamina"
            staged_fd = os.open(staged, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o500)
            try:
                while chunk := os.read(fd, 1024 * 1024):
                    remaining = memoryview(chunk)
                    while remaining:
                        written = os.write(staged_fd, remaining)
                        if written <= 0:
                            raise TrustedCliError("enrolled CLI staging write failed")
                        remaining = remaining[written:]
                os.fsync(staged_fd)
                os.fchmod(staged_fd, 0o500)
            finally:
                os.close(staged_fd)

            adapter = DreaminaAdapter(cli_command=str(staged), trusted_binary_sha256=sha256)
            snapshot = adapter.capability_snapshot()
            try:
                snapshot = json.loads(json.dumps(snapshot, sort_keys=True, ensure_ascii=False, allow_nan=False))
            except (TypeError, ValueError) as exc:
                raise TrustedCliError("capability snapshot is not canonical JSON") from exc
            validate_contract(snapshot, "capability_snapshot.schema.json")
            try:
                path_metadata = os.stat(path, follow_symlinks=False)
            except OSError as exc:
                raise TrustedCliError("enrolled CLI path changed during capture") from exc
            if identity(path_metadata) != identity(metadata):
                raise TrustedCliError("enrolled CLI path changed during capture")
        finally:
            if adapter is not None:
                adapter.close()
            if private_root is not None:
                shutil.rmtree(private_root, ignore_errors=True)
            os.close(fd)
        return {
            "snapshot": snapshot,
            "identity_receipt": {
                "cli_path": str(path.resolve(strict=True)), "cli_sha256": sha256,
                "device": metadata.st_dev, "inode": metadata.st_ino, "size_bytes": metadata.st_size,
                "mode": stat.S_IMODE(metadata.st_mode), "owner_uid": metadata.st_uid,
                "cli_version": snapshot["cli_version"], "cli_commit": snapshot.get("cli_commit"),
                "captured_at": snapshot["captured_at"],
                "snapshot_fingerprint": canonical_fingerprint(snapshot),
            },
        }


__all__ = ["TrustedCapabilityProvider"]
