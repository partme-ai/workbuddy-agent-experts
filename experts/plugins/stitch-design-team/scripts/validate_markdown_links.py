#!/usr/bin/env python3
"""Validate repository-local inline Markdown links."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REMOTE_PREFIXES = ("http://", "https://", "mailto:", "codex://", "app://", "#")
SKIPPED_DIRECTORIES = {".git", ".pytest_cache", "__pycache__", "node_modules"}


def _target(raw_target: str) -> str:
    value = raw_target.strip()
    if value.startswith("<") and ">" in value:
        return value[1 : value.index(">")]
    return value.split(maxsplit=1)[0]


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    root = root.resolve()
    for markdown in sorted(root.rglob("*.md")):
        if any(part in SKIPPED_DIRECTORIES for part in markdown.relative_to(root).parts):
            continue
        fence: str | None = None
        for line_number, line in enumerate(markdown.read_text(encoding="utf-8").splitlines(), 1):
            fence_match = re.match(r"^[ \t]*(`{3,}|~{3,})", line)
            if fence_match:
                marker = fence_match.group(1)[0]
                fence = None if fence == marker else marker
                continue
            if fence is not None:
                continue
            for match in LINK_PATTERN.finditer(line):
                target = _target(match.group(1))
                if not target or target.startswith(REMOTE_PREFIXES):
                    continue
                local = unquote(target.split("#", 1)[0].split("?", 1)[0])
                if not local:
                    continue
                resolved = (markdown.parent / local).resolve()
                try:
                    resolved.relative_to(root)
                except ValueError:
                    errors.append(f"{markdown.relative_to(root)}:{line_number}: link escapes repository: {target}")
                    continue
                if not resolved.exists():
                    errors.append(f"{markdown.relative_to(root)}:{line_number}: missing link target: {target}")
    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    errors = validate(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("validated repository-local Markdown links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
