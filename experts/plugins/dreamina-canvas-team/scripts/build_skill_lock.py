#!/usr/bin/env python3
"""Generate upstream/dreamina-skills.lock.json from the local upstream snapshot.

Records the upstream commit SHA and the SHA-256 of every file under each
declared dreamina-canvas-* Skill directory. The verify script consumes
this lock to enforce byte parity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

DOWNSTREAM_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = DOWNSTREAM_ROOT / "upstream" / "dreamina-skills.lock.json"

CANVAS_SKILLS = [
    "dreamina-canvas-cli",
    "dreamina-canvas-auth",
    "dreamina-canvas-discover-models",
    "dreamina-canvas-create",
    "dreamina-canvas-compose",
    "dreamina-canvas-generate-image",
    "dreamina-canvas-generate-video",
    "dreamina-canvas-generate-audio",
    "dreamina-canvas-manage-timeline",
    "dreamina-canvas-quote-and-run",
    "dreamina-canvas-resume-operation",
    "dreamina-canvas-download-assets",
    "dreamina-canvas-use",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def git(upstream_repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=upstream_repo).decode().strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--upstream-path",
        required=True,
        help="Checked-out dreamina-skills repository at the commit to lock",
    )
    parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    args = parser.parse_args()
    upstream_repo = Path(args.upstream_path).resolve()
    lock_path = Path(args.lock).resolve()
    if not (upstream_repo / ".git").exists():
        # Linked worktrees use a .git file; normal repositories use a directory.
        print(f"FAIL: not a Git checkout: {upstream_repo}", file=sys.stderr)
        sys.exit(1)
    commit = git(upstream_repo, "rev-parse", "HEAD")
    if len(commit) != 40 or any(ch not in "0123456789abcdef" for ch in commit):
        print(f"FAIL: upstream HEAD is not a canonical commit SHA: {commit}", file=sys.stderr)
        sys.exit(1)
    skills: dict[str, dict[str, str]] = {}
    for name in CANVAS_SKILLS:
        skill_dir = upstream_repo / "skills" / name
        if not skill_dir.is_dir():
            print(f"FAIL: missing skill dir: {skill_dir}", file=sys.stderr)
            sys.exit(1)
        files: dict[str, str] = {}
        for path in sorted(skill_dir.rglob("*")):
            if path.is_file():
                rel = path.relative_to(skill_dir).as_posix()
                files[rel] = sha256_file(path)
        skills[name] = files

    lock = {
        "schemaVersion": "1.0",
        "repository": "https://github.com/full-aigc-skills/dreamina-skills",
        "commit": commit,
        "skills": skills,
        "sourceContract": "verification/dreamina-canvas-guide-contract.json",
        "suiteReport": "verification/dreamina-canvas-skill-suite.json",
    }
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"OK: wrote {lock_path} (commit {commit[:12]}, {sum(len(v) for v in skills.values())} files)")


if __name__ == "__main__":
    main()
