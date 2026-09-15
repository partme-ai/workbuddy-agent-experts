#!/usr/bin/env python3
"""Inventory source and target migration tests and verify copied test resources."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

JAVA_CASE = re.compile(r"@(Test|ParameterizedTest|RepeatedTest|TestFactory)\b")
SWIFT_CASE = re.compile(r"(?m)^\s*(?:@Test\b|func\s+test[A-Za-z0-9_]*)")


def is_test_source(path: Path) -> bool:
    return any(part.lower() in {"test", "tests", "testfixtures"} for part in path.parts)


def sources(root: Path, extension: str) -> list[Path]:
    return sorted(path for path in root.rglob(f"*{extension}") if is_test_source(path))


def count_cases(paths: list[Path], extension: str) -> int:
    pattern = SWIFT_CASE if extension == ".swift" else JAVA_CASE
    return sum(len(pattern.findall(path.read_text(encoding="utf-8", errors="ignore"))) for path in paths)


def resource_key(path: Path) -> str | None:
    parts = list(path.parts)
    for marker in ("resources", "testdata", "fixtures"):
        if marker in parts:
            index = parts.index(marker)
            prefix = "/".join(parts[max(0, index - 3):index])
            suffix = "/".join(parts[index + 1:])
            return f"{prefix}/{marker}/{suffix}"
    return None


def resource_hashes(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        key = resource_key(path.relative_to(root))
        if key is not None:
            result[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java-root", type=Path, required=True)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--target-extension", choices=(".kt", ".swift"), required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    java_sources = sources(args.java_root.resolve(), ".java")
    target_sources = sources(args.target_root.resolve(), args.target_extension)
    java_assets = resource_hashes(args.java_root.resolve())
    target_assets = resource_hashes(args.target_root.resolve())
    missing_assets = sorted(set(java_assets) - set(target_assets))
    changed_assets = sorted(
        key for key in set(java_assets) & set(target_assets)
        if java_assets[key] != target_assets[key]
    )
    java_cases = count_cases(java_sources, ".java")
    target_cases = count_cases(target_sources, args.target_extension)
    report = {
        "schema_version": 1,
        "warning": "Inventory is a lower-bound audit; explicit per-case mapping and differential MATCH evidence are still required.",
        "java": {"test_files": len(java_sources), "annotated_cases": java_cases},
        "target": {
            "extension": args.target_extension,
            "test_files": len(target_sources),
            "annotated_cases": target_cases,
        },
        "assets": {
            "java_count": len(java_assets),
            "target_count": len(target_assets),
            "missing": missing_assets,
            "changed": changed_assets,
        },
        "potential_gaps": {
            "test_file_deficit": max(0, len(java_sources) - len(target_sources)),
            "annotated_case_deficit": max(0, java_cases - target_cases),
            "asset_parity": not missing_assets and not changed_assets,
        },
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    gaps = report["potential_gaps"]
    return 1 if gaps["test_file_deficit"] or gaps["annotated_case_deficit"] or not gaps["asset_parity"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

