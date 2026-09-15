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
CI_MATRIX_PATTERN = re.compile(r"(?m)^ {6}matrix:\s*\n((?: {8}[^\n]+\n?)+)")
CI_DEPENDENCY_INSTALLER_PATTERN = re.compile(
    r"(?i)\b(?:"
    r"(?:python(?:3)?\s+-m\s+)?pip(?:3)?\s+install|"
    r"pipx\s+install|uv\s+(?:sync|add)|poetry\s+(?:install|add)|"
    r"(?:conda|mamba)\s+install|npm\s+(?:install|ci)|"
    r"(?:yarn|pnpm|bun)\s+(?:install|add)"
    r")\b"
)
REQUIRED_FILES = (
    ".github/workflows/ci.yml",
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    "NOTICE",
    "PRIVACY.md",
    "TERMS.md",
    "THIRD_PARTY_NOTICES.md",
    "docs/portable-migration.md",
    "docs/verification/offline.md",
    "docs/verification/runtime.md",
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
        errors.append("release version must be 0.1.2")
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

    workflow_path = root / ".github" / "workflows" / "ci.yml"
    if workflow_path.is_file():
        workflow = workflow_path.read_text(encoding="utf-8")
        for required in (
            "ubuntu-latest",
            "macos-latest",
            "windows-latest",
            '"3.11"',
            '"3.13"',
            "python -m compileall -q scripts tests",
            "python -m unittest discover -s tests -v",
            "python scripts/validate_distribution.py .",
            "git diff --check",
        ):
            if required not in workflow:
                errors.append(f"CI workflow missing required contract: {required}")
        matrix_match = CI_MATRIX_PATTERN.search(workflow)
        matrix: dict[str, list[str]] = {}
        if matrix_match is not None:
            for line in matrix_match.group(1).splitlines():
                key, separator, raw_values = line.strip().partition(":")
                if (
                    not separator
                    or not raw_values.strip().startswith("[")
                    or not raw_values.strip().endswith("]")
                ):
                    matrix = {}
                    break
                matrix[key] = [
                    value.strip().strip('"\'')
                    for value in raw_values.strip()[1:-1].split(",")
                    if value.strip()
                ]
        expected_matrix = {
            "os": ["ubuntu-latest", "macos-latest", "windows-latest"],
            "python-version": ["3.11", "3.13"],
        }
        if matrix != expected_matrix:
            errors.append(
                "CI matrix must contain exactly os and python-version with the supported values"
            )
        if CI_DEPENDENCY_INSTALLER_PATTERN.search(workflow):
            errors.append("CI workflow must not install dependencies")

    runtime_evidence_path = root / "docs" / "verification" / "runtime.md"
    if runtime_evidence_path.is_file():
        runtime_evidence = runtime_evidence_path.read_text(encoding="utf-8")
        if "0.1.2" not in runtime_evidence:
            errors.append("runtime evidence must identify release candidate 0.1.2")
        for gate in (
            "remote_ci_matrix",
            "remote_sha_parity",
            "fresh_marketplace_install",
            "fresh_session_no_spend_smoke",
            "paid_canary",
            "usage_limit_evidence",
        ):
            rows = [
                line
                for line in runtime_evidence.splitlines()
                if line.startswith("|") and gate in line
            ]
            status = rows[0].split("|")[2].strip().strip("`") if len(rows) == 1 else ""
            if status not in {"PASS", "FAIL", "NOT_RUN"}:
                errors.append(f"runtime evidence missing explicit status for {gate}")
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
