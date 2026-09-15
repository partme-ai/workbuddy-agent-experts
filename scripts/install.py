#!/usr/bin/env python3
"""Install the pre-built experts/ marketplace into WorkBuddy (macOS / Windows / Linux).

Works from the committed, pre-built ``experts/`` tree - no build step, no
sibling repositories, no third-party dependencies (stdlib only).

What it does (non-destructive):
  1. Copies this build's plugins into  <config>/plugins/marketplaces/my-experts/plugins/
     (only replaces plugins this build owns; foreign plugins are preserved).
  2. Merges the marketplace manifest, keeping foreign entries.
  3. Mirrors plugins into  <config>/plugins/cache/my-experts/<name>/<version>/
  4. Writes install records into <config>/plugins/installed_plugins.json
     (key: <name>@my-experts), backing the file up first.
  5. Ensures the my-experts entry in <config>/plugins/known_marketplaces.json.

<config> defaults to ~/.workbuddy and can be overridden with --config-dir or
the WORKBUDDY_HOME environment variable (useful for tests).

Usage:
  python3 scripts/install.py                 # install (source: ./experts)
  python3 scripts/install.py --uninstall     # remove everything this build owns
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = "my-experts"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json_backup(path: Path, payload) -> None:
    if path.is_file():
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak-agent-experts"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def our_plugins(src: Path) -> list[str]:
    manifest = _read_json(src / ".codebuddy-plugin" / "marketplace.json", {})
    names = [entry.get("name") for entry in manifest.get("plugins", [])]
    return [name for name in names if name]


def install(src: Path, config_dir: Path) -> int:
    if not (src / ".codebuddy-plugin" / "marketplace.json").is_file():
        raise SystemExit(f"pre-built marketplace not found: {src} (expected experts/ tree)")
    ours = our_plugins(src)
    if not ours:
        raise SystemExit("manifest lists no plugins; refusing to install")

    market = config_dir / "plugins" / "marketplaces" / MARKETPLACE
    market_plugins = market / "plugins"
    market_plugins.mkdir(parents=True, exist_ok=True)

    # 1. replace only what this build owns
    for name in ours:
        target = market_plugins / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(src / "plugins" / name, target)

    # 2. merge manifest, keep foreign entries
    manifest_path = market / ".codebuddy-plugin" / "marketplace.json"
    foreign = [entry for entry in _read_json(manifest_path, {}).get("plugins", [])
               if entry.get("name") not in set(ours)]
    src_manifest = _read_json(src / ".codebuddy-plugin" / "marketplace.json", {})
    _write_json_backup(manifest_path, {
        "name": MARKETPLACE,
        "description": src_manifest.get("description", f"{MARKETPLACE} marketplace"),
        "plugins": foreign + src_manifest.get("plugins", []),
    })

    # 3. cache mirror + 4. install records
    now = _now()
    ip_path = config_dir / "plugins" / "installed_plugins.json"
    installed = _read_json(ip_path, {"version": 2, "plugins": {}})
    installed.setdefault("plugins", {})
    cache_root = config_dir / "plugins" / "cache" / MARKETPLACE
    for name in ours:
        plugin_json = src / "plugins" / name / ".codebuddy-plugin" / "plugin.json"
        version = _read_json(plugin_json, {}).get("version", "1.0.0")
        cache = cache_root / name / version
        if cache.exists():
            shutil.rmtree(cache)
        cache.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src / "plugins" / name, cache)
        installed["plugins"][f"{name}@{MARKETPLACE}"] = [{
            "scope": "user", "installPath": str(cache), "version": version,
            "installedAt": now, "lastUpdated": now,
        }]
    _write_json_backup(ip_path, installed)

    # 5. ensure marketplace registration entry
    km_path = config_dir / "plugins" / "known_marketplaces.json"
    km = _read_json(km_path, {})
    entry = km.get(MARKETPLACE, {})
    entry.update({
        "manifestName": MARKETPLACE, "type": "directory",
        "source": {"source": "directory", "path": str(market)},
        "installLocation": str(market),
        "description": f"Marketplace from {market}",
        "lastUpdated": now, "autoUpdate": False,
    })
    km[MARKETPLACE] = entry
    _write_json_backup(km_path, km)

    print(f"installed {len(ours)} plugins -> {market}")
    print("restart WorkBuddy (or reopen the expert picker) to load them")
    return 0


def uninstall(src: Path, config_dir: Path) -> int:
    ours = our_plugins(src) if (src / ".codebuddy-plugin" / "marketplace.json").is_file() else []
    if not ours:
        raise SystemExit("cannot determine owned plugins (experts/ tree missing?)")

    market_plugins = config_dir / "plugins" / "marketplaces" / MARKETPLACE / "plugins"
    removed = 0
    for name in ours:
        target = market_plugins / name
        if target.exists():
            shutil.rmtree(target)
            removed += 1

    manifest_path = config_dir / "plugins" / "marketplaces" / MARKETPLACE / ".codebuddy-plugin" / "marketplace.json"
    if manifest_path.is_file():
        manifest = _read_json(manifest_path, {})
        manifest["plugins"] = [e for e in manifest.get("plugins", []) if e.get("name") not in set(ours)]
        _write_json_backup(manifest_path, manifest)

    ip_path = config_dir / "plugins" / "installed_plugins.json"
    installed = _read_json(ip_path, None)
    if installed is not None:
        for name in ours:
            installed.get("plugins", {}).pop(f"{name}@{MARKETPLACE}", None)
        _write_json_backup(ip_path, installed)

    cache_root = config_dir / "plugins" / "cache" / MARKETPLACE
    for name in ours:
        target = cache_root / name
        if target.exists():
            shutil.rmtree(target)

    print(f"uninstalled {removed} plugins from {config_dir}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Install/uninstall the pre-built WorkBuddy expert teams")
    parser.add_argument("--src", default=str(ROOT / "experts"), help="pre-built marketplace tree (default: ./experts)")
    parser.add_argument("--config-dir", default=None,
                        help="WorkBuddy config dir (default: ~/.workbuddy, or $WORKBUDDY_HOME)")
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args(argv)
    config_dir = Path(args.config_dir or __import__("os").environ.get("WORKBUDDY_HOME")
                      or Path.home() / ".workbuddy").expanduser().resolve()
    src = Path(args.src).resolve()
    if args.uninstall:
        return uninstall(src, config_dir)
    return install(src, config_dir)


if __name__ == "__main__":
    raise SystemExit(main())
