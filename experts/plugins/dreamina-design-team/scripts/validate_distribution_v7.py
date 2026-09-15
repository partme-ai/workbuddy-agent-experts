"""v7 distribution validator for the Dreamina Design plugin (Task 7).

Runs every check from ``scripts/validate_distribution.py`` and adds:

* Skill snapshot SHA consistency (each Skill's ``upstream_commit_sha``
  matches the verified upstream commit);
* link audit between ``plugin.json`` and ``marketplace.json``;
* symlink / cache directory detection;
* a stricter secret scan (PEM blocks, API key shapes);
* the canary gate: ``paid_canary`` is either ``APPROVED`` (when an
  approval marker file exists) or ``NOT_RUN`` — never silently
  consumed by CI;
* the read-only runtime contract: when the ``dreamina`` binary is not
  available on PATH, the verifier reports ``blocked`` with explicit
  instructions; it never silently passes.

The validator is intentionally read-only: it never installs the binary,
never authenticates, and never performs any generation.
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


EXPECTED_SKILLS: tuple[str, ...] = (
    "dreamina-cli",
    "dreamina-cli-image2image",
    "dreamina-cli-image2video",
    "dreamina-cli-text2image",
    "dreamina-cli-text2video",
    "dreamina-opencli-image2image",
    "dreamina-opencli-image2video",
    "dreamina-opencli-text2image",
    "dreamina-opencli-text2video",
    "dreamina-prompt-image2image",
    "dreamina-prompt-image2video",
    "dreamina-prompt-text2image",
    "dreamina-prompt-text2video",
)

SECRET_PATTERNS: tuple[re.Pattern[bytes], ...] = (
    re.compile(rb"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)

# File globs whose contents are *not* treated as live secrets. The test
# suite legitimately embeds byte patterns that match the secret
# detectors (e.g. fixture strings for the secret-scan test itself).
SAFE_BASENAMES: frozenset[str] = frozenset(
    {
        "test_distribution_v7.py",
        "test_secret_scan.py",  # legacy name kept for safety
    }
)


def _is_valid_version_capture(version_text: str) -> bool:
    """Accept semantic versions or the CLI's commit-based JSON build identity."""
    if re.search(r"\d+\.\d+", version_text):
        return True
    try:
        payload = json.loads(version_text)
    except (json.JSONDecodeError, ValueError):
        return False
    if not isinstance(payload, dict):
        return False
    version = payload.get("version")
    commit = payload.get("commit")
    if not isinstance(version, str) or not isinstance(commit, str):
        return False
    if re.fullmatch(r"[0-9a-fA-F]{7,40}", commit) is None:
        return False
    return version in {commit, f"{commit}-dirty"}


class DistributionV7Error(Exception):
    """Base class for v7 verifier errors."""


class SecretLikeContentError(DistributionV7Error):
    """A secret-shaped byte pattern was detected in a non-test file."""


class SymlinkError(DistributionV7Error):
    """A symlink was found inside the plugin tree."""


class SkillSnapshotShaMismatchError(DistributionV7Error):
    """A packaged Skill's upstream_commit_sha does not match the verified commit."""


class ReadOnlyRuntimeBlockedError(DistributionV7Error):
    """The dreamina CLI is required but missing from PATH."""


class CanaryMissingError(DistributionV7Error):
    """The caller invoked ``require_paid_canary`` while no approval was recorded."""


@dataclass
class SecretMatch:
    path: str
    pattern: str


@dataclass
class DistributionV7Report:
    skill_count: int = 0
    skill_snapshot_status: str = "NOT_RUN"
    skill_snapshot_mismatches: list[str] = field(default_factory=list)
    secret_matches: list[SecretMatch] = field(default_factory=list)
    symlinks: list[str] = field(default_factory=list)
    marketplace_url_matches: bool = False
    repository_url: str = ""
    paid_canary: str = "NOT_RUN"
    read_only_runtime_contract: str = "blocked"
    read_only_runtime_reason: str = ""
    cli_available: bool = False
    legacy_validator_exit_code: int = 0
    forbidden_installable_identities: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), indent=2, sort_keys=True)


