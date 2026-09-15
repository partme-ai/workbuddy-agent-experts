#!/usr/bin/env python3
"""Validate the codex-blender plugin distribution.

This validator is the union of two complementary sets of checks.

**Project policy** (the compatibility-first foundation rules):
  - the required structure, legal files, and brand assets exist
  - brand PNGs have the expected dimensions and alpha channel
  - the plugin name is a codex-prefixed kebab-case identifier
  - `mcpServers` is forbidden while no MCP server exists
  - the marketplace entry pins this repository as a url source on `main`
  - the portable root `plugin.json` / `mcp.json` stay inactive

**Codex manifest rules** (mirroring Codex's own handling in
`codex-rs/plugin/src/plugin_id.rs`, `core-plugins/src/manifest.rs`,
`core-plugins/src/marketplace.rs`):
  - `name` is a valid identifier segment: ASCII letters, digits, `.`, `_`, `-`,
    with no leading/trailing dot and no `..`
  - `skills` entries start with `./`, are never `./`, contain no `..`, and stay
    inside the plugin root
  - every declared skills directory contains `<skill>/SKILL.md` whose frontmatter
    `name` matches its directory name and which carries a `description`
  - `interface.defaultPrompt` carries 1-3 entries of at most 128 characters
  - the marketplace manifest declares a valid `name` and a non-empty `plugins`
    array whose entry name matches the manifest name

A `LICENSE` file is required by project policy.
"""

from __future__ import annotations

import json
import os
import re
import struct
import sys
from pathlib import Path

# --- project policy -------------------------------------------------------

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# Local iteration requires a "+codex.<cachebuster>" build suffix, so the version
# must not be pinned to a bare literal.
VERSION_PATTERN = re.compile(r"^0\.3\.0(?:\+[0-9A-Za-z.-]+)?$")
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
REQUIRED_DIRECTORIES = ("assets", "bin", "skills", "schemas", "scripts", "tests")
EXPECTED_ASSETS = {
    "assets/logo.png": (1024, 1024, 6),
    "assets/logo-dark.png": (1024, 1024, 6),
    "assets/composer-icon.png": (256, 256, 6),
}
REQUIRED_INTERFACE_FIELDS = (
    "displayName", "shortDescription", "longDescription", "developerName",
    "category", "brandColor", "composerIcon", "logo", "logoDark",
)
REPO_URL = "https://github.com/partme-ai/codex-blender-plugin"
EXPECTED_SOURCE = {"source": "url", "url": REPO_URL + ".git", "ref": "main"}
EXPECTED_POLICY = {"installation": "AVAILABLE", "authentication": "ON_USE"}
EXPECTED_SKILLS = (
    "codex-blender-use",
    "codex-blender-inspect",
    "codex-blender-managed",
    "codex-blender-connector",
    "codex-blender-design",
    "codex-blender-preview",
    "codex-blender-export",
    "codex-blender-recover",
    "codex-blender-jimeng-web",
)

SECRET_PATTERNS = (
    re.compile(rb"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"ghp_[A-Za-z0-9]{36}"),
    re.compile(rb"sk-[A-Za-z0-9]{20,}"),
    re.compile(rb"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{8,}"),
)

MAX_BINARY_BYTES = 1024 * 1024
SKIP_DIRS = {".git", ".superpowers", "__pycache__", "node_modules"}
BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mov", ".webm", ".avi",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".zip", ".tar", ".gz",
}
SEGMENT_CHARS = re.compile(r"^[A-Za-z0-9._-]+$")


# --- Codex manifest rules -------------------------------------------------

def validate_segment(value, kind):
    """Mirror validate_plugin_segment(); return an error string or None."""
    if not value:
        return f"invalid {kind}: must not be empty"
    allow_dots = kind == "plugin name"
    if allow_dots and value in (".", ".."):
        return f"invalid {kind}: path traversal is not allowed"
    if allow_dots and (value.startswith(".") or value.endswith(".") or ".." in value):
        return f"invalid {kind}: dots must separate non-empty name segments"
    allowed = (
        "ASCII letters, digits, `.`, `_`, and `-`"
        if allow_dots
        else "ASCII letters, digits, `_`, and `-`"
    )
    if not SEGMENT_CHARS.match(value) or (not allow_dots and "." in value):
        return f"invalid {kind}: only {allowed} are allowed"
    return None


