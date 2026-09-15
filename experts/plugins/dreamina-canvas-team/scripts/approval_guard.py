"""Approval guard for dreamina-canvas paid execution.

Mirrors the rules in the upstream quote-and-run Skill:

- No quote (confirmable=false) → refuse.
- --credit-ceiling below the latest authoritative total → refuse.
- The set of nodeIds in the approval must equal the set being run;
  switching nodes invalidates the token.
- The token is bound to a projectId; switching project invalidates the token.
- --credit-ceiling must be re-validated against the latest quote; the
  approval is invalidated by a request that exceeds the ceiling.
- Replaying an approval that was already used is rejected (replay).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Quote:
    project_id: str
    ordered_node_ids: tuple[str, ...]
    total_max_credits: int
    ceiling: int | None  # minimumCreditCeiling from server, None means unknown
    confirmable: bool


@dataclass(frozen=True)
class Approval:
    project_id: str
    ordered_node_ids: tuple[str, ...]
    ceiling: int
    used: bool = False


@dataclass(frozen=True)
class RunRequest:
    project_id: str
    ordered_node_ids: tuple[str, ...]
    latest_total: int


@dataclass
class Decision:
    ok: bool
    reason: str = ""


def check_approval(quote: Quote, approval: Approval, run: RunRequest) -> Decision:
    if not quote.confirmable:
        return Decision(False, "quote.confirmable=false; no token can be issued")
    if approval.used:
        return Decision(False, "approval has already been used")
    if approval.project_id != quote.project_id:
        return Decision(False, "approval.project_id does not match quote.project_id")
    if approval.project_id != run.project_id:
        return Decision(False, "run.project_id does not match approval.project_id")
    if set(approval.ordered_node_ids) != set(quote.ordered_node_ids):
        return Decision(False, "approval.ordered_node_ids does not match quote")
    if set(run.ordered_node_ids) != set(approval.ordered_node_ids):
        return Decision(False, "run.ordered_node_ids does not match approval")
    if approval.ceiling < quote.total_max_credits:
        return Decision(False, "approval.ceiling below quote.totalMaxCredits")
    if run.latest_total > approval.ceiling:
        return Decision(False, "latest authoritative quote exceeds approved ceiling")
    return Decision(True)


def mark_used(approval: Approval) -> Approval:
    return Approval(
        project_id=approval.project_id,
        ordered_node_ids=approval.ordered_node_ids,
        ceiling=approval.ceiling,
        used=True,
    )