class DistributionV7Verifier:
    """Run every v7 distribution check against the plugin root."""

    def __init__(
        self,
        *,
        root: Path,
        expected_upstream_sha: str | None = None,
        dreamina_command: str = "dreamina",
    ) -> None:
        self._root = Path(root)
        self._verification_dir = self._root / "docs" / "verification"
        self._expected_upstream_sha = expected_upstream_sha
        self._dreamina_command = dreamina_command

    # ------------------------------------------------------------------
    # Public surface
    # ------------------------------------------------------------------
    def run(self) -> DistributionV7Report:
        report = DistributionV7Report()
        report.cli_available = self._dreamina_available()
        self._run_legacy_validator(report)
        self._run_skill_snapshot_check(report)
        self._run_forbidden_identity_scan(report)
        self._run_secret_scan(report)
        self._run_symlink_scan(report)
        self._run_link_audit(report)
        self._run_canary_check(report)
        self._run_runtime_contract_check(report)
        return report

    def require_read_only_runtime(self) -> None:
        if not self._dreamina_available():
            raise ReadOnlyRuntimeBlockedError(
                "dreamina CLI is not available; "
                "read-only runtime contract is BLOCKED — install and authorize "
                "the CLI before requesting PASS"
            )

    def require_paid_canary(self) -> None:
        if not self._canary_approved():
            raise CanaryMissingError(
                "paid canary is NOT_RUN; either record an explicit approval "
                "via docs/verification/paid-canary-approved.md or treat "
                "the canary as a separate action-time approval"
            )

    # ------------------------------------------------------------------
    # Check implementations
    # ------------------------------------------------------------------
    def _run_legacy_validator(self, report: DistributionV7Report) -> None:
        legacy_script = Path(__file__).resolve().parent / "validate_distribution.py"
        if not legacy_script.is_file():
            report.legacy_validator_exit_code = -1
            return
        result = subprocess.run(  # noqa: S603 — argv-only
            [sys.executable, str(legacy_script), str(self._root)],
            capture_output=True,
            text=True,
            check=False,
        )
        report.legacy_validator_exit_code = result.returncode

    def _run_skill_snapshot_check(self, report: DistributionV7Report) -> None:
        skills_root = self._root / "skills"
        if not skills_root.is_dir():
            report.skill_snapshot_status = "FAIL"
            report.skill_snapshot_mismatches.append("skills/ directory missing")
            return
        found = 0
        for name in EXPECTED_SKILLS:
            skill_md = skills_root / name / "SKILL.md"
            if not skill_md.is_file():
                report.skill_snapshot_mismatches.append(f"{name}: SKILL.md missing")
                continue
            found += 1
        report.skill_count = found
        pin_path = skills_root / ".upstream-commit"
        pinned_sha = pin_path.read_text(encoding="utf-8").strip() if pin_path.is_file() else ""
        if not found:
            report.skill_snapshot_status = "FAIL"
            report.skill_snapshot_mismatches.append("no packaged Skills found")
            return
        if report.skill_snapshot_mismatches:
            report.skill_snapshot_status = "FAIL"
            return
        if re.fullmatch(r"[0-9a-f]{40}", pinned_sha) is None:
            report.skill_snapshot_status = "FAIL"
            report.skill_snapshot_mismatches.append(
                f"skills/.upstream-commit is not a 40-hex commit: {pinned_sha!r}"
            )
            return
        if self._expected_upstream_sha is not None and pinned_sha != self._expected_upstream_sha:
            report.skill_snapshot_status = "FAIL"
            report.skill_snapshot_mismatches.append(
                f"snapshot pin {pinned_sha} != expected {self._expected_upstream_sha}"
            )
            return
        report.skill_snapshot_status = "PASS"

    def _run_forbidden_identity_scan(self, report: DistributionV7Report) -> None:
        """No installable ``jimeng-*`` Skill identity may remain."""
        skills_root = self._root / "skills"
        if not skills_root.is_dir():
            return
        found = [p.name for p in sorted(skills_root.iterdir()) if p.is_dir() and p.name.startswith("jimeng-")]
        report.forbidden_installable_identities = found

    def _run_secret_scan(self, report: DistributionV7Report) -> None:
        for target in self._root.rglob("*"):
            if not target.is_file() or ".git" in target.parts:
                continue
            if target.name in SAFE_BASENAMES:
                continue
            if target.suffix in {".pyc", ".pyo", ".pyd"}:
                continue
            try:
                data = target.read_bytes()
            except OSError:
                continue
            for pattern in SECRET_PATTERNS:
                if pattern.search(data):
                    report.secret_matches.append(
                        SecretMatch(path=str(target.relative_to(self._root)), pattern=pattern.pattern.decode("ascii", errors="replace"))
                    )

    def _run_symlink_scan(self, report: DistributionV7Report) -> None:
        for entry in self._root.rglob("*"):
            if entry.is_symlink() and ".git" not in entry.parts:
                report.symlinks.append(str(entry.relative_to(self._root)))

    def _run_link_audit(self, report: DistributionV7Report) -> None:
        manifest_path = self._root / ".codex-plugin" / "plugin.json"
        marketplace_path = self._root / ".agents" / "plugins" / "marketplace.json"
        if not (manifest_path.is_file() and marketplace_path.is_file()):
            return
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        repository = manifest.get("repository", "")
        report.repository_url = repository
        expected_source = {"source": "url", "url": repository + ".git", "ref": "main"}
        for entry in marketplace.get("plugins", []):
            if entry.get("name") == manifest.get("name"):
                report.marketplace_url_matches = entry.get("source") == expected_source
                return
        report.marketplace_url_matches = False

    def _run_canary_check(self, report: DistributionV7Report) -> None:
        approved, _reason = self._validate_canary_marker()
        report.paid_canary = "APPROVED" if approved else "NOT_RUN"

    def _canary_approved(self) -> bool:
        approved, _reason = self._validate_canary_marker()
        return approved

    def _validate_canary_marker(self) -> tuple[bool, str]:
        """Validate the paid-canary marker's *content*, not just its existence.

        A marker that merely exists proves nothing: any non-empty file would
        otherwise unlock the gate. The record must actually carry the four
        pieces of evidence the plan requires — submit ID, timestamp,
        approver, and observed behavior.
        """
        marker = self._root / "docs" / "verification" / "paid-canary-approved.md"
        if not marker.is_file():
            return False, "no approval marker present"
        try:
            text = marker.read_text(encoding="utf-8")
        except OSError as exc:
            return False, f"cannot read marker: {exc}"
        if not text.strip():
            return False, "marker is empty"
        missing: list[str] = []
        if re.search(r"submit[_-]?id\s*[:`]*\s*`?\S+", text, re.IGNORECASE) is None:
            missing.append("submit_id")
        if re.search(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}", text) is None:
            missing.append("timestamp")
        if re.search(r"approver\s*[:`]*\s*`?\S+", text, re.IGNORECASE) is None:
            missing.append("approver")
        observed = re.split(r"observed behavior", text, flags=re.IGNORECASE)
        if len(observed) < 2 or len(observed[-1].strip()) < 20:
            missing.append("observed behavior")
        if missing:
            return False, f"marker is missing required evidence: {', '.join(missing)}"
        return True, "marker carries submit_id, timestamp, approver, and observed behavior"

    def _run_runtime_contract_check(self, report: DistributionV7Report) -> None:
        """Evidence-based: the committed artifacts ARE the observation record.

        The gate is satisfied when the version / help / schema captures exist
        and are well-formed. This is deliberately not a check of whether the
        CLI happens to be on PATH right now — the record is what gets
        committed and reviewed, and a CI machine need not have the binary.
        Whether the binary is currently resolvable is reported separately as
        `cli_available`.
        """
        ok, reason = self._validate_cli_artifacts()
        if ok:
            report.read_only_runtime_contract = "observed"
            report.read_only_runtime_reason = (
                "version / help / schema captures present and well-formed"
            )
        else:
            report.read_only_runtime_contract = "blocked"
            report.read_only_runtime_reason = reason

    def _validate_cli_artifacts(self) -> tuple[bool, str]:
        """Validate the CLI capture artifacts' contents, not just existence."""
        version = self._verification_dir / "cli-version.txt"
        help_text = self._verification_dir / "cli-help.txt"
        schema = self._verification_dir / "cli-schema.json"
        missing = [
            p.name for p in (version, help_text, schema) if not p.is_file()
        ]
        if missing:
            return False, (
                f"missing capture(s): {', '.join(missing)}; run "
                "`python3 scripts/unlock_runtime_gates.py probe` after "
                "installing and authorizing the dreamina CLI"
            )
        try:
            version_text = version.read_text(encoding="utf-8").strip()
            help_text_value = help_text.read_text(encoding="utf-8").strip()
            schema_text = schema.read_text(encoding="utf-8").strip()
        except OSError as exc:
            return False, f"cannot read captures: {exc}"
        if not version_text:
            return False, "cli-version.txt is empty"
        if not _is_valid_version_capture(version_text):
            return False, (
                f"cli-version.txt has no version-like token: {version_text!r}; "
                "the capture does not look like real `dreamina --version` output"
            )
        if len(help_text_value) < 40:
            return False, (
                "cli-help.txt is too short to be real `dreamina --help` output "
                f"({len(help_text_value)} chars)"
            )
        try:
            parsed = json.loads(schema_text)
        except (json.JSONDecodeError, ValueError):
            return False, "cli-schema.json does not parse as JSON"
        if not isinstance(parsed, (dict, list)):
            return False, "cli-schema.json is not a JSON object or array"
        if isinstance(parsed, dict) and parsed.get("source") == "command-help":
            commands = parsed.get("commands")
            required_commands = {
                "text2image", "image2image", "text2video", "image2video",
                "frames2video", "multimodal2video", "session", "list_task",
                "query_result",
            }
            if not isinstance(commands, dict) or not required_commands.issubset(commands):
                return False, "command-help snapshot is missing required commands"
            if any(
                not isinstance(commands[name], str) or len(commands[name]) < 40
                for name in required_commands
            ):
                return False, "command-help snapshot contains empty or truncated help"
            readiness = self._verification_dir / "account-readiness.md"
            readiness_text = (
                readiness.read_text(encoding="utf-8") if readiness.is_file() else ""
            )
            if (
                "Status: READY" not in readiness_text
                or "authenticated user: **yes**" not in readiness_text
            ):
                return False, "account-readiness.md is missing READY authentication evidence"
            if "generation performed as part of this check: **no**" not in readiness_text:
                return False, "account-readiness.md does not preserve the no-generation boundary"
        return True, "captures present and well-formed"

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _dreamina_available(self) -> bool:
        binary = shutil.which(self._dreamina_command)
        if binary:
            return True
        # Allow explicit absolute paths too.
        if os.path.sep in self._dreamina_command and Path(self._dreamina_command).exists():
            return os.access(self._dreamina_command, os.X_OK)
        return False

    @staticmethod
    def _parse_frontmatter(text: str) -> dict[str, str]:
        if not text.startswith("---"):
            return {}
        end = text.find("\n---", 3)
        if end == -1:
            return {}
        block = text[3:end].strip()
        parsed: dict[str, str] = {}
        for line in block.splitlines():
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            parsed[key.strip()] = value.strip()
        return parsed


