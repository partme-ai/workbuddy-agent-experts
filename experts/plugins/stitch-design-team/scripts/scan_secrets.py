#!/usr/bin/env python3
"""Scan repository files for high-confidence secret formats without echoing values."""

from __future__ import annotations

import re
import sys
from pathlib import Path


SECRET_PATTERNS = (
    ("google-api-key", re.compile(b"AI" + rb"za[0-9A-Za-z_-]{20,}")),
    ("private-key", re.compile(b"-----BEGIN " + rb"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github-token", re.compile(b"gh" + rb"[pousr]_[0-9A-Za-z]{36,}")),
    ("aws-access-key", re.compile(b"AK" + rb"IA[0-9A-Z]{16}")),
    ("slack-token", re.compile(b"xo" + rb"x[baprs]-[0-9A-Za-z-]{20,}")),
    ("stripe-live-key", re.compile(b"sk_" + rb"live_[0-9A-Za-z]{20,}")),
)
SKIPPED_DIRECTORIES = {".git", ".pytest_cache", "__pycache__", "node_modules"}
MAX_FILE_SIZE = 5 * 1024 * 1024


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    root = root.resolve()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in SKIPPED_DIRECTORIES for part in relative.parts):
            continue
        try:
            if path.stat().st_size > MAX_FILE_SIZE:
                continue
            data = path.read_bytes()
        except OSError:
            findings.append(f"{relative}: unreadable file")
            continue
        if b"\x00" in data:
            continue
        for rule_name, pattern in SECRET_PATTERNS:
            if pattern.search(data):
                findings.append(f"{relative}: matched {rule_name}")
    return findings


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    findings = scan(root)
    if findings:
        print("\n".join(findings), file=sys.stderr)
        return 1
    print("secret scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
