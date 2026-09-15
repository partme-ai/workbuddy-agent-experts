"""Native enrollment and protected storage for the trusted Dreamina CLI."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from scripts.native_approval import NativeApprovalProvider


class TrustedCliError(PermissionError):
    """Trusted CLI enrollment or protected configuration is invalid."""


class TrustedCliStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (Path.home() / ".config" / "codex-dreamina-design" / "trusted-cli.json")

    def enroll(self, cli_path: Path, *, approval_provider=None) -> dict[str, str]:
        candidate = Path(cli_path)
        if not candidate.is_absolute() or candidate.is_symlink() or not candidate.is_file():
            raise TrustedCliError("CLI enrollment requires an absolute regular non-symlink file")
        stat = candidate.stat()
        if stat.st_uid not in {0, os.getuid()} or stat.st_mode & 0o022:
            raise TrustedCliError("CLI enrollment rejected untrusted owner or write permissions")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        digest = hashlib.sha256()
        with os.fdopen(os.open(candidate, flags), "rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        canonical = str(candidate.resolve(strict=True))
        sha256 = digest.hexdigest()
        provider = approval_provider or NativeApprovalProvider()
        provider.confirm_cli_enrollment(path=canonical, owner_uid=stat.st_uid, sha256=sha256)
        payload = {"cli_path": canonical, "cli_sha256": sha256}
        self._atomic_write(payload)
        return payload

    def load(self) -> dict[str, str]:
        if self.path.is_symlink() or not self.path.is_file():
            raise TrustedCliError("trusted CLI is not enrolled")
        stat = self.path.stat()
        if stat.st_uid != os.getuid() or stat.st_mode & 0o077:
            raise TrustedCliError("trusted CLI config must be user-owned mode 0600")
        parent = self.path.parent
        if parent.is_symlink() or parent.stat().st_mode & 0o077:
            raise TrustedCliError("trusted CLI config directory must be private mode 0700")
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if set(payload) != {"cli_path", "cli_sha256"}:
            raise TrustedCliError("trusted CLI config has unexpected fields")
        if re.fullmatch(r"[a-f0-9]{64}", str(payload["cli_sha256"])) is None:
            raise TrustedCliError("trusted CLI digest is invalid")
        return {"cli_path": str(payload["cli_path"]), "cli_sha256": str(payload["cli_sha256"])}

    def _atomic_write(self, payload: dict[str, str]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(self.path.parent, 0o700)
        fd, tmp_name = tempfile.mkstemp(prefix=".trusted-cli.", dir=self.path.parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
            os.chmod(self.path, 0o600)
        except Exception:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
            raise


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Enroll a trusted Dreamina CLI with native confirmation")
    parser.add_argument("cli_path", type=Path)
    args = parser.parse_args()
    result = TrustedCliStore().enroll(args.cli_path)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["TrustedCliError", "TrustedCliStore"]
