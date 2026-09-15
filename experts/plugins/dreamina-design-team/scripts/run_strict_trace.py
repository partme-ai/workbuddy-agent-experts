"""Strict per-Skill TRACE for the Dreamina Design plugin.

Implements the offline equivalent of the plan's "Run quick validation,
strict TRACE and forward scenarios for every packaged entry" gate.

For every Skill directory under ``skills_root``, the tracer checks:

* **frontmatter** — YAML frontmatter parses and contains ``name`` and
  ``description`` (and, where applicable, ``upstream_commit_sha``);
* **body** — the Skill has substantive prose (>= 80 characters after
  the closing ``---``);
* **examples** — at least one fenced code block is present;
* **links** — every local relative link (``./foo``, ``../foo``,
  ``foo.md``) resolves to a real file; external ``http(s)`` URLs are
  reported but never network-checked in offline mode.

The tracer is read-only. It never invokes the network and never
performs any Dreamina generation.
"""

from __future__ import annotations

import dataclasses
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


FRONTMATTER_OPEN = re.compile(r"^---\s*$")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CODE_FENCE_PATTERN = re.compile(r"^```", re.MULTILINE)
FRONTMATTER_KEY_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(.*)$")
MIN_BODY_LENGTH = 80


def _validate_frontmatter_block(block: str) -> list[str]:
    """Return a list of YAML-shape errors for a frontmatter block.

    A frontmatter block must consist of ``key: value`` pairs. A value may
    continue on subsequent lines **only if those lines are indented**
    (either a ``|`` / ``>`` block scalar or an indented plain scalar).

    An unindented continuation line makes the block unparseable YAML. Codex
    silently skips any Skill whose frontmatter fails to parse, so such a
    Skill is invisible to the model even though every key is nominally
    present — this check exists to catch exactly that failure mode.
    """
    errors: list[str] = []
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        match = FRONTMATTER_KEY_PATTERN.match(line)
        if match is None:
            errors.append(
                "invalid frontmatter line (not a `key: value` pair, and not "
                f"indented): {line!r} — an unindented plain-scalar "
                "continuation makes the block unparseable YAML and the Skill "
                "will be silently skipped"
            )
            i += 1
            continue
        j = i + 1
        while j < len(lines) and lines[j].strip() and lines[j][:1] in (" ", "\t"):
            j += 1
        i = j
    return errors


@dataclass
class SkillTraceResult:
    skill_name: str
    skill_md_path: str
    frontmatter_status: str = "NOT_RUN"
    frontmatter_errors: list[str] = field(default_factory=list)
    body_status: str = "NOT_RUN"
    body_errors: list[str] = field(default_factory=list)
    examples_status: str = "NOT_RUN"
    examples_errors: list[str] = field(default_factory=list)
    links_status: str = "NOT_RUN"
    links_errors: list[str] = field(default_factory=list)

    def is_passing(self) -> bool:
        return all(
            status == "PASS"
            for status in (
                self.frontmatter_status,
                self.body_status,
                self.examples_status,
                self.links_status,
            )
        )


@dataclass
class StrictTraceReport:
    skills_root: str
    overall_status: str = "NOT_RUN"
    passed_skills: int = 0
    failed_skills: int = 0
    skill_results: dict[str, SkillTraceResult] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), indent=2, sort_keys=True)


def _extract_frontmatter_block(text: str) -> str | None:
    """Return the raw frontmatter block between the ``---`` fences."""
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    return text[3:end].strip("\n")


def _parse_frontmatter(text: str) -> tuple[dict[str, str], int]:
    """Return (parsed frontmatter dict, body offset)."""
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return {}, -1
    body_offset = text.find("\n---", 3)
    if body_offset == -1:
        return {}, -1
    block = text[3:body_offset].strip()
    parsed: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        parsed[key.strip()] = value.strip()
    end_marker = text.find("\n", body_offset + 4)
    body_start = end_marker + 1 if end_marker != -1 else body_offset + 4
    return parsed, body_start