def validate_manifest_path(field, raw):
    """Mirror resolve_manifest_path(); return (relative, error)."""
    if not raw:
        return None, f"{field}: path must not be empty"
    if not raw.startswith("./"):
        return None, f"{field}: path must start with `./` relative to plugin root"
    relative = raw[2:]
    if not relative:
        return None, f"{field}: path must not be `./`"
    if any(component == ".." for component in relative.split("/")):
        return None, f"{field}: path must not contain '..'"
    if relative.startswith("/"):
        return None, f"{field}: path must stay within the plugin root"
    return relative, None


def _skill_frontmatter(path):
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fields = {}
    for line in text[3:end].splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip("\"'")
    return fields


def png_shape(target: Path):
    data = target.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    width, height = struct.unpack(">II", data[16:24])
    return width, height, data[25]


# --- validation -----------------------------------------------------------

def _validate_skills(root, manifest, errors):
    declared = manifest.get("skills")
    if declared is None:
        return
    paths = [declared] if isinstance(declared, str) else declared
    if not isinstance(paths, list) or not paths:
        errors.append("skills must be a path string or a non-empty list of paths")
        return
    for raw in paths:
        relative, path_error = validate_manifest_path("skills", raw)
        if path_error:
            errors.append(path_error)
            continue
        skills_dir = root / relative
        if not skills_dir.is_dir():
            errors.append(f"skills directory does not exist: {raw}")
            continue
        for entry in sorted(os.listdir(skills_dir)):
            skill_md = skills_dir / entry / "SKILL.md"
            if not skill_md.is_file():
                errors.append(f"skills/{entry} has no SKILL.md")
                continue
            front = _skill_frontmatter(skill_md)
            if front is None:
                errors.append(f"skills/{entry}/SKILL.md has no frontmatter block")
                continue
            if not front.get("name"):
                errors.append(f"skills/{entry}/SKILL.md frontmatter has no name")
            elif front["name"] != entry:
                errors.append(
                    f"skills/{entry}/SKILL.md name {front['name']!r} does not match its directory"
                )
            if not front.get("description"):
                errors.append(f"skills/{entry}/SKILL.md frontmatter has no description")


def _validate_marketplace(root, marketplace, plugin_id, errors):
    market_name = marketplace.get("name", "")
    segment_error = validate_segment(market_name, "marketplace name")
    if segment_error:
        errors.append(f"marketplace name {market_name!r}: {segment_error}")

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        errors.append("marketplace must declare a non-empty `plugins` array")
        return

    for index, entry in enumerate(plugins):
        if not isinstance(entry, dict):
            errors.append(f"marketplace plugins[{index}] is not an object")
            continue
        entry_name = entry.get("name", "")
        error = validate_segment(entry_name, "plugin name")
        if error:
            errors.append(f"marketplace plugins[{index}] name: {error}")
        elif plugin_id and entry_name != plugin_id:
            errors.append(
                f"marketplace plugins[{index}] name {entry_name!r} does not match "
                f"manifest name {plugin_id!r}"
            )
        source = entry.get("source")
        if source is None:
            errors.append(f"marketplace plugins[{index}] has no `source`")
        elif isinstance(source, str):
            if not source:
                errors.append(f"marketplace plugins[{index}] source is empty")
        elif isinstance(source, dict):
            kind = source.get("source")
            if kind == "local":
                raw = source.get("path", "")
                if raw not in (".", "./"):
                    _, path_error = validate_manifest_path(
                        f"plugins[{index}].source.path", raw
                    )
                    if path_error:
                        errors.append(path_error)
                    elif not (root / raw).is_dir():
                        errors.append(f"plugins[{index}].source.path does not exist: {raw}")
            elif kind not in ("url", "git-subdir", "npm", "git"):
                errors.append(
                    f"marketplace plugins[{index}] source kind {kind!r} is not supported"
                )
        else:
            errors.append(f"marketplace plugins[{index}] source has an unsupported shape")

    matching = [
        entry for entry in plugins
        if isinstance(entry, dict) and entry.get("name") == plugin_id
    ]
    if len(matching) != 1:
        errors.append("marketplace must contain exactly one matching plugin")
        return
    if matching[0].get("source") != EXPECTED_SOURCE:
        errors.append("marketplace source does not match repository")
    if matching[0].get("policy") != EXPECTED_POLICY:
        errors.append("marketplace policy mismatch")


