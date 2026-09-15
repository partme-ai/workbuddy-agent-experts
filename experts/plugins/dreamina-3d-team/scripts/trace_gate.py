#!/usr/bin/env python3
"""Repository-owned deterministic TRACE behavior gate."""

from __future__ import annotations

import json
import re
from pathlib import Path


DIMENSIONS = ("T", "R", "A", "C", "E")


def evaluate_skill(skill_dir: Path) -> dict[str, object]:
    path = skill_dir / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if match is None:
        raise ValueError(f"missing YAML frontmatter: {path}")
    frontmatter = match.group(1)
    body = text[match.end():]
    declared = next((line.split(":", 1)[1].strip() for line in frontmatter.splitlines() if line.startswith("name:")), "")
    checks = {
        "T": declared == skill_dir.name and "description:" in frontmatter,
        "R": "validate" in body.lower() and any(word in body.lower() for word in ("never", "stop", "reject")),
        "A": any(word in body.lower() for word in ("use when", "when to use", "能力边界")),
        "C": 0 < len(body.splitlines()) <= 220,
        "E": "completed" in body.lower() and any(word in body.lower() for word in ("submitted", "querying")),
    }
    return {"skill_name": skill_dir.name, "dimensions": checks, "passed": all(checks.values())}


def evaluate_all(root: Path) -> dict[str, object]:
    reports = [evaluate_skill(path) for path in sorted((root / "skills").iterdir()) if (path / "SKILL.md").is_file()]
    return {"skill_trace": f"{sum(bool(item['passed']) for item in reports)}/{len(reports)}", "reports": reports}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = evaluate_all(root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if all(bool(item["passed"]) for item in report["reports"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
