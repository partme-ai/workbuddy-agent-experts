#!/usr/bin/env python3
"""Verify that packaged Skills match upstream/dreamina-skills.lock.json.

Reads upstream/dreamina-skills.lock.json and re-hashes every file under
skills/dreamina-canvas-*/. Returns exit 0 iff every packaged file's
SHA-256 equals the locked value.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "upstream" / "dreamina-skills.lock.json"
SKILLS = ROOT / "skills"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    if not LOCK.is_file():
        print(f"FAIL: missing lock file: {LOCK}", file=sys.stderr)
        sys.exit(1)
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    declared = set(lock["skills"].keys())
    actual = {
        p.name
        for p in SKILLS.iterdir()
        if p.is_dir() and p.name.startswith("dreamina-canvas-")
    }
    missing = declared - actual
    extra = actual - declared
    if missing or extra:
        print(
            f"FAIL: skill set mismatch missing={sorted(missing)} extra={sorted(extra)}",
            file=sys.stderr,
        )
        sys.exit(1)
    failures: list[str] = []
    for name in sorted(declared):
        expected = lock["skills"][name]
        skill_dir = SKILLS / name
        seen: set[str] = set()
        for relpath, expected_sha in expected.items():
            file_path = skill_dir / relpath
            if not file_path.is_file():
                failures.append(f"{name}: missing file {relpath}")
                continue
            actual_sha = sha256_file(file_path)
            if actual_sha != expected_sha:
                failures.append(
                    f"{name}: hash mismatch on {relpath} "
                    f"(expected {expected_sha[:12]}, got {actual_sha[:12]})"
                )
            seen.add(relpath)
        # Detect extra files in the packaged skill not in the lock
        for path in sorted(skill_dir.rglob("*")):
            if path.is_file():
                rel = path.relative_to(skill_dir).as_posix()
                if rel not in seen:
                    failures.append(f"{name}: undeclared file {rel}")
    if failures:
        for line in failures:
            print(f"FAIL: {line}", file=sys.stderr)
        sys.exit(1)
    print(
        f"OK: {len(declared)} skills, "
        f"{sum(len(v) for v in lock['skills'].values())} files match upstream "
        f"commit {lock['commit'][:12]}"
    )


if __name__ == "__main__":
    main()
