#!/usr/bin/env python3
"""Validate the Codex plugin distribution.

The repository ships two manifests:
  - `plugin.json`                canonical portable manifest
  - `.codex-plugin/plugin.json`  compatibility fallback

Both must agree on identity and interface, the portable one must satisfy the
published schema (required `$schema` + `name`, `additionalProperties: false`
at top level so no top-level `skills` / `interface`), and every declared
component must actually exist.
"""

from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PORTABLE_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
PORTABLE_TOP_LEVEL_FIELDS = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}
IDENTITY_FIELDS = (
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
)
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
    if manifest.get("version") != "0.1.2":
        errors.append("plugin version must be 0.1.2")
    if manifest.get("skills") != "./skills/":
        errors.append("manifest skills path must be ./skills/")
    if "mcpServers" in manifest or (root / ".mcp.json").exists():
        errors.append("MCP configuration is forbidden until an MCP server exists")
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

    # --- portable manifest (canonical) -----------------------------------
    portable_path = root / "plugin.json"
    if not portable_path.is_file():
        errors.append("missing canonical portable manifest: plugin.json")
    else:
        portable = load_json(portable_path)
        allowed = PORTABLE_TOP_LEVEL_FIELDS
        unknown = sorted(set(portable) - allowed)
        if unknown:
            errors.append(
                f"portable plugin.json has fields outside the published schema: {unknown}"
            )
        if portable.get("$schema") != PORTABLE_SCHEMA:
            errors.append(f"portable plugin.json $schema must be {PORTABLE_SCHEMA}")
        if portable.get("name") != plugin_id:
            errors.append("portable plugin.json name must match the compat manifest")
        author = portable.get("author", {})
        unknown_author = sorted(set(author) - {"name", "email", "url"})
        if unknown_author:
            errors.append(f"portable author has unsupported fields: {unknown_author}")
        # additionalProperties:false means these must NOT be top-level here
        for forbidden in ("skills", "interface", "mcpServers", "apps"):
            if forbidden in portable:
                errors.append(
                    f"portable plugin.json must not declare top-level `{forbidden}`"
                )
        extension = (portable.get("extensions") or {}).get("com.openai") or {}
        portable_interface = extension.get("interface")
        if not isinstance(portable_interface, dict):
            errors.append("portable manifest must declare extensions.com.openai.interface")
        else:
            if set(portable_interface) != set(interface):
                errors.append("portable and compat interface field sets differ")
            for field, value in interface.items():
                if portable_interface.get(field) != value:
                    errors.append(f"interface parity mismatch on `{field}`")
        for field in IDENTITY_FIELDS:
            if portable.get(field) != manifest.get(field):
                errors.append(f"identity parity mismatch on `{field}`")

    # This plugin ships no MCP servers and no apps. Declaring either without
    # its companion file would be an untruthful claim.
    if (root / "mcp.json").exists() or (root / ".mcp.json").exists():
        errors.append("MCP configuration is forbidden until an MCP server exists")
    if (root / ".app.json").exists() or (root / "app.json").exists():
        errors.append("app configuration is forbidden until an app exists")

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
    print(
        f"validated {manifest['name']} {manifest['version']} "
        "(portable + compatibility manifests, identity parity confirmed)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
