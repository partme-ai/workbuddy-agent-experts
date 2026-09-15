#!/usr/bin/env python3
"""Validate an image batch plan before anything is allowed to spend usage.

Validation is split in two stages on purpose. Structural validation runs first
against the published JSON Schema and returns immediately if it fails, so a plan
that asks for something the platform cannot do (a size, a quality tier, a model)
is rejected as a contract violation rather than quietly ignored. Only a
structurally valid plan reaches the semantic stage, which hashes reference
images, rejects duplicate work, and applies the spend caps.

Every batch item carries an idempotency key derived from its content, so a
resumed run can skip an item that has already been produced instead of paying
for it twice.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import contract_migrations
import schema_lite

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "image_batch.schema.json"

# These mirror the published schema and are asserted against it in tests, so the
# document and the code cannot drift apart unnoticed.
DEFAULT_MAX_IMAGES = 200
DEFAULT_MAX_ROUNDS = 20
MAX_REFERENCE_IMAGES = 5

HASH_CHUNK = 64 * 1024


@dataclass(frozen=True)
class PlanError:
    code: str
    message: str
    item_id: str | None = None


@dataclass(frozen=True)
class PlanItem:
    id: str
    prompt: str
    round: int
    reference_images: tuple[str, ...]
    reference_sha256: tuple[str, ...]
    idempotency_key: str


@dataclass(frozen=True)
class PlanResult:
    ok: bool
    batch_id: str
    round: int
    errors: tuple[PlanError, ...]
    items: tuple[PlanItem, ...]
    require_approval_before_run: bool
    max_images: int
    max_rounds: int
    pass_threshold: float
    min_dimension: int
    reject_duplicates: bool
    advisory_enabled: bool
    plan_sha256: str
    require_human_labels: bool
    migration_notes: tuple[str, ...]


def file_sha256(target: Path) -> str:
    digest = hashlib.sha256()
    with target.open("rb") as handle:
        while True:
            block = handle.read(HASH_CHUNK)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def compute_idempotency_key(
    *,
    batch_id: str,
    item_id: str,
    round_number: int,
    prompt: str,
    reference_sha256: tuple[str, ...],
) -> str:
    """Hash what would actually be sent, so identical work maps to one key.

    Reference order is preserved because an edit treats the first reference as the
    identity source; reordering them is a different request.
    """
    payload = json.dumps(
        {
            "batch_id": batch_id,
            "item_id": item_id,
            "round": round_number,
            "prompt": prompt,
            "reference_sha256": list(reference_sha256),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonical_plan_sha256(result_fields: dict) -> str:
    """Return the SHA-256 of a canonical, semantic plan representation."""
    encoded = json.dumps(
        result_fields,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _coerce(plan: object) -> tuple[dict | None, PlanError | None]:
    if isinstance(plan, dict):
        return plan, None
    if isinstance(plan, (str, bytes)):
        try:
            loaded = json.loads(plan)
        except (ValueError, UnicodeDecodeError) as error:
            return None, PlanError("plan_unparseable", f"plan is not valid JSON: {error}")
        if not isinstance(loaded, dict):
            return None, PlanError("plan_unparseable", "plan must be a JSON object")
        return loaded, None
    return None, PlanError("plan_unparseable", f"unsupported plan type: {type(plan).__name__}")


def validate_plan(
    plan: object,
    *,
    base_dir: Path,
    schema: dict | None = None,
) -> PlanResult:
    document = schema if schema is not None else _load_schema()
    empty = PlanResult(
        ok=False,
        batch_id="",
        round=0,
        errors=(),
        items=(),
        require_approval_before_run=True,
        max_images=DEFAULT_MAX_IMAGES,
        max_rounds=DEFAULT_MAX_ROUNDS,
        pass_threshold=0.0,
        min_dimension=0,
        reject_duplicates=True,
        advisory_enabled=False,
        plan_sha256="",
        require_human_labels=True,
        migration_notes=(),
    )

    instance, coercion_error = _coerce(plan)
    if instance is None:
        assert coercion_error is not None
        return PlanResult(**{**empty.__dict__, "errors": (coercion_error,)})

    try:
        migration = contract_migrations.migrate_image_batch(instance)
    except ValueError as error:
        return PlanResult(
            **{**empty.__dict__, "errors": (PlanError("plan_schema_invalid", str(error)),)}
        )
    instance = migration.document
    empty = PlanResult(**{**empty.__dict__, "migration_notes": migration.notes})
    structural = schema_lite.validate(instance, document)
    if structural:
        errors = tuple(PlanError("plan_schema_invalid", message) for message in structural)
        return PlanResult(**{**empty.__dict__, "errors": errors})

    batch_id = instance["batch_id"]
    round_number = instance["round"]
    limits = instance.get("limits") or {}
    policy = instance.get("judge_policy") or {}

    max_images = limits.get("max_images", DEFAULT_MAX_IMAGES)
    max_rounds = limits.get("max_rounds", DEFAULT_MAX_ROUNDS)
    require_approval = limits.get("require_approval_before_run", True)

    errors: list[PlanError] = []
    rows = instance["items"]

    if len(rows) > max_images:
        errors.append(
            PlanError(
                "plan_exceeds_max_images",
                f"plan declares {len(rows)} items but its cap is {max_images}",
            )
        )
    if round_number > max_rounds:
        errors.append(
            PlanError(
                "plan_exceeds_max_rounds",
                f"round {round_number} exceeds the cap of {max_rounds}",
            )
        )

    seen: set[str] = set()
    items: list[PlanItem] = []
    for row in rows:
        item_id = row["id"]
        prompt = row["prompt"].strip()
        if not prompt:
            errors.append(PlanError("plan_empty_prompt", "prompt is empty after trimming", item_id))
            continue
        if item_id in seen:
            errors.append(PlanError("plan_duplicate_item_id", f"duplicate item id {item_id!r}", item_id))
            continue
        seen.add(item_id)

        references = tuple(row.get("reference_images") or ())
        if len(references) > MAX_REFERENCE_IMAGES:
            errors.append(
                PlanError(
                    "plan_schema_invalid",
                    f"item {item_id!r} passes {len(references)} reference images; the platform accepts {MAX_REFERENCE_IMAGES}",
                    item_id,
                )
            )
            continue

        hashes: list[str] = []
        missing = False
        for reference in references:
            target = Path(reference)
            if not target.is_absolute():
                target = base_dir / target
            if not target.is_file():
                errors.append(
                    PlanError(
                        "plan_missing_reference_image",
                        f"reference image not found: {reference}",
                        item_id,
                    )
                )
                missing = True
                continue
            hashes.append(file_sha256(target))
        if missing:
            continue

        reference_hashes = tuple(hashes)
        items.append(
            PlanItem(
                id=item_id,
                prompt=prompt,
                round=round_number,
                reference_images=references,
                reference_sha256=reference_hashes,
                idempotency_key=compute_idempotency_key(
                    batch_id=batch_id,
                    item_id=item_id,
                    round_number=round_number,
                    prompt=prompt,
                    reference_sha256=reference_hashes,
                ),
            )
        )

    require_human_labels = policy.get("require_human_labels", True)
    pass_threshold = policy.get("pass_threshold", 0.8)
    min_dimension = policy.get("min_dimension", 256)
    reject_duplicates = policy.get("reject_duplicates", True)
    advisory_enabled = policy.get("advisory_enabled", False)
    plan_sha256 = ""
    if not errors:
        plan_sha256 = canonical_plan_sha256(
            {
                "batch_id": batch_id,
                "round": round_number,
                "limits": {
                    "max_images": max_images,
                    "max_rounds": max_rounds,
                    "require_approval_before_run": require_approval,
                },
                "judge_policy": {
                    "min_dimension": min_dimension,
                    "reject_duplicates": reject_duplicates,
                    "pass_threshold": pass_threshold,
                    "advisory_enabled": advisory_enabled,
                    "require_human_labels": require_human_labels,
                },
                "items": [
                    {
                        "id": item.id,
                        "prompt": item.prompt,
                        "reference_sha256": list(item.reference_sha256),
                        "idempotency_key": item.idempotency_key,
                    }
                    for item in items
                ],
            }
        )

    return PlanResult(
        ok=not errors,
        batch_id=batch_id,
        round=round_number,
        errors=tuple(errors),
        items=tuple(items),
        require_approval_before_run=require_approval,
        max_images=max_images,
        max_rounds=max_rounds,
        pass_threshold=pass_threshold,
        min_dimension=min_dimension,
        reject_duplicates=reject_duplicates,
        advisory_enabled=advisory_enabled,
        plan_sha256=plan_sha256,
        require_human_labels=require_human_labels,
        migration_notes=migration.notes,
    )
