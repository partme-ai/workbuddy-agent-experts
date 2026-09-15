#!/usr/bin/env python3
"""Evaluate a batch round and record the verdict.

The single design rule here is that a machine verdict and a model verdict are not
the same kind of thing, so they are not given the same authority.

Deterministic gates decide. They answer questions with one true answer: did a file
appear, is it a PNG, is it large enough, does its hash match the receipt, is the
same image standing in for two different items. A batch fails on these alone.

A model-authored score is advisory. This module never calls a model; if a score is
supplied it is recorded and compared against the threshold, and a low score asks
for a human rather than failing the batch. Making a model's opinion authoritative
would mean an optimizer tuning against its own judge, which is how a loop drifts
somewhere the operator never asked for.

A human decision outranks both, because it is the only signal that is actually
about the desired result. Human labels are recorded next to the scores so the
advisory signal can later be calibrated against real decisions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from artifact_collector import file_sha256, parse_png_size

SCHEMA_VERSION = "1.0.0"
HUMAN_LABELS = ("approved", "rejected", "unlabeled")
DECISIONS = ("pass", "fail", "pending_approval")


@dataclass(frozen=True)
class EvaluationResult:
    ok: bool
    scores: dict
    errors: tuple[str, ...] = ()


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _gate(
    receipt: dict | None,
    destination_dir: Path,
    min_dimension: int,
) -> tuple[str, ...]:
    if receipt is None:
        return ("missing_artifact",)
    target = destination_dir / str(receipt.get("path", ""))
    if not target.is_file():
        return ("missing_artifact",)

    failures: list[str] = []
    size = parse_png_size(target)
    if size is None:
        failures.append("not_a_png")
    elif size[0] < min_dimension or size[1] < min_dimension:
        failures.append("below_min_dimension")
    if file_sha256(target) != receipt.get("sha256"):
        failures.append("hash_mismatch")
    return tuple(failures)


def _validate_advisory(advisory: dict, known: set[str]) -> None:
    for item_id, entry in advisory.items():
        if item_id not in known:
            raise ValueError(f"advisory score given for unknown item {item_id!r}")
        score = entry[0] if isinstance(entry, (tuple, list)) else entry
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise ValueError(f"advisory score for {item_id!r} must be a number")
        if not 0.0 <= float(score) <= 1.0:
            raise ValueError(f"advisory score for {item_id!r} must be between 0 and 1")


def _validate_labels(labels: dict, known: set[str]) -> None:
    for item_id, label in labels.items():
        if item_id not in known:
            raise ValueError(f"label given for unknown item {item_id!r}")
        if label not in HUMAN_LABELS:
            raise ValueError(f"label for {item_id!r} must be one of {HUMAN_LABELS}")


def evaluate_batch(
    *,
    batch_id: str,
    round_number: int,
    items,
    receipts: dict,
    destination_dir: Path,
    min_dimension: int,
    reject_duplicates: bool,
    pass_threshold: float,
    advisory_enabled: bool,
    require_human_labels: bool,
    advisory: dict | None = None,
    human_labels: dict | None = None,
) -> EvaluationResult:
    destination_dir = Path(destination_dir)
    advisory = dict(advisory or {})
    human_labels = dict(human_labels or {})
    known = {item.id for item in items}
    _validate_advisory(advisory, known)
    _validate_labels(human_labels, known)

    item_ids = [item.id for item in items]
    gates: dict[str, tuple[str, ...]] = {}
    hashes: dict[str, str | None] = {}

    for item in items:
        receipt = receipts.get(item.id)
        gates[item.id] = _gate(receipt, destination_dir, min_dimension)
        resolved = destination_dir / str(receipt.get("path", "")) if receipt else None
        hashes[item.id] = (
            file_sha256(resolved) if resolved is not None and resolved.is_file() else None
        )

    if reject_duplicates:
        counts: dict[str, int] = {}
        for digest in hashes.values():
            if digest is not None:
                counts[digest] = counts.get(digest, 0) + 1
        for item_id, digest in hashes.items():
            if digest is not None and counts.get(digest, 0) > 1:
                gates[item_id] = gates[item_id] + ("duplicate_content",)

    per_item = [
        {"item_id": item_id, "passed": not gates[item_id], "failures": list(gates[item_id])}
        for item_id in item_ids
    ]
    all_passed = all(row["passed"] for row in per_item)

    advisory_items = []
    for item_id in item_ids:
        if item_id not in advisory:
            continue
        entry = advisory[item_id]
        score, reason = (entry if isinstance(entry, (tuple, list)) else (entry, ""))
        advisory_items.append({"item_id": item_id, "score": float(score), "reason": str(reason)})

    label_rows = []
    for item_id in item_ids:
        label = human_labels.get(item_id, "unlabeled")
        label_rows.append(
            {
                "item_id": item_id,
                "label": label,
                "at": _timestamp() if label != "unlabeled" else None,
            }
        )

    rejected = any(row["label"] == "rejected" for row in label_rows)
    unlabeled = any(row["label"] == "unlabeled" for row in label_rows)
    below_threshold = any(row["score"] < pass_threshold for row in advisory_items)

    if not all_passed:
        decision = "fail"
    elif rejected:
        decision = "fail"
    elif require_human_labels and unlabeled:
        decision = "pending_approval"
    elif advisory_enabled and below_threshold:
        decision = "pending_approval"
    else:
        decision = "pass"

    scores = {
        "schema_version": SCHEMA_VERSION,
        "batch_id": batch_id,
        "round": round_number,
        "pass_threshold": pass_threshold,
        "deterministic_gates": {"all_passed": all_passed, "per_item": per_item},
        "advisory": {"enabled": advisory_enabled, "items": advisory_items},
        "human_labels": label_rows,
        "decision": decision,
    }
    # `ok` means "nothing is wrong with this batch". A pending approval is not a
    # failure: the artifacts are sound and a person still has to look at them.
    return EvaluationResult(ok=decision in ("pass", "pending_approval"), scores=scores)


def render_scores(result: EvaluationResult) -> str:
    return json.dumps(result.scores, indent=2, sort_keys=True)