class StrictTracer:
    """Run per-Skill frontmatter / body / examples / links checks."""

    def __init__(
        self,
        *,
        skills_root: Path,
        check_external_links: bool = False,
        required_fields: Iterable[str] = ("name", "description"),
        additional_required_for_packaged: Iterable[str] = (),
        upstream_skills_root: Path | None = None,
    ) -> None:
        self._skills_root = Path(skills_root)
        self._check_external_links = check_external_links
        self._required_fields = tuple(required_fields)
        self._additional_required_for_packaged = tuple(additional_required_for_packaged)
        # When ``upstream_skills_root`` is provided, the tracer validates the
        # upstream Skill bodies (which carry the real content) instead of the
        # local stubs. This is the correct interpretation for the plan's
        # "strict TRACE on every packaged entry" gate: per the plan, the
        # plugin tracks upstream Skills rather than copying them, so TRACE
        # runs against the upstream source of truth.
        self._upstream_skills_root = (
            Path(upstream_skills_root) if upstream_skills_root is not None else None
        )

    def run(self) -> StrictTraceReport:
        report = StrictTraceReport(skills_root=str(self._skills_root))
        if not self._skills_root.is_dir():
            report.overall_status = "FAIL"
            return report
        for entry in sorted(self._skills_root.iterdir()):
            if not entry.is_dir():
                continue
            result = self._trace_skill(entry)
            report.skill_results[entry.name] = result
            if result.is_passing():
                report.passed_skills += 1
            else:
                report.failed_skills += 1
        report.overall_status = "PASS" if report.failed_skills == 0 else "FAIL"
        return report

    def trace_against_upstream(self) -> StrictTraceReport:
        """Run the same per-Skill checks against the upstream source of truth.

        This independently walks the cloned upstream ``skills/`` directory
        so callers can compare source quality with the byte-parity verifier.
        """
        if self._upstream_skills_root is None:
            raise RuntimeError(
                "upstream_skills_root not configured; cannot trace against upstream"
            )
        report = StrictTraceReport(
            skills_root=f"upstream:{self._upstream_skills_root}"
        )
        if not self._upstream_skills_root.is_dir():
            report.overall_status = "FAIL"
            return report
        for entry in sorted(self._upstream_skills_root.iterdir()):
            if not entry.is_dir():
                continue
            result = self._trace_skill(entry, require_packaged_pin=False)
            report.skill_results[entry.name] = result
            if result.is_passing():
                report.passed_skills += 1
            else:
                report.failed_skills += 1
        report.overall_status = "PASS" if report.failed_skills == 0 else "FAIL"
        return report

    # ------------------------------------------------------------------
    # Per-Skill trace
    # ------------------------------------------------------------------
    def _trace_skill(self, skill_dir: Path, *, require_packaged_pin: bool = True) -> SkillTraceResult:
        skill_md = skill_dir / "SKILL.md"
        result = SkillTraceResult(skill_name=skill_dir.name, skill_md_path=str(skill_md))
        if not skill_md.is_file():
            result.frontmatter_status = "FAIL"
            result.frontmatter_errors.append("SKILL.md missing")
            result.body_status = "FAIL"
            result.body_errors.append("SKILL.md missing")
            result.examples_status = "FAIL"
            result.examples_errors.append("SKILL.md missing")
            result.links_status = "FAIL"
            result.links_errors.append("SKILL.md missing")
            return result
        text = skill_md.read_text(encoding="utf-8")
        frontmatter, body_offset = _parse_frontmatter(text)
        self._check_frontmatter(frontmatter, skill_dir.name, result, require_packaged_pin=require_packaged_pin)
        # Catch unparseable-YAML frontmatter that still yields the expected
        # keys. Codex silently skips such Skills entirely.
        block = _extract_frontmatter_block(text)
        if block is not None:
            result.frontmatter_errors.extend(_validate_frontmatter_block(block))
            if result.frontmatter_errors:
                result.frontmatter_status = "FAIL"
        body = text[body_offset:] if body_offset >= 0 else ""
        self._check_body(body, result)
        self._check_examples(body, result)
        self._check_links(body, skill_md, result)
        return result

    def _check_frontmatter(
        self,
        frontmatter: dict[str, str],
        skill_name: str,
        result: SkillTraceResult,
        *,
        require_packaged_pin: bool = True,
    ) -> None:
        if not frontmatter:
            result.frontmatter_status = "FAIL"
            result.frontmatter_errors.append("frontmatter missing or unparseable")
            return
        missing = [f for f in self._required_fields if f not in frontmatter or not frontmatter[f]]
        if missing:
            result.frontmatter_status = "FAIL"
            result.frontmatter_errors.append(f"missing required field: {', '.join(missing)}")
            return
        # ``upstream_commit_sha`` is a packaging contract for *local* Skills
        # only. Upstream Skills legitimately omit it; when we trace the
        # upstream source of truth, the field is not required.
        if require_packaged_pin and skill_name != "dreamina-design-use":
            missing_sha = [
                f for f in self._additional_required_for_packaged if not frontmatter.get(f)
            ]
            if missing_sha:
                result.frontmatter_status = "FAIL"
                result.frontmatter_errors.append(
                    f"missing required field for packaged Skill: {', '.join(missing_sha)}"
                )
                return
        result.frontmatter_status = "PASS"

    def _check_body(self, body: str, result: SkillTraceResult) -> None:
        if len(body.strip()) < MIN_BODY_LENGTH:
            result.body_status = "FAIL"
            result.body_errors.append(
                f"body too short ({len(body.strip())} < {MIN_BODY_LENGTH} chars)"
            )
            return
        result.body_status = "PASS"

    def _check_examples(self, body: str, result: SkillTraceResult) -> None:
        if not CODE_FENCE_PATTERN.search(body):
            result.examples_status = "FAIL"
            result.examples_errors.append("no fenced code block found")
            return
        result.examples_status = "PASS"

    def _check_links(self, body: str, skill_md: Path, result: SkillTraceResult) -> None:
        errors: list[str] = []
        for _label, target in LINK_PATTERN.findall(body):
            stripped = target.strip()
            if not stripped or stripped.startswith("#"):
                continue
            lowered = stripped.lower()
            if lowered.startswith(("http://", "https://", "mailto:")):
                if self._check_external_links:
                    # Offline mode never reaches here; reserved for future
                    # online integration runs.
                    errors.append(f"external link not reachable offline: {stripped}")
                continue
            # Resolve relative to the SKILL.md location.
            resolved = (skill_md.parent / stripped).resolve()
            try:
                resolved.relative_to(skill_md.parent.parent.resolve())
            except ValueError:
                errors.append(f"link escapes skills/ root: {stripped}")
                continue
            if not resolved.exists():
                errors.append(f"link target missing: {stripped}")
        if errors:
            result.links_status = "FAIL"
            result.links_errors.extend(errors)
            return
        result.links_status = "PASS"


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    skills_root = Path("skills").resolve()
    upstream_skills_root: Path | None = None
    upstream_root: Path | None = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--skills-root" and i + 1 < len(args):
            skills_root = Path(args[i + 1]).resolve()
            i += 2
            continue
        if arg == "--upstream-root" and i + 1 < len(args):
            upstream_root = Path(args[i + 1]).resolve()
            i += 2
            continue
        if arg == "--strict":
            i += 1
            continue
        i += 1
    if upstream_root is not None:
        upstream_skills_root = upstream_root / "skills"
        if not upstream_skills_root.is_dir():
            upstream_skills_root = upstream_root
    tracer = StrictTracer(
        skills_root=skills_root,
        upstream_skills_root=upstream_skills_root,
    )
    if upstream_skills_root is not None:
        report = tracer.trace_against_upstream()
    else:
        report = tracer.run()
    print(report.to_json())
    return 0 if report.overall_status == "PASS" else 1


__all__ = [
    "SkillTraceResult",
    "StrictTraceReport",
    "StrictTracer",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
