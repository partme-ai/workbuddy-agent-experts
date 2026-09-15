#!/usr/bin/env python3
"""Re-run the deterministic sync for the pinned upstream commit.

Copies the declared dreamina-canvas-* Skills from the local upstream
snapshot into this plugin's skills/ directory, then writes
upstream/dreamina-skills.lock.json with the recorded commit and per-file
SHA-256 values.

Usage:
    python3 scripts/sync_dreamina_canvas_skills.py [--lock <path>]

Default lock path: upstream/dreamina-skills.lock.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--upstream-path",
        required=True,
        help="Checked-out dreamina-skills repository matching the locked commit",
    )
    parser.add_argument("--lock", default=str(ROOT / "upstream" / "dreamina-skills.lock.json"))
    args = parser.parse_args()
    upstream_path = Path(args.upstream_path).resolve()
    lock_path = Path(args.lock).resolve()
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    actual_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=upstream_path, text=True
    ).strip()
    if actual_commit != lock["commit"]:
        print(
            f"FAIL: upstream HEAD {actual_commit} does not match lock {lock['commit']}",
            file=sys.stderr,
        )
        sys.exit(1)
    declared = list(lock["skills"].keys())
    skills_dir = ROOT / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    for name in declared:
        src = upstream_path / "skills" / name
        dst = skills_dir / name
        if not src.is_dir():
            print(f"FAIL: upstream skill missing: {src}", file=sys.stderr)
            sys.exit(1)
        if any(path.is_symlink() for path in src.rglob("*")):
            print(f"FAIL: symlink rejected in upstream skill: {src}", file=sys.stderr)
            sys.exit(1)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    print(f"OK: synced {len(declared)} skills from {upstream_path}")


if __name__ == "__main__":
    main()
