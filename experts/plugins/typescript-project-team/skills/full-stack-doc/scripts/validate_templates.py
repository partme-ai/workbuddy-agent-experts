#!/usr/bin/env python3
"""Validate the full-stack-doc source without rendering a target project."""

from __future__ import annotations

import re
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SKILL_ROOT / "templates"
EXPECTED_COUNTS = {
    "root": 10,
    "version": 7,
    "module": 3,
    "delivery": 5,
    "readme": 5,
    "architecture": 1,
}
EXPECTED_PROFILE_COUNTS = {
    "readme/rust-profiles": 7,
    "architecture/profiles": 7,
}
ALLOWED_TOKENS = {
    "API_BASE_URL",
    "ARTIFACT_ID",
    "BOM_ARTIFACT_ID",
    "CONFIG_PATH",
    "CONFIG_PREFIX",
    "CRATE_NAME",
    "DEFAULT_FEATURES",
    "DATETIME",
    "DATE",
    "DOC_ROOT",
    "GROUP_ID",
    "HOST_NAME",
    "HOST_VERSION",
    "INSTALL_SCOPE",
    "JAVA_VERSION",
    "MAIN_CLASS",
    "MANIFEST_PATH",
    "MAVEN_VERSION",
    "MODULE_INDEX",
    "MODULE_NAME",
    "OPEN_SOURCE_NAME",
    "ORGANIZATION",
    "OWNER",
    "PACKAGE_MANAGER",
    "PACKAGE_NAME",
    "PREPROD_BASE_URL",
    "PRIMARY_LANGUAGE",
    "PROJECT_DESCRIPTION",
    "PROJECT_NAME",
    "PROJECT_TAGLINE",
    "PLUGIN_ID",
    "PRODUCT_NAME",
    "PROD_BASE_URL",
    "REPOSITORY_URL",
    "RUNTIME_NAME",
    "RUNTIME_VERSION",
    "RUST_EDITION",
    "RUST_VERSION",
    "SECURITY_CONTACT",
    "START_COMMAND",
    "SKILL_COUNT",
    "SPRING_BOOT_VERSION",
    "SWAGGER_URL",
    "TEST_BASE_URL",
    "TEST_PASSWORD",
    "TEST_USERNAME",
    "TEST_COMMAND",
    "BUILD_COMMAND",
    "CI_BADGE_URL",
    "CI_URL",
    "CONFIG_FILE",
    "CURRENT_VERSION",
    "DOCS_URL",
    "INSTALL_COMMAND",
    "ISSUES_URL",
    "LICENSE_NAME",
    "LICENSE_URL",
    "VERSION",
    "WORKSPACE_RESOLVER",
}
TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")
ABSOLUTE_LOCAL_PATH_RE = re.compile(
    "/" + r"Users/[^/\s`]+/(?:workspaces?|projects?)/|"
    "/" + r"home/[^/\s`]+/(?:workspaces?|projects?)/"
)
PRIVATE_PATTERNS = (
    re.compile("Part" + "Me", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z])" + "Oc" + r"to[A-Za-z]*", re.IGNORECASE),
    re.compile("Open" + "Ecom", re.IGNORECASE),
    re.compile("Open" + "Mem", re.IGNORECASE),
)
STALE_LINK_NAMES = (
    "4、需求分析模板.md",
    "5、PRD文档模板.md",
    "6、视觉与交互%20DNA%20规范模板.md",
    "9、系统架构设计模板.md",
    "10、技术细分模板.md",
    "11、功能提测模板.md",
    "12、测试结果模板.md",
    "14、项目运维模板.md",
)
PRESERVATION_FLOORS = {
    "module/模块-PRD.md": 1050,
    "version/5、PRD文档.md": 700,
    "delivery/5、项目运维模板.md": 850,
    "readme/README模板.md": 700,
    "readme/README-Java项目模板.md": 400,
    "readme/README-Rust项目模板.md": 450,
    "readme/README-插件项目模板.md": 380,
    "readme/README-技能包与生态目录模板.md": 350,
    "readme/rust-profiles/README.md": 65,
    "readme/rust-profiles/文档与文件格式处理剖面.md": 145,
    "readme/rust-profiles/上游兼容与移植剖面.md": 110,
    "readme/rust-profiles/大型工具箱Workspace剖面.md": 120,
    "readme/rust-profiles/认证与安全框架剖面.md": 125,
    "readme/rust-profiles/纯设计阶段剖面.md": 100,
    "readme/rust-profiles/多语言README布局剖面.md": 95,
    "architecture/架构设计文档模板.md": 900,
    "architecture/profiles/README.md": 45,
    "architecture/profiles/运行时与应用平台架构剖面.md": 80,
    "architecture/profiles/插件与扩展体系架构剖面.md": 95,
    "architecture/profiles/边缘与嵌入式架构剖面.md": 100,
    "architecture/profiles/消息与事件驱动架构剖面.md": 105,
    "architecture/profiles/AI-Agent与RAG架构剖面.md": 100,
    "architecture/profiles/可观测性与控制面架构剖面.md": 95,
}


