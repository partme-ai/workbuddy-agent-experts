#!/usr/bin/env python3
"""Audit lossless Java-to-Zig source-test, asset, and result parity."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path


JAVA_ANNOTATION = re.compile(
    r"@(?P<kind>Test|ParameterizedTest|RepeatedTest|TestFactory|TestTemplate)\b"
    r"(?:\s*\([^)]*\))?",
    re.MULTILINE,
)
JAVA_METHOD = re.compile(
    r"(?:public|protected|private|static|final|synchronized|\s)+"
    r"(?:<[^>{};]+>\s*)?[\w$<>\[\],?.\s]+\s+"
    r"(?P<name>[A-Za-z_$][\w$]*)\s*\(",
    re.MULTILINE,
)
ZIG_TEST = re.compile(r'\btest\s+"(?P<name>(?:[^"\\]|\\.)*)"\s*\{')
COMPLETE_DISPOSITIONS = {"MIRRORED", "ADAPTED", "SPLIT", "MERGED_APPROVED"}
PRESERVATION_FIELDS = (
    "contract_preserved",
    "inputs_preserved",
    "assertions_preserved",
    "fixture_state_preserved",
    "cleanup_preserved",
)
PARAMETERIZED_KINDS = {
    "ParameterizedTest",
    "RepeatedTest",
    "TestFactory",
    "TestTemplate",
}
DEFAULT_ASSET_MARKERS = (
    ("src", "test", "resources"),
    ("test", "resources"),
    ("tests", "resources"),
)
EXCLUDED_DIRS = {".git", ".codegraph", ".gradle", "build", "target", "zig-cache", ".zig-cache", "zig-out"}


@dataclass(frozen=True)
class JavaTest:
    file: str
    line: int
    name: str
    kind: str

    @property
    def key(self) -> str:
        return f"{self.file}#{self.name}"


@dataclass
class AuditSummary:
    manifest: str | None
    java_tests: int = 0
    mapped_java_tests: int = 0
    manifest_cases: int = 0
    java_assets: int = 0
    exact_assets: int = 0
    acceptance_module: str | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return bool(self.errors)


def safe_file(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe relative path: {relative}")
    resolved_root = root.resolve()
    candidate = (resolved_root / path).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(f"path escapes root: {relative}") from error
    return candidate


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_files(root: Path, suffix: str) -> list[Path]:
    return [
        path
        for path in sorted(root.rglob(f"*{suffix}"))
        if path.is_file() and not set(path.relative_to(root).parts).intersection(EXCLUDED_DIRS)
    ]


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def extract_java_tests(java_root: Path) -> list[JavaTest]:
    tests: list[JavaTest] = []
    for path in source_files(java_root, ".java"):
        text = path.read_text(encoding="utf-8", errors="replace")
        annotations = list(JAVA_ANNOTATION.finditer(text))
        for index, annotation in enumerate(annotations):
            next_annotation = annotations[index + 1].start() if index + 1 < len(annotations) else len(text)
            method = JAVA_METHOD.search(text, annotation.end(), min(next_annotation, annotation.end() + 1800))
            if method is None:
                continue
            tests.append(
                JavaTest(
                    file=path.relative_to(java_root).as_posix(),
                    line=line_number(text, annotation.start()),
                    name=method.group("name"),
                    kind=annotation.group("kind"),
                )
            )
    return tests


def extract_zig_test_names(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {match.group("name") for match in ZIG_TEST.finditer(text)}


def path_contains(path: Path, marker: tuple[str, ...]) -> bool:
    parts = path.parts
    width = len(marker)
    return any(parts[index:index + width] == marker for index in range(len(parts) - width + 1))


def discover_java_assets(java_root: Path, extra_roots: list[Path]) -> list[Path]:
    assets: set[Path] = set()
    for path in sorted(java_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(java_root)
        if set(relative.parts).intersection(EXCLUDED_DIRS):
            continue
        if any(path_contains(relative, marker) for marker in DEFAULT_ASSET_MARKERS):
            assets.add(path)
    for configured in extra_roots:
        root = configured if configured.is_absolute() else java_root / configured
        root = root.resolve()
        try:
            root.relative_to(java_root.resolve())
        except ValueError as error:
            raise ValueError(f"asset root escapes Java root: {configured}") from error
        if not root.is_dir():
            raise ValueError(f"asset root is not a directory: {configured}")
        assets.update(path for path in root.rglob("*") if path.is_file())
    return sorted(assets)


def require_artifact(manifest: Path, value: object, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}.artifact is required")
        return
    try:
        artifact = safe_file(manifest.parent, value)
    except ValueError as error:
        errors.append(f"{label}: {error}")
        return
    if not artifact.is_file():
        errors.append(f"{label}: artifact does not exist: {artifact}")


def validate_run(run: object, label: str, manifest: Path, errors: list[str]) -> dict[str, object] | None:
    if not isinstance(run, dict):
        errors.append(f"{label} is required")
        return None
    if not isinstance(run.get("command"), str) or not run["command"].strip():
        errors.append(f"{label}.command is required")
    require_artifact(manifest, run.get("artifact"), label, errors)
    if run.get("status") != "PASS":
        errors.append(f"{label}.status must be PASS")
    for field_name in ("failed", "skipped", "not_run"):
        if run.get(field_name) != 0:
            errors.append(f"{label}.{field_name} must equal 0")
    return run


def validate_acceptance(
    raw: object,
    manifest: Path,
    zig_root: Path,
    errors: list[str],
) -> str | None:
    label = "acceptance_module"
    if not isinstance(raw, dict):
        errors.append(f"{label} is required")
        return None
    name = raw.get("name")
    if not isinstance(name, str) or not name.endswith("-test"):
        errors.append(f"{label}.name must use singular <project>-test")
        name = None
    root_value = raw.get("root")
    module_root: Path | None = None
    if not isinstance(root_value, str) or not root_value:
        errors.append(f"{label}.root is required")
    else:
        try:
            module_root = safe_file(zig_root, root_value)
        except ValueError as error:
            errors.append(f"{label}: {error}")
        else:
            if not module_root.is_dir():
                errors.append(f"{label}: module root does not exist: {module_root}")
            if isinstance(name, str) and module_root.name != name:
                errors.append(f"{label}: directory name must match {name}")
    if raw.get("published") is not False:
        errors.append(f"{label}.published must be false")
    components = raw.get("components")
    if not isinstance(components, list) or not components or not all(
        isinstance(component, str) and component for component in components
    ):
        errors.append(f"{label}.components must be a non-empty string list")
    build_step = raw.get("build_step")
    if build_step != "migration-test":
        errors.append(f"{label}.build_step must be migration-test")
    run = validate_run(raw, label, manifest, errors)
    if isinstance(run, dict) and run.get("command") != "zig build migration-test":
        errors.append(f"{label}.command must equal `zig build migration-test`")

    build_manifest = raw.get("build_manifest")
    if not isinstance(build_manifest, str) or not build_manifest:
        errors.append(f"{label}.build_manifest is required")
    else:
        try:
            build_path = safe_file(zig_root, build_manifest)
        except ValueError as error:
            errors.append(f"{label}: {error}")
        else:
            if not build_path.is_file():
                errors.append(f"{label}: build manifest does not exist: {build_path}")
            else:
                build_text = build_path.read_text(encoding="utf-8", errors="replace")
                step_pattern = re.compile(r'b\.step\(\s*"migration-test"\s*,')
                if step_pattern.search(build_text) is None:
                    errors.append(f"{label}: build.zig does not register migration-test")
                if isinstance(root_value, str) and root_value not in build_text:
                    errors.append(f"{label}: build.zig does not reference {root_value}")

    package_manifest = zig_root / "build.zig.zon"
    if package_manifest.is_file() and isinstance(root_value, str):
        zon_text = package_manifest.read_text(encoding="utf-8", errors="replace")
        paths_match = re.search(r"\.paths\s*=\s*\.\{(?P<body>.*?)\}\s*,", zon_text, re.DOTALL)
        if paths_match is not None and f'"{root_value}"' in paths_match.group("body"):
            errors.append(f"{label}: {root_value} must be excluded from package .paths")
    return name


def validate_manifest(
    manifest: Path | None,
    java_root: Path,
    zig_root: Path,
    java_tests: list[JavaTest],
    java_assets: list[Path],
) -> AuditSummary:
    summary = AuditSummary(
        manifest=str(manifest) if manifest else None,
        java_tests=len(java_tests),
        java_assets=len(java_assets),
    )
    if manifest is None or not manifest.is_file():
        summary.errors.append("source parity manifest is required")
        return summary
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        summary.errors.append(f"cannot read source parity manifest: {error}")
        return summary
    if payload.get("schema") != 2:
        summary.errors.append("manifest schema must equal 2")
    if payload.get("target_language") != "zig":
        summary.errors.append("target_language must equal zig")
    for baseline in ("java_baseline", "target_baseline"):
        if not isinstance(payload.get(baseline), str) or not payload[baseline].strip():
            summary.errors.append(f"{baseline} is required")
    summary.acceptance_module = validate_acceptance(
        payload.get("acceptance_module"), manifest, zig_root, summary.errors
    )

    records = payload.get("source_tests")
    if not isinstance(records, list):
        summary.errors.append("source_tests must be a list")
        records = []
    by_source: dict[str, list[dict[str, object]]] = {}
    for index, raw in enumerate(records):
        if not isinstance(raw, dict) or not isinstance(raw.get("source"), str):
            summary.errors.append(f"source_tests[{index}] must contain source")
            continue
        by_source.setdefault(raw["source"], []).append(raw)
        summary.manifest_cases += 1

    extracted = {test.key: test for test in java_tests}
    for stale in sorted(set(by_source) - set(extracted)):
        summary.errors.append(f"manifest Java test not found: {stale}")
    for key, test in extracted.items():
        mappings = by_source.get(key, [])
        if not mappings:
            summary.errors.append(f"missing Java test mapping: {key}")
            continue
        summary.mapped_java_tests += 1
        case_ids: set[str] = set()
        for index, record in enumerate(mappings):
            label = f"{key}[{index}]"
            if record.get("disposition") not in COMPLETE_DISPOSITIONS:
                summary.errors.append(f"{label}: incomplete disposition {record.get('disposition')}")
            for field_name in PRESERVATION_FIELDS:
                if record.get(field_name) is not True:
                    summary.errors.append(f"{label}: {field_name} must be true")
            if record.get("result_parity") != "MATCH":
                summary.errors.append(f"{label}: result_parity must be MATCH")
            targets = record.get("targets")
            if not isinstance(targets, list) or not targets or not all(isinstance(value, str) for value in targets):
                summary.errors.append(f"{label}: targets must be a non-empty string list")
            else:
                for anchor in targets:
                    file_value, separator, test_name = anchor.partition("#")
                    try:
                        target_file = safe_file(zig_root, file_value)
                    except ValueError as error:
                        summary.errors.append(f"{label}: {error}")
                        continue
                    if not target_file.is_file():
                        summary.errors.append(f"{label}: Zig target file does not exist: {target_file}")
                    elif separator and test_name not in extract_zig_test_names(target_file):
                        summary.errors.append(f"{label}: Zig test anchor not found: {anchor}")
            require_artifact(manifest, record.get("evidence"), label, summary.errors)
            case_id = record.get("case_id")
            if test.kind in PARAMETERIZED_KINDS:
                if not isinstance(case_id, str) or not case_id:
                    summary.errors.append(f"{label}: case_id is required")
                elif case_id in case_ids:
                    summary.errors.append(f"{label}: duplicate case_id {case_id}")
                else:
                    case_ids.add(case_id)
                if record.get("case_expansion_complete") is not True:
                    summary.errors.append(f"{label}: case_expansion_complete must be true")

    asset_records = payload.get("assets")
    if not isinstance(asset_records, list):
        summary.errors.append("assets must be a list")
        asset_records = []
    by_asset = {
        record.get("source"): record
        for record in asset_records
        if isinstance(record, dict) and isinstance(record.get("source"), str)
    }
    discovered_assets = {path.relative_to(java_root).as_posix() for path in java_assets}
    for source in sorted(discovered_assets - set(by_asset)):
        summary.errors.append(f"missing source asset mapping: {source}")
    for source, record in by_asset.items():
        label = f"asset {source}"
        try:
            source_file = safe_file(java_root, source)
        except ValueError as error:
            summary.errors.append(f"{label}: {error}")
            continue
        target_value = record.get("target")
        if record.get("mode") != "COPY_EXACT":
            summary.errors.append(f"{label}: mode must be COPY_EXACT")
            continue
        if not source_file.is_file() or not isinstance(target_value, str):
            summary.errors.append(f"{label}: source and target files are required")
            continue
        try:
            target_file = safe_file(zig_root, target_value)
        except ValueError as error:
            summary.errors.append(f"{label}: {error}")
            continue
        if not target_file.is_file():
            summary.errors.append(f"{label}: target does not exist: {target_file}")
            continue
        source_hash = sha256_file(source_file)
        if record.get("sha256") != source_hash:
            summary.errors.append(f"{label}: declared SHA-256 does not match source")
        elif sha256_file(target_file) != source_hash:
            summary.errors.append(f"{label}: source/target SHA-256 mismatch")
        else:
            summary.exact_assets += 1

    runs = payload.get("runs")
    if not isinstance(runs, dict):
        summary.errors.append("runs must be an object")
    else:
        validate_run(runs.get("java"), "runs.java", manifest, summary.errors)
        validate_run(runs.get("target"), "runs.target", manifest, summary.errors)
        differential = runs.get("differential")
        if not isinstance(differential, dict):
            summary.errors.append("runs.differential is required")
        else:
            if not isinstance(differential.get("command"), str) or not differential["command"].strip():
                summary.errors.append("runs.differential.command is required")
            require_artifact(manifest, differential.get("artifact"), "runs.differential", summary.errors)
            if differential.get("status") != "PASS":
                summary.errors.append("runs.differential.status must be PASS")
            for field_name in ("mismatched", "harness_failures", "skipped", "not_run"):
                if differential.get(field_name) != 0:
                    summary.errors.append(f"runs.differential.{field_name} must equal 0")
            if differential.get("matched") != summary.manifest_cases:
                summary.errors.append(
                    f"runs.differential.matched must equal manifest cases ({summary.manifest_cases})"
                )
    return summary


def markdown(summary: AuditSummary) -> str:
    lines = [
        "# Java-to-Zig Migration Test Audit",
        "",
        f"- Manifest: `{summary.manifest or 'MISSING'}`",
        f"- Acceptance module: `{summary.acceptance_module or 'MISSING'}`",
        f"- Java tests mapped: **{summary.mapped_java_tests}/{summary.java_tests}**",
        f"- Manifest cases: **{summary.manifest_cases}**",
        f"- Exact assets: **{summary.exact_assets}/{summary.java_assets}**",
        f"- Completion blocked: **{str(summary.blocked).lower()}**",
        "",
    ]
    lines.extend(f"- ERROR: {error}" for error in summary.errors)
    if not summary.errors:
        lines.append("**Strict Java-to-Zig source parity gate passed.**")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java-root", required=True, type=Path)
    parser.add_argument("--zig-root", required=True, type=Path)
    parser.add_argument("--parity-manifest", type=Path)
    parser.add_argument("--java-test-assets-root", action="append", default=[], type=Path)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on-incomplete", action="store_true")
    args = parser.parse_args()

    try:
        java_assets = discover_java_assets(args.java_root, args.java_test_assets_root)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    summary = validate_manifest(
        args.parity_manifest,
        args.java_root,
        args.zig_root,
        extract_java_tests(args.java_root),
        java_assets,
    )
    report = (
        json.dumps({**asdict(summary), "blocked": summary.blocked}, ensure_ascii=False, indent=2)
        if args.format == "json"
        else markdown(summary)
    )
    if args.output:
        args.output.write_text(report + "\n", encoding="utf-8")
    else:
        print(report)
    if args.fail_on_incomplete and summary.blocked:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
