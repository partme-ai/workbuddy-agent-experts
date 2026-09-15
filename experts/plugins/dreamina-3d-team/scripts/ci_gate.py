#!/usr/bin/env python3
"""Strict, self-contained offline production gate for Dreamina 3D."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StrictGateError(RuntimeError):
    pass


def assert_test_result(result: unittest.TestResult) -> None:
    if result.skipped:
        reasons = "; ".join(reason for _, reason in result.skipped)
        raise StrictGateError(f"required tests skipped: {reasons}")
    if not result.wasSuccessful():
        raise StrictGateError("required unittest suite failed")


def _files(root: Path) -> dict[str, str]:
    result = {}
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(root).as_posix()
        result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def verify_disposable_install(source: Path, cache_root: Path) -> dict[str, object]:
    manifest = json.loads((source / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    destination = cache_root / "partme-ai-dreamina-3d" / manifest["name"] / manifest["version"]
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
    source_hashes = _files(source)
    installed_hashes = _files(destination)
    if source_hashes != installed_hashes:
        raise StrictGateError("disposable installed candidate differs from source")
    return {"version": manifest["version"], "files_verified": len(source_hashes), "parity": True}


def validate_companion(label: str, repo: Path) -> None:
    validator = repo / "scripts" / "validate_distribution.py"
    if not validator.is_file():
        raise StrictGateError(f"required companion validator missing: {label} at {repo}")
    proc = subprocess.run([sys.executable, str(validator), str(repo)], cwd=repo, capture_output=True, text=True, timeout=180)
    if proc.returncode != 0:
        raise StrictGateError(f"{label} validator failed: {(proc.stdout + proc.stderr).strip()}")


def _flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


# Floor for the strict gate. If a refactor ever filters or renames tests such
# that the selected suite shrinks, an empty or near-empty suite would otherwise
# report success. Keep this in step with the real suite size.
MINIMUM_REQUIRED_TESTS = 150


def run_required_tests() -> unittest.TestResult:
    discovered = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    required = unittest.TestSuite(
        test for test in _flatten(discovered)
        if ".CodexCliTests." not in test.id()
    )
    selected = required.countTestCases()
    if selected < MINIMUM_REQUIRED_TESTS:
        raise StrictGateError(
            f"strict gate selected only {selected} tests, below the required "
            f"floor of {MINIMUM_REQUIRED_TESTS}; the discovery filter may be "
            "excluding the suite"
        )
    result = unittest.TextTestRunner(verbosity=1).run(required)
    assert_test_result(result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", required=True)
    args = parser.parse_args(argv)
    del args
    blender = Path(os.environ.get("CODEX_BLENDER_REPO", ROOT.parent / "codex-blender-plugin"))
    design = Path(os.environ.get("CODEX_DREAMINA_DESIGN_REPO", ROOT.parent / "codex-dreamina-design-plugin"))
    validate_companion("codex-blender", blender)
    validate_companion("codex-dreamina-design", design)
    validate_companion("codex-dreamina-3d", ROOT)
    from trace_gate import evaluate_all
    trace = evaluate_all(ROOT)
    if not all(bool(item["passed"]) for item in trace["reports"]):
        raise StrictGateError("repository TRACE behavior gate failed")
    with tempfile.TemporaryDirectory(prefix="dreamina-3d-ci-cache-") as tmp:
        install = verify_disposable_install(ROOT, Path(tmp))
    result = run_required_tests()
    print(json.dumps({"strict": True, "tests_run": result.testsRun, "required_skips": 0, "trace": trace["skill_trace"], "install": install}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except StrictGateError as exc:
        print(f"STRICT_GATE_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