def _validate_tree(root, errors):
    for target in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in target.parts):
            continue
        if target.is_symlink():
            errors.append(f"symlink found: {target.relative_to(root)}")
            continue
        if not target.is_file():
            continue
        try:
            size = target.stat().st_size
            data = target.read_bytes()
        except OSError:
            continue
        if size > MAX_BINARY_BYTES and target.suffix.lower() in BINARY_SUFFIXES:
            errors.append(
                f"binary exceeds {MAX_BINARY_BYTES} bytes: "
                f"{target.relative_to(root)} ({size} bytes)"
            )
        if any(pattern.search(data) for pattern in SECRET_PATTERNS):
            errors.append(f"secret-like content detected: {target.relative_to(root)}")


def validate(root: Path) -> list[str]:
    errors: list[str] = []

    manifest_path = root / ".codex-plugin" / "plugin.json"
    marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
    for target in (manifest_path, marketplace_path):
        if not target.is_file():
            errors.append(f"missing {target.relative_to(root)}")
    if errors:
        return errors

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"plugin.json is not valid JSON: {exc}"]
    try:
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"marketplace.json is not valid JSON: {exc}"]

    plugin_id = manifest.get("name", "")

    # -- project policy: identity, version, forbidden MCP --
    if NAME_PATTERN.fullmatch(plugin_id) is None or not plugin_id.startswith("codex-"):
        errors.append("manifest name must be a codex-prefixed kebab-case identifier")
    if VERSION_PATTERN.fullmatch(manifest.get("version") or "") is None:
        errors.append(
            "release version must be 0.3.0, optionally with a +build cachebuster"
        )
    for field in ("description", "skills"):
        if not manifest.get(field):
            errors.append(f"manifest missing required field: {field}")
    if manifest.get("receipt_contract_versions") != ["1.0.0", "2.0.0", "3.0.0"]:
        errors.append("manifest receipt_contract_versions must be ['1.0.0', '2.0.0', '3.0.0']")
    if "mcpServers" in manifest or (root / ".mcp.json").exists():
        errors.append("MCP configuration is forbidden until an MCP server exists")

    # -- Codex rule: the name must also be a valid identifier segment --
    segment_error = validate_segment(plugin_id, "plugin name")
    if segment_error:
        errors.append(f"manifest name {plugin_id!r}: {segment_error}")

    # -- project policy: required interface fields --
    interface = manifest.get("interface", {})
    for field in REQUIRED_INTERFACE_FIELDS:
        if not interface.get(field):
            errors.append(f"missing interface.{field}")
    prompts = interface.get("defaultPrompt", [])
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3:
        errors.append("defaultPrompt must contain 1-3 entries")
    elif any(not isinstance(item, str) or len(item) > 128 for item in prompts):
        errors.append("defaultPrompt entries must be strings of at most 128 characters")

    _validate_skills(root, manifest, errors)

    for skill_name in EXPECTED_SKILLS:
        if not (root / "skills" / skill_name / "SKILL.md").is_file():
            errors.append(f"missing expected Skill: skills/{skill_name}/SKILL.md")

    _validate_marketplace(root, marketplace, plugin_id, errors)

    # -- project policy: structure, legal files, brand assets --
    for directory in REQUIRED_DIRECTORIES:
        if not (root / directory).is_dir():
            errors.append(f"missing directory: {directory}")
    for filename in REQUIRED_FILES:
        if not (root / filename).is_file():
            errors.append(f"missing required file: {filename}")
    adapter = root / "bin" / "blender_adapter"
    if not adapter.is_file() or not os.access(adapter, os.X_OK):
        errors.append("bin/blender_adapter must exist and be executable")
    if (root / "plugin.json").exists() or (root / "mcp.json").exists():
        errors.append(
            "portable manifests must remain inactive during compatibility-first scaffolding"
        )
    for filename, expected in EXPECTED_ASSETS.items():
        try:
            if png_shape(root / filename) != expected:
                errors.append(f"invalid PNG shape or alpha channel: {filename}")
        except (OSError, ValueError):
            errors.append(f"missing or invalid PNG: {filename}")

    # -- tree hygiene --
    _validate_tree(root, errors)

    return errors


def main(root: str | None = None) -> int:
    base = Path(root if root is not None else ".").resolve()
    errors = validate(base)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    manifest = json.loads((base / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    print(f"validated {manifest['name']} compatibility foundation {manifest['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
