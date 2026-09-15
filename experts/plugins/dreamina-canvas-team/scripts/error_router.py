"""Stable exit-code → typed next-action routing for dreamina-canvas.

Maps each documented exit code to a typed action. Localized message
text is NEVER branched on; the routing key is the numeric exit code plus
`error.requiredAction`.
"""

from __future__ import annotations

from dataclasses import dataclass


# Stable routing decisions. These names are also used by tests and by the
# Skill scenarios so they form the public surface of the router.
class Action:
    CONTINUE = "continue"
    FIX_AND_RETRY = "fix_and_retry"
    ALERT = "alert"
    APPROVAL_PAUSE = "approval_pause"
    REAUTH_AND_RETRY = "reauth_and_retry"
    ESCALATE = "escalate"
    UPGRADE_CLI = "upgrade_cli"
    RESUME_OPERATION = "resume_operation"
    BOUNDED_BACKOFF_RETRY = "bounded_backoff_retry"
    HAND_TO_HUMAN = "hand_to_human"


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str


# Plan Task 3 Step 4 mapping.
ROUTING_TABLE: dict[int, Decision] = {
    0: Decision(Action.CONTINUE, "success"),
    1: Decision(Action.ALERT, "uncategorized internal failure"),
    2: Decision(Action.FIX_AND_RETRY, "invalid command, argument, or schema"),
    10: Decision(Action.APPROVAL_PAUSE, "structured credit approval required"),
    11: Decision(Action.REAUTH_AND_RETRY, "login required or session expired"),
    12: Decision(Action.ESCALATE, "permission / capability / entitlement denied"),
    13: Decision(Action.UPGRADE_CLI, "environment or release compatibility blocked"),
    20: Decision(Action.RESUME_OPERATION, "operation recoverable, not converged"),
    21: Decision(Action.BOUNDED_BACKOFF_RETRY, "retryable service / transport failure"),
    22: Decision(Action.HAND_TO_HUMAN, "human intervention required"),
}


def route(exit_code: int) -> Decision:
    """Return the typed next-step decision for an exit code."""
    return ROUTING_TABLE.get(exit_code, Decision(Action.ALERT, f"unknown exit {exit_code}"))
