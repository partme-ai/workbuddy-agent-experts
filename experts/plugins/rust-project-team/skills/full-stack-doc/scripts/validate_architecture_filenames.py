#!/usr/bin/env python3
"""Validate generated architecture-document filenames."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ARCHITECTURE_FILENAME_RE = re.compile(
    r"^(?P<stem>[^\s/][^\s/]*)-Architecture(?P<locale>\.zh_CN)?\.md$"
)


def validate_filename(path: str | Path) -> str | None:
    """Return an error for a non-conforming architecture filename."""
    name = Path(path).name
    if ARCHITECTURE_FILENAME_RE.fullmatch(name):
        return None
    return (
        f"{name!r}: expected '*-Architecture.md' or "
        "'*-Architecture.zh_CN.md'"
    )


def language_stems(paths: list[str]) -> tuple[set[str], set[str]]:
    """Return the default-language and Chinese filename stems."""
    default_stems: set[str] = set()
    chinese_stems: set[str] = set()
    for path in paths:
        match = ARCHITECTURE_FILENAME_RE.fullmatch(Path(path).name)
        if not match:
            continue
        if match.group("locale"):
            chinese_stems.add(match.group("stem"))
        else:
            default_stems.add(match.group("stem"))
    return default_stems, chinese_stems


def validate_paths(paths: list[str], require_pairs: bool = False) -> list[str]:
    """Validate names and optionally require identical bilingual stems."""
    errors = [error for path in paths if (error := validate_filename(path))]
    if require_pairs and not errors:
        default_stems, chinese_stems = language_stems(paths)
        for stem in sorted(default_stems - chinese_stems):
            errors.append(f"{stem!r}: missing paired '-Architecture.zh_CN.md'")
        for stem in sorted(chinese_stems - default_stems):
            errors.append(f"{stem!r}: missing paired '-Architecture.md'")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate architecture filenames against the full-stack-doc contract."
    )
    parser.add_argument("paths", nargs="+", help="Architecture Markdown paths to validate")
    parser.add_argument(
        "--require-pairs",
        action="store_true",
        help="Require default-language and zh_CN files with identical stems",
    )
    args = parser.parse_args()

    errors = validate_paths(args.paths, require_pairs=args.require_pairs)
    for error in errors:
        print(f"ERROR    {error}")
    print(f"SUMMARY  architecture_files={len(args.paths)} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
