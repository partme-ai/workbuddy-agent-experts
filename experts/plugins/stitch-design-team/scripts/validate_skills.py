#!/usr/bin/env python3
"""Validate every repository Skill without workstation-specific dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata"}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_PATTERN = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)
MAX_SKILL_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return ["SKILL.md is missing"]
    content = skill_file.read_text(encoding="utf-8")
    frontmatter_match = FRONTMATTER_PATTERN.match(content)
    if frontmatter_match is None:
        return ["invalid or missing YAML frontmatter"]

    try:
        values = yaml.safe_load(frontmatter_match.group(1))
    except yaml.YAMLError:
        return ["invalid YAML frontmatter"]
    if not isinstance(values, dict):
        return ["YAML frontmatter must be a mapping"]

    for key in sorted(set(values) - ALLOWED_KEYS):
        errors.append(f"unexpected frontmatter key: {key}")
    for key in ("name", "description"):
        if key not in values:
            errors.append(f"missing frontmatter key: {key}")

    name = values.get("name", "")
    description = values.get("description", "")
    if not isinstance(name, str):
        errors.append("name must be a string")
        name = ""
    if not isinstance(description, str):
        errors.append("description must be a string")
        description = ""
    name = name.strip()
    description = description.strip()
    if not name or NAME_PATTERN.fullmatch(name) is None:
        errors.append("name must use lowercase hyphen-case")
    if len(name) > MAX_SKILL_NAME_LENGTH:
        errors.append(f"name exceeds {MAX_SKILL_NAME_LENGTH} characters")
    if name != skill_dir.name:
        errors.append(f"name {name!r} does not match directory {skill_dir.name!r}")
    if not description:
        errors.append("description must not be empty")
    if len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(f"description exceeds {MAX_DESCRIPTION_LENGTH} characters")
    if "<" in description or ">" in description:
        errors.append("description must not contain angle brackets")
    if description.startswith("[TODO:"):
        errors.append("description contains an unfinished TODO")

    fence_marker: tuple[str, int] | None = None
    for line in content[frontmatter_match.end() :].splitlines():
        fence = re.match(r"^[ \t]*(?:(?:[-+*]|\d+[.)])[ \t]+)?(`{3,}|~{3,})(.*)$", line)
        if fence:
            marker = fence.group(1)
            if fence_marker is None:
                fence_marker = (marker[0], len(marker))
            elif marker[0] == fence_marker[0] and len(marker) >= fence_marker[1] and not fence.group(2).strip():
                fence_marker = None
            continue
        if fence_marker is None and re.fullmatch(r"[ ]{0,3}\[TODO:[^\n]*\][ \t]*", line):
            errors.append("body contains an unfinished TODO")
    if fence_marker is not None:
        errors.append("body contains an unclosed code fence")
    return errors


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    skill_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    for skill_dir in skill_dirs:
        for error in validate_skill(skill_dir):
            errors.append(f"{skill_dir.name}: {error}")
    if not skill_dirs:
        errors.append("no Skill directories found")
    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "skills").resolve()
    errors = validate(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    count = sum(1 for path in root.iterdir() if path.is_dir())
    print(f"validated {count} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
