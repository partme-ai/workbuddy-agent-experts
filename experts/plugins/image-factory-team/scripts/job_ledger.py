#!/usr/bin/env python3
"""Durable state for one image production job.

The ledger is the reason a batch can be interrupted without being paid for
twice. Every transition is written atomically, so the file on disk is always a
complete older or newer state rather than a torn one, and every batch item is
tracked by its content-derived idempotency key so a resume skips work that is
already done.

Two deliberate restrictions:

* `Failed` is terminal. A failed job is not silently restarted; that requires a
  new job, because an automatic restart is exactly how a bad prompt becomes a
  large bill.
* Anything resembling a credential is refused on both read and write. A ledger is
  meant to be shareable evidence, so it must not be able to hold a secret.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

import contract_migrations
import atomic_json
import schema_lite

SCHEMA_VERSION = "1.1.0"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "factory_job.schema.json"
JOB_ID_PATTERN = r"^[a-z0-9][a-z0-9_-]{2,63}$"
IMAGE_LIMIT_ID = "image_gen"
SHA256_PATTERN = r"^[0-9a-f]{64}$"
ATTEMPT_ID_PATTERN = r"^[0-9a-f]{32}$"

FORBIDDEN_KEYS = frozenset(
    {
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "apikey",
        "password",
        "secret",
        "client_secret",
        "authorization",
        "credit_card",
        "cookie",
    }
)

ERROR_CATEGORIES = (
    "capability_unavailable",
    "codex_missing",
    "quota_exceeded",
    "timeout",
    "generation_failed",
    "artifact_missing",
    "hash_mismatch",
    "duplicate_artifact",
    "plan_invalid",
    "approval_required",
    "job_already_running",
    "recovery_required",
    "unknown",
)


class JobState(str, Enum):
    DRAFT = "Draft"
    PLAN_VALIDATED = "PlanValidated"
    APPROVED = "Approved"
    RUNNING = "Running"
    EVALUATED = "Evaluated"
    PENDING_APPROVAL = "PendingApproval"
    OPTIMIZED = "Optimized"
    ACCEPTED = "Accepted"
    COMPLETED = "Completed"
    PARTIAL = "Partial"
    FAILED = "Failed"
    UNKNOWN = "Unknown"


ITEM_STATES = ("Pending", "Attempting", "Generated", "Failed", "Skipped", "Unknown")
ATTEMPTED_ITEM_STATES = ("Generated", "Failed", "Skipped")

# Legacy compatibility surface for callers that still perform explicit state
# transitions. Production evaluation must finalize through
# JobLedger.record_evaluation_final so evidence and outcome use one write.
ALLOWED_TRANSITIONS: dict[JobState, frozenset[JobState]] = {
    JobState.DRAFT: frozenset({JobState.PLAN_VALIDATED}),
    JobState.PLAN_VALIDATED: frozenset({JobState.APPROVED}),
    JobState.APPROVED: frozenset({JobState.RUNNING}),
    JobState.RUNNING: frozenset(
        {JobState.COMPLETED, JobState.PARTIAL, JobState.UNKNOWN, JobState.FAILED}
    ),
    JobState.COMPLETED: frozenset({JobState.EVALUATED}),
    JobState.PARTIAL: frozenset({JobState.EVALUATED, JobState.PLAN_VALIDATED}),
    JobState.EVALUATED: frozenset(
        {
            JobState.PENDING_APPROVAL,
            JobState.OPTIMIZED,
            JobState.ACCEPTED,
        }
    ),
    JobState.PENDING_APPROVAL: frozenset({JobState.EVALUATED}),
    JobState.OPTIMIZED: frozenset({JobState.PLAN_VALIDATED}),
    JobState.UNKNOWN: frozenset({JobState.COMPLETED, JobState.PARTIAL, JobState.FAILED}),
    JobState.ACCEPTED: frozenset(),
    JobState.FAILED: frozenset(),
}

RESOLVABLE_STATES = frozenset(
    {
        JobState.DRAFT,
        JobState.PLAN_VALIDATED,
        JobState.APPROVED,
        JobState.RUNNING,
        JobState.EVALUATED,
        JobState.OPTIMIZED,
        JobState.UNKNOWN,
    }
)


class LedgerCorruptError(Exception):
    """The ledger is missing, unreadable, or holds something it must never hold."""


class InvalidTransitionError(Exception):
    """The requested state change is not permitted from the current state."""


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_job(job_id: str) -> dict:
    if not isinstance(job_id, str) or not json_pattern_match(job_id, JOB_ID_PATTERN):
        raise ValueError(f"job_id must match {JOB_ID_PATTERN}, got {job_id!r}")
    stamp = _timestamp()
    return {
        "schema_version": SCHEMA_VERSION,
        "job_id": job_id,
        "state": JobState.DRAFT.value,
        "revision": 1,
        "created_at": stamp,
        "updated_at": stamp,
        "batch": None,
        "rounds": [],
        "current_item_keys": [],
        "items": [],
        "approval": {"current": None, "history": []},
        "evaluation": None,
        "optimization": None,
        "usage_limit": None,
        "error_category": None,
        "history": [],
    }


def json_pattern_match(value: str, pattern: str) -> bool:
    import re

    return re.search(pattern, value) is not None


def _scrub(node: object, path: str = "$") -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(key, str) and key.lower() in FORBIDDEN_KEYS:
                raise LedgerCorruptError(
                    f"{path}: refusing to persist a credential-like key {key!r}"
                )
            _scrub(value, f"{path}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _scrub(value, f"{path}[{index}]")


def _assert_well_formed(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise LedgerCorruptError("ledger root must be a JSON object")
    for field in ("schema_version", "job_id", "state", "revision"):
        if field not in payload:
            raise LedgerCorruptError(f"ledger is missing required field {field!r}")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise LedgerCorruptError(
            f"unsupported ledger schema_version {payload['schema_version']!r}"
        )
    if payload["state"] not in {state.value for state in JobState}:
        raise LedgerCorruptError(f"unknown ledger state {payload['state']!r}")
    if not isinstance(payload["revision"], int) or payload["revision"] < 1:
        raise LedgerCorruptError("ledger revision must be a positive integer")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    violations = schema_lite.validate(payload, schema)
    if violations:
        raise LedgerCorruptError(f"ledger does not conform to its schema: {'; '.join(violations)}")
    return payload


def load_ledger(path: Path) -> dict:
    target = Path(path)
    try:
        raw = target.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise LedgerCorruptError(f"no ledger at {target}") from error
    except OSError as error:
        raise LedgerCorruptError(f"ledger at {target} could not be read: {error}") from error
    try:
        decoded = json.loads(raw)
    except ValueError as error:
        raise LedgerCorruptError(f"ledger at {target} is not valid JSON: {error}") from error
    _scrub(decoded)
    try:
        migration = contract_migrations.migrate_factory_job(decoded)
    except ValueError as error:
        raise LedgerCorruptError(f"ledger at {target} could not be migrated: {error}") from error
    payload = migration.document
    return _assert_well_formed(payload)


def write_ledger(path: Path, payload: dict) -> None:
    """Write atomically: a reader sees the previous or the next state, never a torn one."""
    _scrub(payload)
    _assert_well_formed(payload)
    atomic_json.write_json_atomic(Path(path), payload)


def schema_errors(payload: dict) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return schema_lite.validate(payload, schema)


class JobLedger:
    def __init__(self, path: Path, job_id: str | None = None) -> None:
        self.path = Path(path)
        self._job_id = job_id

    def read(self) -> dict:
        return load_ledger(self.path)

    def write(self, payload: dict) -> None:
        write_ledger(self.path, payload)

    def transition(self, target: JobState | str, **fields: object) -> dict:
        try:
            destination = JobState(target)
        except ValueError as error:
            raise ValueError(f"unknown job state {target!r}") from error

        payload = self.read()
        current = JobState(payload["state"])
        if destination not in ALLOWED_TRANSITIONS[current]:
            raise InvalidTransitionError(
                f"cannot move from {current.value} to {destination.value}"
            )

        payload["history"].append(
            {
                "from_state": current.value,
                "to_state": destination.value,
                "at": _timestamp(),
                **({"note": fields["note"]} if "note" in fields else {}),
            }
        )
        payload["state"] = destination.value
        payload["revision"] = payload["revision"] + 1
        payload["updated_at"] = _timestamp()
        for key, value in fields.items():
            if key == "note":
                continue
            payload[key] = value
        self.write(payload)
        return payload

    def bind_plan(
        self,
        plan_sha256: str,
        round_number: int,
        image_count: int,
        item_keys: object | None = None,
    ) -> dict:
        self._validate_plan_binding(plan_sha256, round_number, image_count)
        payload = self.read()
        binding = {
            "batch_id": self._job_id or payload["job_id"],
            "round": round_number,
            "plan_sha256": plan_sha256,
            "image_count": image_count,
        }
        keys = None if item_keys is None else list(item_keys)
        if keys is not None and (
            len(keys) != image_count
            or len(set(keys)) != image_count
            or any(
                not isinstance(key, str) or not json_pattern_match(key, SHA256_PATTERN)
                for key in keys
            )
        ):
            raise ValueError("item_keys must contain one unique idempotency key per image")
        if payload["batch"] != binding or (
            keys is not None and payload.get("current_item_keys") != keys
        ):
            payload["batch"] = binding
            if keys is not None:
                payload["current_item_keys"] = keys
            payload["approval"]["current"] = None
            self._persist_mutation(payload)
        return payload

    def record_approval(
        self,
        plan_sha256: str,
        round_number: int,
        image_count: int,
        source: str,
    ) -> dict:
        self._validate_plan_binding(plan_sha256, round_number, image_count)
        if source != "run_approve_flag":
            raise ValueError("approval source must be 'run_approve_flag'")
        payload = self.read()
        expected_binding = {
            "batch_id": self._job_id or payload["job_id"],
            "round": round_number,
            "plan_sha256": plan_sha256,
        }
        bound = payload["batch"]
        if bound is None or any(bound[key] != value for key, value in expected_binding.items()):
            raise ValueError("approval must exactly match the bound batch")
        record = {
            "plan_sha256": plan_sha256,
            "round": round_number,
            "image_count": image_count,
            "source": source,
            "approved_at": _timestamp(),
        }
        payload["approval"]["history"].append(record)
        payload["approval"]["current"] = record.copy()
        self._persist_mutation(payload)
        return payload

    def record_evaluation(self, scores_sha256: str, decision: str) -> dict:
        """Record the legacy Evaluated intermediate state for compatibility.

        Production evaluate orchestration must use ``record_evaluation_final``.
        """
        if not isinstance(scores_sha256, str) or not json_pattern_match(
            scores_sha256, SHA256_PATTERN
        ):
            raise ValueError("scores_sha256 must be 64 lowercase hexadecimal characters")
        if decision not in ("pass", "fail", "pending_approval"):
            raise ValueError("unknown evaluation decision")
        return self.transition(
            JobState.EVALUATED,
            evaluation={
                "scores_sha256": scores_sha256,
                "decision": decision,
                "evaluated_at": _timestamp(),
            },
        )

    def record_evaluation_final(self, scores_sha256: str, decision: str) -> dict:
        """Persist evaluation evidence and its final state in one ledger revision."""
        if not isinstance(scores_sha256, str) or not json_pattern_match(
            scores_sha256, SHA256_PATTERN
        ):
            raise ValueError("scores_sha256 must be 64 lowercase hexadecimal characters")
        targets = {
            "fail": JobState.EVALUATED,
            "pass": JobState.ACCEPTED,
            "pending_approval": JobState.PENDING_APPROVAL,
        }
        if decision not in targets:
            raise ValueError("unknown evaluation decision")

        payload = self.read()
        current = JobState(payload["state"])
        if current not in (
            JobState.COMPLETED,
            JobState.PARTIAL,
            JobState.PENDING_APPROVAL,
        ):
            raise InvalidTransitionError(f"cannot evaluate job in state {current.value}")
        target = targets[decision]
        timestamp = _timestamp()
        payload["history"].append(
            {
                "from_state": current.value,
                "to_state": target.value,
                "at": timestamp,
            }
        )
        payload["state"] = target.value
        payload["evaluation"] = {
            "scores_sha256": scores_sha256,
            "decision": decision,
            "evaluated_at": timestamp,
        }
        self._persist_mutation(payload)
        return payload

    def record_optimization(self, plan_sha256: str, round_number: int) -> dict:
        if not isinstance(plan_sha256, str) or not json_pattern_match(
            plan_sha256, SHA256_PATTERN
        ):
            raise ValueError("plan_sha256 must be 64 lowercase hexadecimal characters")
        if (
            not isinstance(round_number, int)
            or isinstance(round_number, bool)
            or round_number < 2
        ):
            raise ValueError("round_number must be an integer of at least 2")
        approval = self.read()["approval"]
        approval["current"] = None
        return self.transition(
            JobState.OPTIMIZED,
            approval=approval,
            optimization={
                "next_plan_sha256": plan_sha256,
                "next_round": round_number,
                "created_at": _timestamp(),
            },
        )

    def approval_matches(self, plan_sha256: str, round_number: int, image_count: int) -> bool:
        payload = self.read()
        current = payload["approval"]["current"]
        expected_binding = {
            "batch_id": self._job_id or payload["job_id"],
            "round": round_number,
            "plan_sha256": plan_sha256,
        }
        bound = payload["batch"]
        binding_matches = bound is not None and all(
            bound[key] == value for key, value in expected_binding.items()
        )
        return binding_matches and current is not None and all(
            (
                current["plan_sha256"] == plan_sha256,
                current["round"] == round_number,
                current["image_count"] == image_count,
            )
        )

    def start_attempt(self, item: object, attempt_id: str) -> dict:
        self._validate_attempt_id(attempt_id)
        payload = self.read()
        key = getattr(item, "idempotency_key")
        entry = next(
            (row for row in payload["items"] if row.get("idempotency_key") == key),
            None,
        )
        if entry is not None and entry["state"] != "Pending":
            raise ValueError(
                f"idempotency key {key!r} is already in state {entry['state']!r}"
            )
        if entry is None:
            entry = {
                "item_id": getattr(item, "id"),
                "state": "Pending",
                "attempts": 0,
                "attempt_id": None,
                "attempt_started_at": None,
                "receipt_id": None,
                "idempotency_key": key,
                "error_category": None,
            }
            payload["items"].append(entry)
        entry.update(
            {
                "item_id": getattr(item, "id"),
                "state": "Attempting",
                "attempts": entry["attempts"] + 1,
                "attempt_id": attempt_id,
                "attempt_started_at": _timestamp(),
                "receipt_id": None,
                "idempotency_key": key,
                "error_category": None,
            }
        )
        self._persist_mutation(payload)
        return payload

    def complete_attempt(self, item: object, attempt_id: str, receipt_id: str) -> dict:
        payload, entry = self._active_attempt(getattr(item, "id"), attempt_id)
        if entry["idempotency_key"] != getattr(item, "idempotency_key"):
            raise ValueError("active attempt does not match the item's idempotency key")
        entry["state"] = "Generated"
        entry["receipt_id"] = receipt_id
        entry["error_category"] = None
        self._persist_mutation(payload)
        return payload

    def fail_attempt(
        self, item: object, attempt_id: str, error_category: str
    ) -> dict:
        if error_category not in ERROR_CATEGORIES:
            raise ValueError(f"unknown error category {error_category!r}")
        payload, entry = self._active_attempt(getattr(item, "id"), attempt_id)
        if entry["idempotency_key"] != getattr(item, "idempotency_key"):
            raise ValueError("active attempt does not match the item's idempotency key")
        entry["state"] = "Failed"
        entry["receipt_id"] = None
        entry["error_category"] = error_category
        self._persist_mutation(payload)
        return payload

    def mark_attempt_unknown(self, item_id: str, attempt_id: str) -> dict:
        payload, entry = self._active_attempt(item_id, attempt_id)
        entry["state"] = "Unknown"
        entry["receipt_id"] = None
        entry["error_category"] = "unknown"
        self._persist_mutation(payload)
        return payload

    @staticmethod
    def _validate_plan_binding(plan_sha256: str, round_number: int, image_count: int) -> None:
        if not isinstance(plan_sha256, str) or not json_pattern_match(
            plan_sha256, SHA256_PATTERN
        ):
            raise ValueError("plan_sha256 must be 64 lowercase hexadecimal characters")
        if not isinstance(round_number, int) or isinstance(round_number, bool) or round_number < 1:
            raise ValueError("round_number must be a positive integer")
        if not isinstance(image_count, int) or isinstance(image_count, bool) or not 1 <= image_count <= 200:
            raise ValueError("image_count must be between 1 and 200")

    @staticmethod
    def _validate_attempt_id(attempt_id: str) -> None:
        if not isinstance(attempt_id, str) or not json_pattern_match(
            attempt_id, ATTEMPT_ID_PATTERN
        ):
            raise ValueError("attempt_id must be 32 lowercase hexadecimal characters")

    def _active_attempt(self, item_id: str, attempt_id: str) -> tuple[dict, dict]:
        self._validate_attempt_id(attempt_id)
        payload = self.read()
        entry = next(
            (
                row
                for row in payload["items"]
                if row["item_id"] == item_id and row["attempt_id"] == attempt_id
            ),
            None,
        )
        if entry is None or entry["state"] != "Attempting" or entry["attempt_id"] != attempt_id:
            raise ValueError(f"no active attempt {attempt_id!r} for item {item_id!r}")
        return payload, entry

    def _persist_mutation(self, payload: dict) -> None:
        payload["revision"] += 1
        payload["updated_at"] = _timestamp()
        self.write(payload)

    def record_item(
        self,
        item: object,
        *,
        state: str,
        receipt_id: str | None = None,
        error_category: str | None = None,
    ) -> dict:
        if state not in ITEM_STATES:
            raise ValueError(f"item state must be one of {ITEM_STATES}, got {state!r}")
        if error_category is not None and error_category not in ERROR_CATEGORIES:
            raise ValueError(f"unknown error category {error_category!r}")

        payload = self.read()
        item_id = getattr(item, "id")
        key = getattr(item, "idempotency_key")
        entry = next((row for row in payload["items"] if row["item_id"] == item_id), None)
        if entry is None:
            entry = {
                "item_id": item_id,
                "state": state,
                "attempts": 0,
                "attempt_id": None,
                "attempt_started_at": None,
                "receipt_id": None,
                "idempotency_key": None,
                "error_category": None,
            }
            payload["items"].append(entry)
        if state in ATTEMPTED_ITEM_STATES:
            entry["attempts"] = entry["attempts"] + 1
        entry["state"] = state
        entry["idempotency_key"] = key
        entry["receipt_id"] = receipt_id
        entry["error_category"] = error_category
        payload["revision"] = payload["revision"] + 1
        payload["updated_at"] = _timestamp()
        self.write(payload)
        return payload

    def pending_items(self, items: object) -> list:
        """Items with no recorded attempt.

        An item that was attempted and failed is deliberately absent: retrying it
        automatically is not this plugin's decision to make.
        """
        payload = self.read()
        seen = {row.get("idempotency_key") for row in payload["items"] if row.get("idempotency_key")}
        return [item for item in items if getattr(item, "idempotency_key") not in seen]

    def note_usage_limit(self, *, limit_id: str, resets_at: int | None) -> dict:
        if limit_id != IMAGE_LIMIT_ID:
            raise ValueError(f"only the {IMAGE_LIMIT_ID!r} limit is tracked, got {limit_id!r}")
        payload = self.read()
        payload["usage_limit"] = {"limit_id": limit_id, "resets_at": resets_at}
        payload["error_category"] = "quota_exceeded"
        payload["revision"] = payload["revision"] + 1
        payload["updated_at"] = _timestamp()
        self.write(payload)
        return payload

    def set_error_category(self, category: str | None) -> dict:
        if category is not None and category not in ERROR_CATEGORIES:
            raise ValueError(f"unknown error category {category!r}")
        payload = self.read()
        payload["error_category"] = category
        payload["revision"] = payload["revision"] + 1
        payload["updated_at"] = _timestamp()
        self.write(payload)
        return payload
