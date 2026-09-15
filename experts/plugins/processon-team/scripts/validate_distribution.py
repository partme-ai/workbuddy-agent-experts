#!/usr/bin/env python3
"""Validate the complete Codex ProcessOn plugin distribution."""

from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAMES = (
    "processon-use",
    "processon-setup",
    "processon-diagram",
    "processon-mindmap",
    "processon-infographic",
    "processon-prompt",
    "processon-review",
)
REQUIRED_FILES = (
    ".codex-plugin/plugin.json",
    ".mcp.json",
    ".agents/plugins/marketplace.json",
    "assets/logo.svg",
    "assets/logo-light.png",
    "assets/logo.png",
    "assets/logo-dark.png",
    "assets/composer-icon.png",
    "assets/setup/index.html",
    "assets/setup/styles.css",
    "assets/setup/app.js",
    "processon_harness/__init__.py",
    "processon_harness/secrets.py",
    "processon_harness/mcp_proxy.py",
    "processon_harness/setup_trigger.py",
    "scripts/processon_mcp_proxy.py",
    "scripts/processon_setup.py",
    "README.md",
    "README.zh-CN.md",
    "docs/ProcessOn-Documentation-Index.zh_CN.md",
    "docs/Codex-ProcessOn-Plugin-Architecture.md",
    "docs/Codex-ProcessOn-Plugin-Architecture.zh_CN.md",
    "docs/Codex-ProcessOn-Plugin-Technical-Solution.md",
    "docs/Codex-ProcessOn-Plugin-Technical-Solution.zh_CN.md",
    "PRIVACY.md",
    "TERMS.md",
    "LICENSE",
    "NOTICE",
    "THIRD_PARTY_NOTICES.md",
)
PLACEHOLDER_PATTERN = re.compile(r"\b(?:TBD|TODO|FIXME|PLACEHOLDER)\b")
REAL_BEARER_PATTERN = re.compile(
    r"Bearer\s+(?!<|TOKEN_VALUE|test-secret-value)[A-Za-z0-9+/=_-]{20,}"
)


def _load_json(path: Path, errors: list[str]) -> dict:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON: {path.name}: {type(exc).__name__}")
        return {}
    if not isinstance(payload, dict):
        errors.append(f"JSON root must be an object: {path.name}")
        return {}
    return payload


def _png_size(path: Path) -> tuple[int, int] | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) < 24:
        return None
    return struct.unpack(">II", data[16:24])


def _validate_skill(path: Path, expected_name: str, errors: list[str]) -> None:
    try:
        text = path.read_text()
    except OSError:
        return
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        errors.append(f"invalid Skill frontmatter: {path.parent.name}")
        return
    frontmatter = text.split("---\n", 2)[1]
    try:
        metadata = yaml.safe_load(frontmatter)
    except yaml.YAMLError:
        errors.append(f"invalid Skill YAML: {path.parent.name}")
        return
    if not isinstance(metadata, dict) or metadata.get("name") != expected_name:
        errors.append(f"Skill name mismatch: {path.parent.name}")
    if not metadata.get("description"):
        errors.append(f"Skill description missing: {path.parent.name}")


def _scan_text_files(root: Path, errors: list[str]) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or ".venv" in path.parts:
            continue
        if path.suffix.lower() in {".png", ".pyc"}:
            continue
        try:
            text = path.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        relative = path.relative_to(root)
        if REAL_BEARER_PATTERN.search(text):
            errors.append(f"literal bearer credential: {relative}")
        if (
            relative.suffix.lower() in {".md", ".json"}
            and "docs/superpowers" not in relative.as_posix()
            and PLACEHOLDER_PATTERN.search(text)
        ):
            errors.append(f"unfinished placeholder: {relative}")


def validate_distribution(root: Path = ROOT) -> list[str]:
    """Return actionable distribution errors; an empty list means valid."""
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")
    for name in SKILL_NAMES:
        skill_path = root / "skills" / name / "SKILL.md"
        if not skill_path.is_file():
            errors.append(f"missing required file: skills/{name}/SKILL.md")
        else:
            _validate_skill(skill_path, name, errors)

    managed = set(SKILL_NAMES)
    skills_dir = root / "skills"
    if skills_dir.is_dir():
        for child in sorted(skills_dir.iterdir()):
            if child.is_dir() and child.name not in managed:
                errors.append(
                    f"unmanaged skill directory: skills/{child.name} "
                    "(skill bodies are vendored; add them to the source package)"
                )

    plugin_path = root / ".codex-plugin/plugin.json"
    mcp_path = root / ".mcp.json"
    marketplace_path = root / ".agents/plugins/marketplace.json"
    plugin = _load_json(plugin_path, errors) if plugin_path.is_file() else {}
    mcp = _load_json(mcp_path, errors) if mcp_path.is_file() else {}
    marketplace = _load_json(marketplace_path, errors) if marketplace_path.is_file() else {}

    if plugin:
        if plugin.get("name") != "codex-processon-plugin":
            errors.append("plugin name must be codex-processon-plugin")
        for key in ("composerIcon", "logo", "logoDark"):
            value = plugin.get("interface", {}).get(key)
            if not isinstance(value, str) or not (root / value.removeprefix("./")).is_file():
                errors.append(f"invalid manifest asset reference: {key}")
    if mcp:
        server = mcp.get("mcpServers", {}).get("processon", {})
        expected_server = {
            "type": "stdio",
            "command": "python3",
            "args": ["scripts/processon_mcp_proxy.py"],
            "cwd": ".",
        }
        if server != expected_server:
            errors.append("ProcessOn MCP must use the local secret-free stdio proxy")
    if marketplace:
        entries = marketplace.get("plugins", [])
        if len(entries) != 1 or entries[0].get("name") != "codex-processon-plugin":
            errors.append("marketplace must contain exactly the ProcessOn plugin")

    expected_pngs = {
        "assets/logo-light.png": (873, 250),
        "assets/logo.png": (873, 250),
        "assets/logo-dark.png": (873, 250),
        "assets/composer-icon.png": (64, 64),
    }
    for relative, expected in expected_pngs.items():
        path = root / relative
        if path.is_file() and _png_size(path) != expected:
            errors.append(f"invalid PNG dimensions: {relative}")

    _scan_text_files(root, errors)
    return errors


def main() -> int:
    errors = validate_distribution()
    if errors:
        print("Distribution validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Distribution validation passed: {ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