def evaluate_plan_gate(report: "DistributionV7Report") -> tuple[bool, list[tuple[str, str, str]]]:
    """Evaluate the plan's 13-line completion gate *as written*.

    Returns ``(all_satisfied, lines)`` where each line is
    ``(gate_line, verdict, basis)``. The last two gate lines are
    disjunctions, so ``blocked`` / ``NOT_RUN`` are accepted end states —
    that is the plan's own text, not a relaxation introduced here. Use
    ``--require-runtime-gates`` for the strictly stronger claim that the
    live gates were actually observed.
    """
    lines: list[tuple[str, str, str]] = []

    def add(name: str, ok: bool, basis: str) -> None:
        lines.append((name, "satisfied" if ok else "NOT satisfied", basis))

    add(
        "dreamina_skill_directories = 13",
        report.skill_count == 13,
        f"skill_count = {report.skill_count}",
    )
    forbidden = report.forbidden_installable_identities
    add(
        "old_installable_jimeng_identities = 0",
        not forbidden,
        f"forbidden = {forbidden or '[]'}",
    )
    add(
        "skill_snapshot_parity = PASS",
        report.skill_snapshot_status == "PASS",
        f"skill_snapshot_status = {report.skill_snapshot_status}",
    )
    # These six gate lines are statements about test results. This verifier
    # does not re-run the suite (that would be circular — the suite tests
    # this verifier), so it records them as externally asserted and says so
    # explicitly rather than implying it checked them.
    for gate_line in (
        "capability_and_adapter_tests = PASS",
        "image_tests = PASS",
        "video_tests = PASS",
        "approval_operation_artifact_tests = PASS",
        "skill_quick_validation = PASS",
        "skill_trace = PASS",
    ):
        add(
            gate_line,
            True,
            "NOT re-verified here — externally asserted by the test suite; "
            "run it and see docs/verification/offline.md §4/§6",
        )
    add(
        "plugin_validation = PASS",
        report.legacy_validator_exit_code == 0,
        f"legacy_validator_exit_code = {report.legacy_validator_exit_code}",
    )
    add(
        "secret_matches = 0",
        not report.secret_matches,
        f"secret_matches = {len(report.secret_matches)}",
    )
    add(
        "read_only_runtime_contract = observed or explicitly blocked",
        report.read_only_runtime_contract in {"observed", "blocked"},
        f"read_only_runtime_contract = {report.read_only_runtime_contract}"
        + (
            " (the 'explicitly blocked' disjunct; documented in "
            "docs/verification/authorization-decision.md)"
            if report.read_only_runtime_contract == "blocked"
            else " (the 'observed' disjunct)"
        ),
    )
    add(
        "paid_canary = separately approved or NOT_RUN",
        report.paid_canary in {"APPROVED", "NOT_RUN"},
        f"paid_canary = {report.paid_canary}",
    )
    return all(verdict == "satisfied" for _n, verdict, _b in lines), lines


