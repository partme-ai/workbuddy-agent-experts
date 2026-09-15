#!/usr/bin/env python3
"""Validate a compatibility-first Codex plugin foundation."""

from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SECRET_PATTERNS = (
    re.compile(rb"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
REQUIRED_FILES = (
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    "NOTICE",
    "PRIVACY.md",
    "TERMS.md",
    "THIRD_PARTY_NOTICES.md",
    "docs/portable-migration.md",
)
REQUIRED_DIRECTORIES = ("assets", "skills", "schemas", "scripts", "tests")


def load_json(target: Path) -> dict:
    return json.loads(target.read_text(encoding="utf-8"))


def png_shape(target: Path) -> tuple[int, int, int]:
    data = target.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    width, height = struct.unpack(">II", data[16:24])
    return width, height, data[25]


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = root / ".codex-plugin" / "plugin.json"
    marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
    for target in (manifest_path, marketplace_path):
        if not target.is_file():
            errors.append(f"missing {target.relative_to(root)}")
    if errors:
        return errors

    manifest = load_json(manifest_path)
    marketplace = load_json(marketplace_path)
    plugin_id = manifest.get("name", "")
    repository = manifest.get("repository", "")
    if NAME_PATTERN.fullmatch(plugin_id) is None or not plugin_id.startswith("codex-"):
        errors.append("manifest name must be a codex-prefixed kebab-case identifier")
    if re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?", str(manifest.get("version", ""))) is None:
        errors.append("manifest version must be semantic-version shaped")
    if manifest.get("skills") != "./skills/":
        errors.append("manifest skills path must be ./skills/")
    mcp_path = root / ".mcp.json"
    if "mcpServers" in manifest or mcp_path.exists():
        if manifest.get("mcpServers") != "./.mcp.json" or not mcp_path.is_file():
            errors.append("manifest and .mcp.json must declare the same MCP companion")
        else:
            try:
                mcp = load_json(mcp_path)["mcpServers"]["dreamina_design"]
                if mcp.get("default_tools_approval_mode") != "prompt":
                    errors.append("MCP default approval mode must fail closed with prompt")
                tools = mcp.get("tools", {})
                if tools.get("dreamina_capability_snapshot", {}).get("approval_mode") != "approve":
                    errors.append("read-only capability tool must be explicitly approved")
                for paid in ("dreamina_submit_image", "dreamina_submit_video"):
                    if tools.get(paid, {}).get("approval_mode") != "prompt":
                        errors.append(f"paid MCP tool must require prompt approval: {paid}")
                if mcp.get("args") != ["-m", "scripts.dreamina_mcp_server"]:
                    errors.append("MCP server module args mismatch")
                if not (root / "scripts" / "dreamina_mcp_server.py").is_file():
                    errors.append("MCP server module missing")
            except (KeyError, TypeError, json.JSONDecodeError):
                errors.append("invalid dreamina_design MCP configuration")
    interface = manifest.get("interface", {})
    for field in ("displayName", "shortDescription", "longDescription", "developerName", "category", "brandColor", "composerIcon", "logo", "logoDark"):
        if not interface.get(field):
            errors.append(f"missing interface.{field}")
    prompts = interface.get("defaultPrompt", [])
    if not 1 <= len(prompts) <= 3 or any(len(item) > 128 for item in prompts):
        errors.append("defaultPrompt must contain 1-3 entries of at most 128 characters")

    entries = [entry for entry in marketplace.get("plugins", []) if entry.get("name") == plugin_id]
    if len(entries) != 1:
        errors.append("marketplace must contain exactly one matching plugin")
    else:
        expected_source = {"source": "url", "url": repository + ".git", "ref": "main"}
        if entries[0].get("source") != expected_source:
            errors.append("marketplace source does not match repository")
        expected_policy = {"installation": "AVAILABLE", "authentication": "ON_USE"}
        if entries[0].get("policy") != expected_policy:
            errors.append("marketplace policy mismatch")

    for directory in REQUIRED_DIRECTORIES:
        if not (root / directory).is_dir():
            errors.append(f"missing directory: {directory}")
    for filename in REQUIRED_FILES:
        if not (root / filename).is_file():
            errors.append(f"missing required file: {filename}")
    if (root / "plugin.json").exists() or (root / "mcp.json").exists():
        errors.append("portable manifests must remain inactive during compatibility-first scaffolding")

    expected_assets = {
        "assets/logo.png": (1024, 1024, 6),
        "assets/logo-dark.png": (1024, 1024, 6),
        "assets/composer-icon.png": (256, 256, 6),
    }
    for filename, expected in expected_assets.items():
        target = root / filename
        try:
            if png_shape(target) != expected:
                errors.append(f"invalid PNG shape or alpha channel: {filename}")
        except (OSError, ValueError):
            errors.append(f"missing or invalid PNG: {filename}")

    for target in root.rglob("*"):
        if not target.is_file() or ".git" in target.parts:
            continue
        # Test files legitimately embed byte patterns that match the
        # secret detectors (e.g. fixture strings for secret-scan tests).
        if "tests" in target.parts:
            continue
        data = target.read_bytes()
        if any(pattern.search(data) for pattern in SECRET_PATTERNS):
            errors.append(f"secret-like content detected: {target.relative_to(root)}")
    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors = validate(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    manifest = load_json(root / ".codex-plugin" / "plugin.json")
    print(f"validated {manifest['name']} compatibility foundation {manifest['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
