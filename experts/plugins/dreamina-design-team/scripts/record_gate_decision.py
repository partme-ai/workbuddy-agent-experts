"""Record the owner's decision to accept the plan's blocked/NOT_RUN branch.

The plan's completion gate ends with two disjunctions:

    read_only_runtime_contract = observed or explicitly blocked
    paid_canary = separately approved or NOT_RUN

Option (b) — observing the live CLI and running a paid canary — has a
mechanism (``unlock_runtime_gates.py probe`` / ``record-canary``). Option
(a) — accepting the second disjunct as the closing state — had none, so
the owner would have had to hand-edit prose.

This tool gives (a) the same shape: **the human supplies the decision**,
the tool only records it. It refuses to run without an explicit,
non-placeholder approver, so the assistant cannot generate its own
acceptance record, and it never writes wording that claims the gates were
observed or approved.

Usage, run by the repository owner in their own shell:

    python3 scripts/record_gate_decision.py accept-blocked \
        --approver <your-name> \
        --reason "<why the live-runtime evidence is deferred>"
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path


# An acceptance record must name a human. These strings cannot be one.
PLACEHOLDER_APPROVERS = (
    "tbd",
    "todo",
    "model",
    "assistant",
    "agent",
    "ai",
    "test",
    "unknown",
    "n/a",
    "na",
    "none",
    "xxx",
    "example",
    "placeholder",
)


DECISION_MARKER_NAME = "gate-decision-accepted.md"

# Exact audit rows to rewrite, and what they become. The replacement wording
# is deliberately "owner-accepted ... via the <disjunct> disjunct" so it can
# never be mistaken for "observed" / "APPROVED".
OLD_ROWS = (
    "| `read_only_runtime_contract observed or blocked` | \u2705 BLOCKED      | "
    "\u00a72 + `docs/verification/dreamina-cli-runtime.md` + "
    "`docs/verification/authorization-decision.md` |",
    "| `paid_canary = separately approved or NOT_RUN`  | \u2705 NOT_RUN      | "
    "\u00a72 canary gate + `docs/verification/authorization-decision.md` |",
)

NEW_ROWS = (
    "| `read_only_runtime_contract observed or blocked` | \u2705 owner-accepted | "
    "satisfied via the **explicitly blocked** disjunct; "
    "`docs/verification/gate-decision-accepted.md` |",
    "| `paid_canary = separately approved or NOT_RUN`  | \u2705 owner-accepted | "
    "satisfied via the **NOT_RUN** disjunct; "
    "`docs/verification/gate-decision-accepted.md` |",
)


class GateDecisionError(Exception):
    """Base class for gate decision errors."""


class ApprovalRequiredError(GateDecisionError):
    """No explicit, non-placeholder approver was supplied."""


class AlreadyRecordedError(GateDecisionError):
    """An acceptance decision has already been recorded."""


class GateDecisionRecorder:
    """Record an owner decision, refusing to act as the approver itself."""

    def __init__(self, *, root: Path) -> None:
        self._root = Path(root)
        self._verification = self._root / "docs" / "verification"

    @property
    def marker_path(self) -> Path:
        return self._verification / DECISION_MARKER_NAME

    def accept_blocked(self, *, approver: str, reason: str) -> Path:
        """Record acceptance of the `explicitly blocked` / `NOT_RUN` branch."""
        cleaned = (approver or "").strip()
        if not cleaned:
            raise ApprovalRequiredError(
                "an approver is required; the assistant must not record this "
                "decision on the owner's behalf"
            )
        if cleaned.lower() in PLACEHOLDER_APPROVERS:
            raise ApprovalRequiredError(
                f"approver {cleaned!r} is a placeholder; name the human who "
                "accepted this branch"
            )
        if len(cleaned) < 2:
            raise ApprovalRequiredError(
                f"approver {cleaned!r} is too short to identify a human"
            )
        if self.marker_path.exists():
            raise AlreadyRecordedError(
                f"{self.marker_path} already exists; delete it deliberately "
                "before recording a second decision"
            )

        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self._verification.mkdir(parents=True, exist_ok=True)
        self.marker_path.write_text(
            "# Gate decision — accepted the plan's blocked / NOT_RUN branch\n\n"
            "> Record of a decision made by the repository owner, not by the\n"
            "> assistant. The assistant provides the mechanism; the human\n"
            "> supplies the decision.\n\n"
            f"- **decision:** accept the plan's `explicitly blocked` / `NOT_RUN`\n"
            "  disjunct as the closing state for the runtime gates\n"
            f"- **approver:** {cleaned}\n"
            f"- **timestamp:** {stamp}\n"
            f"- **reason:** {reason.strip()}\n\n"
            "## What this does and does not assert\n\n"
            "The plan's completion gate ends with:\n\n"
            "```text\n"
            "read_only_runtime_contract = observed or explicitly blocked\n"
            "paid_canary = separately approved or NOT_RUN\n"
            "```\n\n"
            "This record asserts the **second** disjunct of each line:\n\n"
            "* `read_only_runtime_contract` is **`explicitly blocked`** — the\n"
            "  blocking is documented in `authorization-decision.md` and\n"
            "  `dreamina-cli-runtime.md`;\n"
            "* `paid_canary` is **`NOT_RUN`** — no paid generation was\n"
            "  performed.\n\n"
            "It does **not** assert that the gates were `observed` or\n"
            "`APPROVED`. Those remain available: install and authorize the\n"
            "`dreamina` CLI, run `scripts/unlock_runtime_gates.py probe`,\n"
            "then `record-canary` with a real submit ID, and the verifier\n"
            "flips both gates automatically with no code change.\n\n"
            "## How this was produced\n\n"
            "```text\n"
            "python3 scripts/record_gate_decision.py accept-blocked \\\n"
            f"    --approver {cleaned} \\\n"
            f'    --reason "{" ".join(reason.split())}"\n'
            "```\n",
            encoding="utf-8",
        )
        self._update_audit_rows()
        return self.marker_path

    def _update_audit_rows(self) -> None:
        offline = self._verification / "offline.md"
        if not offline.is_file():
            return
        text = offline.read_text(encoding="utf-8")
        for old, new in zip(OLD_ROWS, NEW_ROWS):
            if old in text:
                text = text.replace(old, new, 1)
        offline.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Record the owner's acceptance of a plan-allowed terminal state."
    )
    parser.add_argument("--root", default=".", help="repository root")
    sub = parser.add_subparsers(dest="command", required=True)
    accept = sub.add_parser(
        "accept-blocked",
        help="accept the plan's `explicitly blocked` / `NOT_RUN` disjunct",
    )
    accept.add_argument("--approver", required=True, help="the human accepting this")
    accept.add_argument("--reason", required=True, help="why the live evidence is deferred")

    args = parser.parse_args(argv)
    recorder = GateDecisionRecorder(root=Path(args.root).resolve())
    if args.command == "accept-blocked":
        try:
            marker = recorder.accept_blocked(
                approver=args.approver, reason=args.reason
            )
        except ApprovalRequiredError as exc:
            print(f"REFUSED: {exc}", file=sys.stderr)
            return 3
        except AlreadyRecordedError as exc:
            print(f"REFUSED: {exc}", file=sys.stderr)
            return 4
        print(f"recorded {marker}")
        return 0
    return 0


__all__ = [
    "AlreadyRecordedError",
    "ApprovalRequiredError",
    "GateDecisionError",
    "GateDecisionRecorder",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
