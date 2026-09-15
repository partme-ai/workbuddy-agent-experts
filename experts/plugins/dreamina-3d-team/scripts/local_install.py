#!/usr/bin/env python3
"""Register / install codex-dreamina-3d into a local Codex setup.

Codex discovers locally installed plugins through a *marketplace* file:

    ~/.agents/plugins/marketplace.json      ("personal" marketplace)

Each entry points at a local checkout, and installation is performed by the
Codex CLI, which materialises the plugin under:

    ~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/
    ...and writes [plugins."<plugin>@<marketplace>"] enabled = true
       into ~/.codex/config.toml

So the canonical install is two steps:

    1. register  — add this repository to the personal marketplace
    2. install   — `codex plugin add codex-dreamina-3d@personal`

This script performs step 1 (idempotently) and, when the Codex CLI can be
located, step 2 as well. It never edits ``config.toml`` by hand: the CLI owns
that file, and hand-written entries are not recognised as installed plugins.

Verification after install:

    python3 scripts/local_install.py --verify
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "codex-dreamina-3d"

MARKETPLACE_PATH = Path.home() / ".agents" / "plugins" / "marketplace.json"
MARKETPLACE_NAME = "personal"

# Codex ships inside the ChatGPT desktop app on macOS.
CLI_CANDIDATES = (
    Path("/Applications/ChatGPT.app/Contents/Resources/codex"),
    Path("/Applications/Codex.app/Contents/Resources/codex"),
)


def find_cli() -> Path | None:
    for candidate in CLI_CANDIDATES:
        if candidate.is_file():
            return candidate
    found = shutil.which("codex")
    return Path(found) if found else None


def relative_to_home(path: Path) -> str:
    """Marketplace paths are written relative to the user's home directory."""
    try:
        return "./" + str(path.resolve().relative_to(Path.home()))
    except ValueError:
        return str(path.resolve())


def bump_cachebuster(plugin_dir: Path, cachebuster: str | None = None) -> str:
    """Apply the Codex local-development cachebuster to the manifest version.

    Implements the documented policy
    (``plugin-creator/references/installing-and-updating.md``):

        <base-version>+codex.<cachebuster>

    The base version is everything before ``+``; an existing cachebuster is
    replaced rather than appended. Returns the new version string.
    """
    from datetime import datetime, timezone

    manifest_path = plugin_dir / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = str(manifest["version"]).split("+", 1)[0]
    token = cachebuster or datetime.now(timezone.utc).strftime("local-%Y%m%d-%H%M%S")
    version = f"{base}+codex.{token}"
    manifest["version"] = version
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return version


def read_marketplace() -> dict:
    if not MARKETPLACE_PATH.is_file():
        return {
            "name": MARKETPLACE_NAME,
            "interface": {"displayName": "Personal"},
            "plugins": [],
        }
    return json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))


def entry_for(plugin_dir: Path, policy: str) -> dict:
    return {
        "name": PLUGIN_NAME,
        "source": {"source": "local", "path": relative_to_home(plugin_dir)},
        "policy": {"installation": "AVAILABLE", "authentication": policy},
        "category": "Creativity",
    }


def register(
    *, plugin_dir: Path = PLUGIN_DIR, policy: str = "ON_INSTALL", dry_run: bool = False
) -> dict:
    data = read_marketplace()
    entries = data.setdefault("plugins", [])
    existing = next((e for e in entries if e.get("name") == PLUGIN_NAME), None)
    desired = entry_for(plugin_dir, policy)

    if existing == desired:
        return {"marketplace": str(MARKETPLACE_PATH), "changed": False, "entry": desired}

    if dry_run:
        return {"marketplace": str(MARKETPLACE_PATH), "changed": True, "entry": desired, "dry_run": True}

    if existing is not None:
        entries[entries.index(existing)] = desired
    else:
        entries.append(desired)

    MARKETPLACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKETPLACE_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return {"marketplace": str(MARKETPLACE_PATH), "changed": True, "entry": desired}


def install_via_cli(cli: Path, marketplace: str = MARKETPLACE_NAME) -> tuple[int, str]:
    proc = subprocess.run(
        [str(cli), "plugin", "add", f"{PLUGIN_NAME}@{marketplace}"],
        capture_output=True, text=True, timeout=300,
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def list_plugins(cli: Path) -> str:
    proc = subprocess.run(
        [str(cli), "plugin", "list"], capture_output=True, text=True, timeout=120
    )
    return proc.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--plugin-dir", default=str(PLUGIN_DIR))
    parser.add_argument("--policy", default="ON_INSTALL", choices=["ON_INSTALL", "ON_USE"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--register-only", action="store_true", help="skip the Codex CLI install step")
    parser.add_argument("--verify", action="store_true", help="only report current install status")
    parser.add_argument(
        "--cachebuster",
        nargs="?",
        const="",
        default=None,
        help=(
            "bump the manifest version to <base>+codex.<token> so Codex picks up "
            "local edits (default token: UTC timestamp); omit the flag to leave "
            "the version alone"
        ),
    )
    args = parser.parse_args()

    cli = find_cli()

    if args.verify:
        if cli is None:
            print("Codex CLI not found; cannot verify install status", file=sys.stderr)
            return 1
        out = list_plugins(cli)
        for line in out.splitlines():
            if PLUGIN_NAME in line:
                print(line.strip())
                return 0
        print(f"{PLUGIN_NAME} not listed by Codex CLI", file=sys.stderr)
        return 1

    if args.cachebuster is not None:
        new_version = bump_cachebuster(
            Path(args.plugin_dir), args.cachebuster or None
        )
        print(json.dumps({"cachebuster_version": new_version}, indent=2))

    result = register(plugin_dir=Path(args.plugin_dir), policy=args.policy, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
    if args.dry_run:
        return 0

    if args.register_only or cli is None:
        if cli is None:
            print(
                "\nCodex CLI not found. Run this once Codex is installed:\n"
                f"    codex plugin add {PLUGIN_NAME}@{MARKETPLACE_NAME}",
                file=sys.stderr,
            )
        return 0

    code, output = install_via_cli(cli)
    print(output)
    if code != 0:
        return code

    for line in list_plugins(cli).splitlines():
        if PLUGIN_NAME in line:
            print(f"\nverified: {line.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())