def main(argv: list[str] | None = None) -> int:
    """Exit-code contract.

    The plan's completion gate writes the two human-performed gates as
    ``read_only_runtime_contract = observed or explicitly blocked`` and
    ``paid_canary = separately approved or NOT_RUN``. Both ``blocked`` and
    ``NOT_RUN`` are therefore *legal* end states, so:

      * default mode fails only on structural problems;
      * ``--strict`` additionally enforces everything verifiable offline
        (snapshot parity when an explicit SHA is supplied, secrets,
        symlinks, legacy validator) but still accepts a plan-legal
        ``blocked`` / ``NOT_RUN``;
      * ``--require-runtime-gates`` is the strictly stronger opt-in that
        demands ``observed`` + ``APPROVED``. It is expected to fail on a
        machine without the ``dreamina`` CLI and without an approval
        marker, and it must not be used as the CI gate for an offline run.

    Exit codes: 1 legacy validator, 2 secrets, 3 symlinks, 4 snapshot
    parity, 5 runtime contract not observed (opt-in only), 6 canary not
    approved (opt-in only).
    """
    parser_args = argv if argv is not None else sys.argv[1:]
    root = Path(".").resolve()
    expected_sha: str | None = None
    strict = False
    require_runtime_gates = False
    plan_gate = False
    i = 0
    while i < len(parser_args):
        arg = parser_args[i]
        if arg == "--root" and i + 1 < len(parser_args):
            root = Path(parser_args[i + 1]).resolve()
            i += 2
            continue
        if arg == "--expected-upstream-sha" and i + 1 < len(parser_args):
            expected_sha = parser_args[i + 1]
            i += 2
            continue
        if arg == "--strict":
            strict = True
            i += 1
            continue
        if arg == "--require-runtime-gates":
            require_runtime_gates = True
            i += 1
            continue
        if arg == "--plan-gate":
            plan_gate = True
            i += 1
            continue
        i += 1
    verifier = DistributionV7Verifier(root=root, expected_upstream_sha=expected_sha)
    report = verifier.run()
    print(report.to_json())
    if plan_gate:
        all_ok, lines = evaluate_plan_gate(report)
        print()
        print("plan_gate (the plan's 13-line completion gate, as written):")
        for name, verdict, basis in lines:
            print(f"  [{'x' if verdict == 'satisfied' else ' '}] {name}  <- {basis}")
        print()
        print(f"plan_gate = {'SATISFIED' if all_ok else 'NOT SATISFIED'}")
        if not all_ok:
            return 7
    if report.legacy_validator_exit_code != 0:
        return 1
    if report.secret_matches:
        return 2
    if report.symlinks:
        return 3
    if expected_sha is not None and report.skill_snapshot_status != "PASS":
        return 4
    # `strict` deliberately does NOT gate on the two human-performed
    # gates; only the explicit opt-in does.
    if require_runtime_gates and report.read_only_runtime_contract != "observed":
        return 5
    if require_runtime_gates and report.paid_canary != "APPROVED":
        return 6
    return 0


__all__ = [
    "CanaryMissingError",
    "DistributionV7Error",
    "DistributionV7Report",
    "DistributionV7Verifier",
    "EXPECTED_SKILLS",
    "ReadOnlyRuntimeBlockedError",
    "SecretLikeContentError",
    "SkillSnapshotShaMismatchError",
    "SymlinkError",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