def outside_fences(text: str) -> list[tuple[int, str]]:
    """Return line-numbered Markdown outside fenced code blocks."""
    result: list[tuple[int, str]] = []
    fence: str | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)[0]
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence is None:
            result.append((number, line))
    return result


def validate_template_text(label: str, text: str) -> list[str]:
    errors: list[str] = []
    visible = outside_fences(text)
    fence_lines = [line for line in text.splitlines() if re.match(r"^\s*(`{3,}|~{3,})", line)]
    if len(fence_lines) % 2:
        errors.append(f"{label}: unbalanced fenced code block")

    h1_lines = [number for number, line in visible if re.match(r"^#\s+", line)]
    if len(h1_lines) != 1:
        errors.append(f"{label}: expected one H1 outside code fences, found {len(h1_lines)}")

    unknown = sorted(set(TOKEN_RE.findall(text)) - ALLOWED_TOKENS)
    if unknown:
        errors.append(f"{label}: unknown global placeholders {unknown}")

    for pattern in PRIVATE_PATTERNS:
        match = pattern.search(text)
        if match:
            errors.append(f"{label}: private product name {match.group(0)!r}")
    match = ABSOLUTE_LOCAL_PATH_RE.search(text)
    if match:
        errors.append(f"{label}: local absolute path {match.group(0)!r}")

    if "123456" in text:
        errors.append(f"{label}: hard-coded sample password")
    for stale in STALE_LINK_NAMES:
        if stale in text:
            errors.append(f"{label}: stale template link {stale!r}")
    if label.startswith("templates/version/") and "{{VERSION}}/" in text:
        errors.append(f"{label}: version document must not prefix same-folder links with {{{{VERSION}}}}/")
    return errors


def validate_repository(skill_root: Path = SKILL_ROOT) -> list[str]:
    errors: list[str] = []
    template_root = skill_root / "templates"
    template_paths: list[Path] = []
    for group, expected in EXPECTED_COUNTS.items():
        paths = sorted((template_root / group).glob("*.md"))
        template_paths.extend(paths)
        if len(paths) != expected:
            errors.append(f"templates/{group}: expected {expected} Markdown files, found {len(paths)}")

    for group, expected in EXPECTED_PROFILE_COUNTS.items():
        paths = sorted((template_root / group).glob("*.md"))
        template_paths.extend(paths)
        if len(paths) != expected:
            errors.append(f"templates/{group}: expected {expected} Markdown files, found {len(paths)}")

    total_lines = 0
    for path in template_paths:
        text = path.read_text(encoding="utf-8")
        label = str(path.relative_to(skill_root))
        total_lines += len(text.splitlines())
        errors.extend(validate_template_text(label, text))

    if total_lines < 9500:
        errors.append(f"templates: preservation floor is 9500 lines, found {total_lines}")
    for relative, minimum in PRESERVATION_FLOORS.items():
        path = template_root / relative
        if path.is_file():
            lines = len(path.read_text(encoding="utf-8").splitlines())
            if lines < minimum:
                errors.append(f"templates/{relative}: preservation floor is {minimum} lines, found {lines}")

    for path in [skill_root / "SKILL.md", *sorted((skill_root / "references").glob("*.md"))]:
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            label = str(path.relative_to(skill_root))
            for pattern in PRIVATE_PATTERNS:
                match = pattern.search(text)
                if match:
                    errors.append(f"{label}: private product name {match.group(0)!r}")
            match = ABSOLUTE_LOCAL_PATH_RE.search(text)
            if match:
                errors.append(f"{label}: local absolute path {match.group(0)!r}")
    return errors


def main() -> int:
    errors = validate_repository()
    for error in errors:
        print(f"ERROR    {error}")
    print(
        f"SUMMARY  templates={sum(EXPECTED_COUNTS.values())} "
        f"profiles={sum(EXPECTED_PROFILE_COUNTS.values())} errors={len(errors)}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
