#!/usr/bin/env python3
"""Turn one round's evaluation into the next round's plan.

Optimization here is a decision about *what* to redo, not a text generator. The
plugin decides which items need another attempt and which are finished, and it
requires an explicit instruction for each item it is asked to redo. Rewritten
prompts come from Codex; this module validates and carries them.

That split is what keeps the loop honest. If this module also wrote the prompts,
then the same component would produce the work and judge it, and a loop that
grades its own homework converges on whatever the grader likes rather than on
what the operator asked for.

Three properties are structural rather than policy:

* A new round is a new document. The previous plan is never edited, so the round
  number alone links a result back to the instruction that produced it.
* An item that already passed is not regenerated. Re-running it would spend the
  account's allowance to reproduce a file that already exists.
* Reaching the round ceiling is reported as incomplete, never as success.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

import contract_migrations

DEFAULT_MAX_ROUNDS = 20

NEEDS_WORK_WITHOUT_INSTRUCTION = "optimizer_missing_instruction"
AMBIGUOUS_INSTRUCTION = "optimizer_ambiguous_instruction"
EMPTY_REWRITE = "optimizer_empty_rewrite"
UNEXPECTED_INSTRUCTION = "optimizer_unexpected_instruction"
UNKNOWN_ITEM = "optimizer_unknown_item"
ROUND_CAP_REACHED = "optimizer_round_cap_reached"


@dataclass(frozen=True)
class OptimizeError:
    code: str
    message: str
    item_id: str | None = None


@dataclass(frozen=True)
class OptimizeResult:
    complete: bool
    next_plan: dict | None
    errors: tuple[OptimizeError, ...]
    carried_forward: tuple[str, ...] = ()
    rework: tuple[str, ...] = ()
    blocked: tuple[str, ...] = ()


def _gates_by_item(evaluation: dict) -> dict[str, bool]:
    rows = evaluation.get("deterministic_gates", {}).get("per_item", [])
    return {row["item_id"]: bool(row["passed"]) for row in rows}


def _labels_by_item(evaluation: dict) -> dict[str, str]:
    return {row["item_id"]: row["label"] for row in evaluation.get("human_labels", [])}


def _advisory_by_item(evaluation: dict) -> dict[str, float]:
    return {row["item_id"]: row["score"] for row in evaluation.get("advisory", {}).get("items", [])}


def needs_rework(item_id: str, *, gates: dict, labels: dict, advisory: dict, policy: dict) -> bool:
    if not gates.get(item_id, False):
        return True
    if labels.get(item_id) == "rejected":
        return True
    threshold = policy.get("pass_threshold", 0.8)
    if policy.get("advisory_enabled", False):
        score = advisory.get(item_id)
        if score is not None and score < threshold:
            return True
    return False


def plan_next_round(
    *,
    current_plan: dict,
    evaluation: dict,
    rewrites: dict | None = None,
    retry_unchanged=(),
) -> OptimizeResult:
    rewrites = dict(rewrites or {})
    retry_unchanged = set(retry_unchanged)

    rows = list(current_plan.get("items", []))
    identifiers = [row["id"] for row in rows]
    known = set(identifiers)

    instructed = set(rewrites) | retry_unchanged
    unknown = sorted(instructed - known)
    if unknown:
        return OptimizeResult(
            complete=False,
            next_plan=None,
            errors=(
                OptimizeError(
                    UNKNOWN_ITEM,
                    f"instructions were given for items that are not in this plan: {', '.join(unknown)}",
                ),
            ),
        )

    policy = current_plan.get("judge_policy") or {}
    gates = _gates_by_item(evaluation)
    labels = _labels_by_item(evaluation)
    advisory = _advisory_by_item(evaluation)

    rework_ids = [
        item_id
        for item_id in identifiers
        if needs_rework(item_id, gates=gates, labels=labels, advisory=advisory, policy=policy)
    ]
    carried = [item_id for item_id in identifiers if item_id not in set(rework_ids)]

    errors: list[OptimizeError] = []

    unexpected = sorted(instructed & (known - set(rework_ids)))
    if unexpected:
        errors.append(
            OptimizeError(
                UNEXPECTED_INSTRUCTION,
                f"instructions were given for items that already passed: {', '.join(unexpected)}",
            )
        )

    ambiguous = sorted(set(rewrites) & retry_unchanged)
    if ambiguous:
        errors.append(
            OptimizeError(
                AMBIGUOUS_INSTRUCTION,
                f"both a rewrite and a retry-unchanged were given for: {', '.join(ambiguous)}",
            )
        )

    blank = sorted(item_id for item_id, text in rewrites.items() if not str(text).strip())
    if blank:
        errors.append(
            OptimizeError(EMPTY_REWRITE, f"a rewrite was empty for: {', '.join(blank)}")
        )

    silent = [item_id for item_id in rework_ids if item_id not in instructed]
    if silent:
        errors.append(
            OptimizeError(
                NEEDS_WORK_WITHOUT_INSTRUCTION,
                "each item that needs rework must be given a rewrite or an explicit "
                f"retry-unchanged: {', '.join(silent)}",
            )
        )

    if errors:
        return OptimizeResult(
            complete=False,
            next_plan=None,
            errors=tuple(errors),
            carried_forward=tuple(carried),
            rework=tuple(rework_ids),
        )

    limits = current_plan.get("limits") or {}
    max_rounds = limits.get("max_rounds", DEFAULT_MAX_ROUNDS)
    current_round = current_plan.get("round", 1)
    if current_round + 1 > max_rounds:
        return OptimizeResult(
            complete=False,
            next_plan=None,
            errors=(
                OptimizeError(
                    ROUND_CAP_REACHED,
                    f"round {current_round + 1} would exceed the cap of {max_rounds}; "
                    "the remaining items are left for a human decision",
                ),
            ),
            carried_forward=tuple(carried),
            rework=tuple(rework_ids),
            blocked=tuple(rework_ids),
        )

    if not rework_ids:
        return OptimizeResult(complete=True, next_plan=None, errors=(), carried_forward=tuple(carried))

    rework_set = set(rework_ids)
    items = []
    for row in rows:
        if row["id"] not in rework_set:
            continue
        replacement = copy.deepcopy(row)
        if row["id"] in rewrites:
            replacement["prompt"] = str(rewrites[row["id"]]).strip()
        items.append(replacement)

    next_plan: dict = {
        "schema_version": current_plan.get("schema_version", "1.0.0"),
        "batch_id": current_plan["batch_id"],
        "round": current_round + 1,
        "items": items,
    }
    if "goal" in current_plan:
        next_plan["goal"] = current_plan["goal"]
    if "limits" in current_plan:
        next_plan["limits"] = copy.deepcopy(current_plan["limits"])
    if "judge_policy" in current_plan:
        next_plan["judge_policy"] = copy.deepcopy(current_plan["judge_policy"])
    next_plan = contract_migrations.migrate_image_batch(next_plan).document

    return OptimizeResult(
        complete=False,
        next_plan=next_plan,
        errors=(),
        carried_forward=tuple(carried),
        rework=tuple(rework_ids),
    )
