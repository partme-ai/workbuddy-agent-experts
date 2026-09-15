"""Harness for the two runtime gates that require human action.

The implementation plan defines two gates that a human must satisfy in
their own authorized shell:

* ``read_only_runtime_contract`` — install + authorize the ``dreamina``
  CLI, then capture ``--version`` / ``--help`` / ``schema`` and record
  account readiness without performing any generation.
* ``paid_canary`` — interactively run one real image or video
  generation and record the submit ID, approver, and observed behavior.

This harness automates the mechanical parts of those steps **for the
human to run**, and enforces the plan's anti-fabrication boundary:

* ``probe`` refuses to write anything when ``dreamina`` is not on PATH.
  It never invents version / help / schema output.
* ``record-canary`` refuses placeholder-looking submit IDs and requires
  every field. It never invents a submit ID, timestamp, or approver.
* ``status`` reports the current gate state without mutating anything.

Usage (run these yourself in your own authorized shell):

    # 1. After installing + authorizing the dreamina CLI:
    python3 scripts/unlock_runtime_gates.py probe

    # 2. Fill in docs/verification/account-readiness.md by hand.

    # 3. Interactively run one low-cost generation, then:
    python3 scripts/unlock_runtime_gates.py record-canary \\
        --submit-id <real-submit-id> \\
        --approver <your-name> \\
        --observed "<one paragraph on what you saw>"

    # 4. Re-run the distribution verifier:
    python3 scripts/validate_distribution_v7.py --strict
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


# Placeholder-looking submit IDs are rejected outright. A real Dreamina
# submit ID is a server-issued identifier; none of these strings can be
# one.
PLACEHOLDER_TOKENS = (
    "tbd",
    "placeholder",
    "fake",
    "test",
    "unknown",
    "xxx",
    "todo",
    "not_run",
    "not-run",
    "example",
    "dummy",
    "sample",
)

CAPABILITY_COMMANDS = (
    "text2image",
    "image2image",
    "text2video",
    "image2video",
    "frames2video",
    "multimodal2video",
    "session",
    "list_task",
    "query_result",
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


def _version_label(version_text: str) -> str:
    """Extract a compact human-readable version label from captured output."""
    try:
        payload = json.loads(version_text)
    except (json.JSONDecodeError, ValueError):
        payload = None
    if isinstance(payload, dict) and isinstance(payload.get("version"), str):
        return payload["version"].strip()
    parts = version_text.split()
    return parts[-1] if parts else "unknown"


class UnlockError(Exception):
    """Base class for unlock harness errors."""


class CLIAbsentError(UnlockError):
    """The dreamina CLI is not available; refusing to fabricate output."""


class IncompleteCanaryRecordError(UnlockError):
    """The canary record is missing fields or uses a placeholder value."""


class UnlockHarness:
    """Drive the human-performed runtime gate steps without fabricating."""

    def __init__(self, *, verification_dir: Path, cli_command: str = "dreamina") -> None:
        self._verification_dir = Path(verification_dir)
        self._cli_command = cli_command

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def status(self) -> dict:
        cli_ok = self._cli_available()
        artifacts_ok, artifacts_reason = self._validate_artifacts()
        canary_ok, canary_reason = self._validate_canary()
        return {
            "cli_available": cli_ok,
            "cli_command": self._cli_command,
            "read_only_runtime_contract": "observed" if artifacts_ok else "blocked",
            "read_only_runtime_reason": artifacts_reason,
            "paid_canary": "APPROVED" if canary_ok else "NOT_RUN",
            "paid_canary_reason": canary_reason,
            "verification_dir": str(self._verification_dir),
        }

    def _validate_artifacts(self) -> tuple[bool, str]:
        """Mirror the v7 verifier's content checks so both agree.

        Existence alone is not evidence: empty or malformed captures must not
        report the gate as satisfied.
        """
        version = self._verification_dir / "cli-version.txt"
        help_text = self._verification_dir / "cli-help.txt"
        schema = self._verification_dir / "cli-schema.json"
        missing = [p.name for p in (version, help_text, schema) if not p.is_file()]
        if missing:
            return False, f"missing capture(s): {', '.join(missing)}"
        try:
            version_text = version.read_text(encoding="utf-8").strip()
            help_value = help_text.read_text(encoding="utf-8").strip()
            schema_text = schema.read_text(encoding="utf-8").strip()
        except OSError as exc:
            return False, f"cannot read captures: {exc}"
        if not version_text:
            return False, "cli-version.txt is empty"
        if not _is_valid_version_capture(version_text):
            return False, f"cli-version.txt has no version-like token: {version_text!r}"
        if len(help_value) < 40:
            return False, f"cli-help.txt too short ({len(help_value)} chars)"
        try:
            parsed = json.loads(schema_text)
        except (json.JSONDecodeError, ValueError):
            return False, "cli-schema.json does not parse as JSON"
        if not isinstance(parsed, (dict, list)):
            return False, "cli-schema.json is not a JSON object or array"
        if isinstance(parsed, dict) and parsed.get("source") == "command-help":
            commands = parsed.get("commands")
            if not isinstance(commands, dict) or not set(CAPABILITY_COMMANDS).issubset(commands):
                return False, "command-help snapshot is missing required commands"
            if any(
                not isinstance(commands[name], str) or len(commands[name]) < 40
                for name in CAPABILITY_COMMANDS
            ):
                return False, "command-help snapshot contains empty or truncated help"
            readiness = self._verification_dir / "account-readiness.md"
            readiness_text = readiness.read_text(encoding="utf-8") if readiness.is_file() else ""
            if "Status: READY" not in readiness_text or "authenticated user: **yes**" not in readiness_text:
                return False, "account-readiness.md is missing READY authentication evidence"
            if "generation performed as part of this check: **no**" not in readiness_text:
                return False, "account-readiness.md does not preserve the no-generation boundary"
        return True, "captures present and well-formed"

    def _validate_canary(self) -> tuple[bool, str]:
        """Mirror the v7 verifier's canary content checks."""
        marker = self._verification_dir / "paid-canary-approved.md"
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
            return False, f"marker missing required evidence: {', '.join(missing)}"
        return True, "marker carries submit_id, timestamp, approver, observed behavior"

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self) -> dict:
        """Capture version / help / schema from the real CLI.

        Raises :class:`CLIAbsentError` when the CLI is unavailable. In
        that case **nothing is written** — no synthetic outputs, no
        placeholder files.
        """
        binary = self._resolve_cli()
        version = self._run([binary, "--version"])
        help_text = self._run([binary, "--help"])
        try:
            schema = self._run([binary, "schema"])
        except UnlockError as exc:
            if 'unknown command "schema"' not in str(exc):
                raise
            command_help = {}
            for command in CAPABILITY_COMMANDS:
                if re.search(rf"(?m)^\s{{2}}{re.escape(command)}\s+", help_text):
                    command_help[command] = self._run([binary, command, "--help"])
            schema = json.dumps(
                {"source": "command-help", "commands": command_help},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        self._verification_dir.mkdir(parents=True, exist_ok=True)
        (self._verification_dir / "cli-version.txt").write_text(
            version + "\n", encoding="utf-8"
        )
        (self._verification_dir / "cli-help.txt").write_text(
            help_text + "\n", encoding="utf-8"
        )
        (self._verification_dir / "cli-schema.json").write_text(
            schema + "\n", encoding="utf-8"
        )
        nickname = _version_label(version)
        readiness_path = self._verification_dir / "account-readiness.md"
        if not readiness_path.exists():
            readiness_path.write_text(
                "# Account readiness\n\n"
                f"> Captured {self._now()} from `{binary} --version` = `{nickname}`.\n\n"
                "**Status: PENDING** — fill in the fields below after you have\n"
                "authorized the CLI with your Dreamina account. Do **not** record\n"
                "credentials here; the plan forbids storing tokens, cookies, or\n"
                "account snapshots.\n\n"
                "- authenticated user: \n"
                "- membership tier: \n"
                "- generation performed as part of this check: **no**\n"
                "- captured at: \n",
                encoding="utf-8",
            )
        return {
            "version": version,
            "help_bytes": len(help_text),
            "schema_bytes": len(schema),
        }

    # ------------------------------------------------------------------
    # Canary record
    # ------------------------------------------------------------------
    def record_canary(self, *, submit_id: str, approver: str, observed: str) -> Path:
        """Record a human-performed paid canary.

        Every field is required. Placeholder-looking submit IDs are
        rejected so the harness cannot be used to manufacture a PASS.
        """
        if not submit_id or not approver or not observed:
            raise IncompleteCanaryRecordError(
                "submit_id, approver, and observed are all required"
            )
        lowered = submit_id.strip().lower()
        if any(token in lowered for token in PLACEHOLDER_TOKENS):
            raise IncompleteCanaryRecordError(
                f"submit_id looks like a placeholder ({submit_id!r}); "
                "record the real server-issued submit ID from your generation"
            )
        if len(submit_id.strip()) < 8:
            raise IncompleteCanaryRecordError(
                f"submit_id too short to be a real server-issued id ({submit_id!r})"
            )
        self._verification_dir.mkdir(parents=True, exist_ok=True)
        target = self._verification_dir / "paid-canary-approved.md"
        target.write_text(
            "# Paid canary approval record\n\n"
            "> This file is the record of a **real, human-performed** paid\n"
            "> generation. It was created by the human who ran the generation,\n"
            "> not synthesized by the model.\n\n"
            f"- **submit_id:** `{submit_id.strip()}`\n"
            f"- **timestamp:** {self._now()}\n"
            f"- **approver:** {approver.strip()}\n\n"
            "## Observed behavior\n\n"
            f"{observed.strip()}\n\n"
            "## How this was produced\n\n"
            "1. Installed and authorized the `dreamina` CLI in an\n"
            "   authorized shell.\n"
            "2. Ran one low-cost image or video generation interactively.\n"
            "3. Captured the server-issued submit ID above.\n"
            "4. Ran `python3 scripts/unlock_runtime_gates.py record-canary\n"
            "   --submit-id <id> --approver <name> --observed \"<summary>\"`.\n",
            encoding="utf-8",
        )
        return target

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _cli_available(self) -> bool:
        if os.path.sep in self._cli_command:
            return Path(self._cli_command).is_file() and os.access(self._cli_command, os.X_OK)
        return shutil.which(self._cli_command) is not None

    def _resolve_cli(self) -> str:
        if not self._cli_available():
            raise CLIAbsentError(
                f"{self._cli_command} is not available on this machine; "
                "install and authorize the dreamina CLI in your own shell first. "
                "This harness will not fabricate version/help/schema output."
            )
        if os.path.sep in self._cli_command:
            return self._cli_command
        return shutil.which(self._cli_command) or self._cli_command

    def _artifacts_present(self) -> bool:
        return all(
            (self._verification_dir / name).is_file()
            for name in ("cli-version.txt", "cli-help.txt", "cli-schema.json")
        )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def _run(argv: list[str]) -> str:
        try:
            completed = subprocess.run(  # noqa: S603 — argv-only
                argv,
                capture_output=True,
                text=True,
                timeout=30,
                shell=False,
                check=False,
            )
        except OSError as exc:
            raise CLIAbsentError(f"failed to run {argv[0]}: {exc}") from exc
        if completed.returncode != 0:
            raise UnlockError(
                f"{' '.join(argv)} failed with exit {completed.returncode}: "
                f"{completed.stderr.strip()}"
            )
        return completed.stdout.rstrip("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Drive the human-performed runtime gate steps."
    )
    parser.add_argument(
        "--verification-dir",
        default="docs/verification",
        help="where to write the evidence artifacts (default: docs/verification)",
    )
    parser.add_argument("--cli-command", default="dreamina")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="report current gate state without mutating anything")
    sub.add_parser("probe", help="capture version / help / schema from the real CLI")
    canary = sub.add_parser("record-canary", help="record a real human-performed canary")
    canary.add_argument("--submit-id", required=True)
    canary.add_argument("--approver", required=True)
    canary.add_argument("--observed", required=True)

    args = parser.parse_args(argv)
    harness = UnlockHarness(
        verification_dir=Path(args.verification_dir).resolve(),
        cli_command=args.cli_command,
    )
    try:
        if args.command == "status":
            print(json.dumps(harness.status(), indent=2, sort_keys=True))
            return 0
        if args.command == "probe":
            result = harness.probe()
            print(json.dumps(result, indent=2, sort_keys=True))
            print(
                "\nNext: fill in docs/verification/account-readiness.md, run one "
                "real generation interactively, then `record-canary`."
            )
            return 0
        if args.command == "record-canary":
            target = harness.record_canary(
                submit_id=args.submit_id,
                approver=args.approver,
                observed=args.observed,
            )
            print(f"wrote {target}")
            return 0
    except CLIAbsentError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    except IncompleteCanaryRecordError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3
    except UnlockError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 4
    return 0


__all__ = [
    "CLIAbsentError",
    "IncompleteCanaryRecordError",
    "UnlockError",
    "UnlockHarness",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
