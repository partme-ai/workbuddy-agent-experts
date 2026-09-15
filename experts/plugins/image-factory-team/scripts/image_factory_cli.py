#!/usr/bin/env python3
"""The deterministic command line the Skills call.

Every step of a batch is a subcommand here, and this module is the only place
that decides what a run is allowed to do. It is deliberately unglamorous: no
model is called, no prompt is written, and no image is generated. The CLI
validates, records, verifies, and reports, while Codex supplies the generation
and the wording of any rewrite.

The spend gate lives here. `quote` reports the size of a batch without touching
it, and `run` refuses to start a plan that asks for approval unless `--approve`
is passed. That mirrors the discipline of quoting, approving, and only then
running, which is the cheapest way to keep an unattended batch from becoming an
unattended bill.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
import uuid
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import artifact_collector
import atomic_json
import capability_probe
import contract_migrations
import evaluator
import generation_runner
import job_lock
import job_ledger
import optimizer
import plan_validator
import prompt_library
import receipt_store
import schema_lite

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
EXIT_APPROVAL_REQUIRED = 3
EXIT_CAPABILITY_UNAVAILABLE = 4
EXIT_JOB_LOCKED = 5
EXIT_RECOVERY_REQUIRED = 6

DEFAULT_TIMEOUT_SECONDS = generation_runner.DEFAULT_TIMEOUT_SECONDS
SCORES_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "scores.schema.json"

# Collection failures share one vocabulary with the ledger, which is narrower
# because a ledger entry has to mean something a resume can act on.
COLLECT_CATEGORY = {
    "artifact_missing": "artifact_missing",
    "duplicate_artifact": "duplicate_artifact",
    "hash_mismatch": "hash_mismatch",
    "duplicate_content": "duplicate_artifact",
    "not_a_png": "generation_failed",
    "below_min_dimension": "generation_failed",
}


def _emit(payload: dict, as_json: bool, summary: list[str] | None = None) -> str:
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True)
    lines = summary or [f"{key}: {value}" for key, value in sorted(payload.items())]
    return "\n".join(lines)


def _load_json(path: Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def canonical_path(path: Path) -> Path:
    """Return one absolute spelling for existing or prospective paths."""
    return Path(path).expanduser().resolve(strict=False)


def refuse_path_aliases(named_paths: dict[str, Path]) -> None:
    """Reject two command roles that resolve to the same filesystem path."""
    seen: dict[Path, str] = {}
    for role, path in named_paths.items():
        resolved = canonical_path(path)
        previous = seen.get(resolved)
        if previous is not None:
            raise ValueError(f"path collision between {previous} and {role}")
        seen[resolved] = role


def mutating_command_paths(args: argparse.Namespace) -> dict[str, Path]:
    """Return every effective filesystem role used by a mutating command."""
    common = {
        "plan": Path(args.plan),
        "job": Path(args.job),
        "destination": Path(args.destination),
    }
    if args.command == "run":
        home = getattr(args, "_effective_codex_home", None) or _resolve_codex_home(args)
        generation_dir = getattr(args, "_effective_generation_dir", None) or (
            Path(args.generation_dir) if args.generation_dir else home / "generated_images"
        )
        binary = getattr(args, "_effective_codex_binary", None) or generation_runner.resolved_binary(
            args.codex_bin
        )
        args._effective_codex_home = Path(home)
        args._effective_generation_dir = Path(generation_dir)
        args._effective_codex_binary = str(binary)
        return {
            **common,
            "codex_home": Path(home),
            "generation_dir": Path(generation_dir),
            "codex_bin": Path(binary),
        }
    if args.command == "evaluate":
        paths = {**common, "scores": Path(args.scores)}
        if args.labels:
            paths["labels"] = Path(args.labels)
        if args.advisory:
            paths["advisory"] = Path(args.advisory)
        return paths
    if args.command == "optimize":
        paths = {**common, "scores": Path(args.scores), "out": Path(args.out)}
        if args.rewrites:
            paths["rewrites"] = Path(args.rewrites)
        return paths
    return common


def preflight_mutating_command_paths(args: argparse.Namespace) -> None:
    """Reject path aliases before a command lock or any other side effect."""
    paths = mutating_command_paths(args)
    refuse_path_aliases(paths)
    if args.command not in {"run", "recover"}:
        return

    cached = getattr(args, "_validated_plan_cache", None)
    if cached is None:
        cached = _validated_plan(args)
        args._validated_plan_cache = cached
    result, _plan_path = cached
    if not result.ok:
        return

    job_path = Path(args.job)
    destination = Path(args.destination)
    receipt_directory = receipt_store.receipt_directory(job_path)
    reference_snapshot_directory = Path(str(job_path) + ".reference-snapshots")
    work_directory = destination / ".work"
    message_directory = destination / ".last-messages"
    derived = {
        "job_lock": job_lock.lock_path_for(job_path),
        "receipt_manifest": receipt_store.manifest_path(job_path),
        "receipt_directory": receipt_directory,
        "reference_snapshot_directory": reference_snapshot_directory,
        "work_directory": work_directory,
        "last_message_directory": message_directory,
    }
    for item in result.items:
        key_suffix = item.idempotency_key[:12]
        artifact_directory = destination / result.batch_id / f"round-{item.round}"
        derived[f"receipt:{item.id}"] = receipt_store.receipt_path(
            job_path, item.idempotency_key
        )
        derived[f"last_message:{item.id}"] = (
            message_directory / f"{item.id}-round-{item.round}.last-message.txt"
        )
        derived.setdefault(f"artifact_directory:round-{item.round}", artifact_directory)
        derived[f"artifact:{item.id}"] = (
            artifact_directory / f"{item.id}-r{item.round}-{key_suffix}.png"
        )
    reference_inputs: dict[str, Path] = {}
    reference_seen: set[Path] = set()
    for item in result.items:
        for index, reference in enumerate(item.reference_images):
            source = Path(reference)
            if not source.is_absolute():
                source = Path(args.plan).parent / source
            canonical = canonical_path(source)
            if canonical not in reference_seen:
                reference_inputs[f"reference:{item.id}:{index}"] = source
                reference_seen.add(canonical)
    refuse_path_aliases({**paths, **reference_inputs, **derived})

    write_trees = {
        "destination": destination,
        "receipt_directory": receipt_directory,
        "reference_snapshot_directory": reference_snapshot_directory,
        "work_directory": work_directory,
        "last_message_directory": message_directory,
    }
    if args.command == "run":
        write_trees["generation_dir"] = args._effective_generation_dir
    input_files = {"plan": Path(args.plan), "job": job_path, **reference_inputs}
    if args.command == "run":
        input_files["codex_bin"] = Path(args._effective_codex_binary)
    for input_role, input_path in input_files.items():
        resolved_input = canonical_path(input_path)
        for tree_role, tree_path in write_trees.items():
            resolved_tree = canonical_path(tree_path)
            if resolved_input == resolved_tree or resolved_tree in resolved_input.parents:
                raise ValueError(
                    f"path collision between {input_role} and {tree_role} tree"
                )


def snapshot_plan_references(
    result: plan_validator.PlanResult,
    plan_path: Path,
    job_path: Path,
    pending_keys: set[str],
) -> tuple[plan_validator.PlanResult, dict[str, str]]:
    """Copy and verify references before any attempt is recorded or invoked."""
    snapshot_root = Path(str(job_path) + ".reference-snapshots")
    snapshot_root_existed = snapshot_root.exists()
    created_directories: list[Path] = []
    snapshot_items: list[plan_validator.PlanItem] = []
    attempt_ids: dict[str, str] = {}
    try:
        for item in result.items:
            if item.idempotency_key not in pending_keys or not item.reference_images:
                snapshot_items.append(item)
                continue
            attempt_id = uuid.uuid4().hex
            attempt_ids[item.idempotency_key] = attempt_id
            attempt_directory = snapshot_root / attempt_id
            attempt_directory.mkdir(parents=True, exist_ok=False)
            created_directories.append(attempt_directory)
            snapshots: list[str] = []
            for index, (reference, expected_sha256) in enumerate(
                zip(item.reference_images, item.reference_sha256, strict=True)
            ):
                source = Path(reference)
                if not source.is_absolute():
                    source = plan_path.parent / source
                snapshot = attempt_directory / f"reference-{index}-{expected_sha256}.bin"
                shutil.copyfile(source, snapshot)
                snapshot_sha256 = plan_validator.file_sha256(snapshot)
                source_sha256 = plan_validator.file_sha256(source)
                if snapshot_sha256 != expected_sha256 or source_sha256 != expected_sha256:
                    raise ValueError(
                        f"reference bytes changed after validation for item {item.id!r}"
                    )
                snapshot.chmod(0o400)
                snapshots.append(str(snapshot))
            snapshot_items.append(replace(item, reference_images=tuple(snapshots)))
    except BaseException:
        for directory in reversed(created_directories):
            shutil.rmtree(directory, ignore_errors=True)
        if (
            not snapshot_root_existed
            and snapshot_root.is_dir()
            and not any(snapshot_root.iterdir())
        ):
            snapshot_root.rmdir()
        raise
    return replace(result, items=tuple(snapshot_items)), attempt_ids


def _resolve_codex_home(args: argparse.Namespace) -> Path:
    if args.codex_home:
        return Path(args.codex_home)
    import os

    override = os.environ.get("CODEX_HOME")
    return Path(override) if override else Path.home() / ".codex"


def _resolve_generation_dir(args: argparse.Namespace, codex_home: Path) -> Path:
    return Path(args.generation_dir) if args.generation_dir else codex_home / "generated_images"


def _error_category(code: str) -> str:
    if code in job_ledger.ERROR_CATEGORIES:
        return code
    return COLLECT_CATEGORY.get(code, "unknown")


# --------------------------------------------------------------------------- probe


def command_probe(args: argparse.Namespace) -> tuple[int, str]:
    home = _resolve_codex_home(args)
    binary = Path(args.codex_bin) if args.codex_bin else None
    capability = capability_probe.probe(codex_home=home, binary_override=binary)
    payload = capability_probe.as_report(capability)
    code = EXIT_OK if capability.is_available else EXIT_CAPABILITY_UNAVAILABLE
    summary = [f"verdict: {capability.verdict}", *[f"reason: {item}" for item in capability.reasons]]
    if capability.guidance:
        summary.append(f"guidance: {capability.guidance}")
    return code, _emit(payload, args.json, summary)


# -------------------------------------------------------------------- plan commands


def _validated_plan(args: argparse.Namespace) -> tuple[plan_validator.PlanResult, Path]:
    path = Path(args.plan)
    result = plan_validator.validate_plan(_load_json(path), base_dir=path.parent)
    return result, path


def _plan_error_payload(result: plan_validator.PlanResult) -> dict:
    return {
        "ok": False,
        "batch_id": result.batch_id,
        "errors": [
            {"code": error.code, "message": error.message, "item_id": error.item_id}
            for error in result.errors
        ],
    }


def command_validate_plan(args: argparse.Namespace) -> tuple[int, str]:
    result, _path = _validated_plan(args)
    if not result.ok:
        return EXIT_USAGE, _emit(_plan_error_payload(result), args.json)
    payload = {
        "ok": True,
        "batch_id": result.batch_id,
        "round": result.round,
        "max_images": result.max_images,
        "max_rounds": result.max_rounds,
        "require_approval_before_run": result.require_approval_before_run,
        "plan_sha256": result.plan_sha256,
        "require_human_labels": result.require_human_labels,
        "migration_notes": list(result.migration_notes),
        "items": [
            {
                "item_id": item.id,
                "idempotency_key": item.idempotency_key,
                "reference_images": list(item.reference_images),
            }
            for item in result.items
        ],
    }
    return EXIT_OK, _emit(payload, args.json)


def command_quote(args: argparse.Namespace) -> tuple[int, str]:
    result, _path = _validated_plan(args)
    if not result.ok:
        return EXIT_USAGE, _emit(_plan_error_payload(result), args.json)
    payload = {
        "ok": True,
        "batch_id": result.batch_id,
        "round": result.round,
        "image_count": len(result.items),
        "max_images": result.max_images,
        "approval_required": result.require_approval_before_run,
        "plan_sha256": result.plan_sha256,
        "require_human_labels": result.require_human_labels,
        "migration_notes": list(result.migration_notes),
        # Quoting is free: it reads the plan and spends nothing.
        "spends_allowance_on_quote": False,
        "note": (
            "Each item costs one generation call against the Codex account's image "
            "allowance. Approval is required before the first call."
        ),
    }
    summary = [
        f"batch: {result.batch_id} (round {result.round})",
        f"images to generate: {len(result.items)}",
        f"approval required: {result.require_approval_before_run}",
        f"human labels required: {result.require_human_labels}",
        f"plan sha256: {result.plan_sha256}",
        *[f"migration note: {note}" for note in result.migration_notes],
        "this quote spends nothing",
    ]
    return EXIT_OK, _emit(payload, args.json, summary)


# ------------------------------------------------------------------------- run


class ApprovalRequiredError(RuntimeError):
    def __init__(self, image_count: int) -> None:
        super().__init__("this plan requires approval; rerun with --approve to spend the allowance")
        self.image_count = image_count


class RunStateError(RuntimeError):
    """The durable job state cannot safely enter an ordinary generation run."""


@dataclass(frozen=True)
class RecoveryReport:
    """Result of reconciling durable job evidence without generating images."""

    state: str
    reconciled: tuple[str, ...]
    unknown: tuple[str, ...]
    pending_count: int
    remaining_generation_calls: int


def require_runnable_state(
    payload: dict,
    pending: list[plan_validator.PlanItem],
    plan_items: tuple[plan_validator.PlanItem, ...],
) -> None:
    state = job_ledger.JobState(payload["state"])
    if state is job_ledger.JobState.COMPLETED and not pending:
        return
    if state is job_ledger.JobState.PARTIAL:
        current_keys = {item.idempotency_key for item in plan_items}
        if pending and payload["usage_limit"] is None and not any(
            row["state"] == "Unknown" and row["idempotency_key"] in current_keys
            for row in payload["items"]
        ):
            return
        raise RunStateError("this partial job is not eligible for an automatic generation resume")
    if state not in (
        job_ledger.JobState.DRAFT,
        job_ledger.JobState.OPTIMIZED,
        job_ledger.JobState.PLAN_VALIDATED,
        job_ledger.JobState.APPROVED,
    ):
        raise RunStateError(f"job state {state.value} requires recovery before generation")


def prepare_run(
    ledger: job_ledger.JobLedger,
    plan: plan_validator.PlanResult,
    approved: bool,
) -> list[plan_validator.PlanItem]:
    pending = ledger.pending_items(plan.items)
    payload = ledger.read()
    require_runnable_state(payload, pending, plan.items)
    if job_ledger.JobState(payload["state"]) is job_ledger.JobState.COMPLETED:
        expected = {
            "batch_id": plan.batch_id,
            "round": plan.round,
            "plan_sha256": plan.plan_sha256,
            "image_count": len(plan.items),
        }
        if payload["batch"] != expected:
            raise RunStateError("a changed completed job cannot be resumed as a generation run")
    ledger.bind_plan(
        plan.plan_sha256,
        plan.round,
        len(plan.items),
        (item.idempotency_key for item in plan.items),
    )
    if pending and not approved:
        raise ApprovalRequiredError(len(pending))
    if pending:
        ledger.record_approval(plan.plan_sha256, plan.round, len(pending), "run_approve_flag")
        state = job_ledger.JobState(ledger.read()["state"])
        if state in (job_ledger.JobState.DRAFT, job_ledger.JobState.OPTIMIZED, job_ledger.JobState.PARTIAL):
            ledger.transition(job_ledger.JobState.PLAN_VALIDATED)
        if job_ledger.JobState(ledger.read()["state"]) is job_ledger.JobState.PLAN_VALIDATED:
            ledger.transition(job_ledger.JobState.APPROVED)
        ledger.transition(job_ledger.JobState.RUNNING)
    return pending


def command_run(args: argparse.Namespace) -> tuple[int, str]:
    try:
        preflight_mutating_command_paths(args)
    except ValueError as error:
        return EXIT_USAGE, _emit({"ok": False, "error": str(error)}, args.json)

    home = args._effective_codex_home
    generation_dir = args._effective_generation_dir
    destination = Path(args.destination)
    job_path = Path(args.job)

    result, plan_path = args._validated_plan_cache
    if not result.ok:
        return EXIT_USAGE, _emit(_plan_error_payload(result), args.json)

    binary = Path(args._effective_codex_binary)
    capability = capability_probe.probe(codex_home=home, binary_override=binary)
    if not capability.is_available:
        payload = {"ok": False, "stage": "capability", **capability_probe.as_report(capability)}
        return EXIT_CAPABILITY_UNAVAILABLE, _emit(payload, args.json)

    codex_binary = args._effective_codex_binary
    reference_attempt_ids: dict[str, str] = {}

    if args.approve:
        try:
            if job_path.is_file():
                preview_ledger = job_ledger.JobLedger(job_path)
                pending_keys = {
                    item.idempotency_key
                    for item in preview_ledger.pending_items(result.items)
                }
            else:
                pending_keys = {item.idempotency_key for item in result.items}
            result, reference_attempt_ids = snapshot_plan_references(
                result, plan_path, job_path, pending_keys
            )
        except (OSError, ValueError) as error:
            return EXIT_RECOVERY_REQUIRED, _emit(
                {
                    "ok": False,
                    "error_category": "recovery_required",
                    "error": str(error),
                },
                args.json,
            )

    ledger = job_ledger.JobLedger(job_path)
    if job_path.is_file():
        ledger.read()
    else:
        ledger.write(job_ledger.new_job(result.batch_id))

    try:
        pending = prepare_run(ledger, result, args.approve)
    except ApprovalRequiredError as error:
        ledger.set_error_category("approval_required")
        payload = {
            "ok": False,
            "stage": "approval",
            "error_category": "approval_required",
            "image_count": error.image_count,
            "message": str(error),
        }
        return EXIT_APPROVAL_REQUIRED, _emit(payload, args.json)
    except RunStateError as error:
        payload = {
            "ok": False,
            "stage": "ledger",
            "error_category": "recovery_required",
            "message": str(error),
        }
        return EXIT_RECOVERY_REQUIRED, _emit(payload, args.json)

    ledger_payload = ledger.read()
    state = job_ledger.JobState(ledger_payload["state"])
    completed_binding = {
        "batch_id": result.batch_id,
        "round": result.round,
        "plan_sha256": result.plan_sha256,
        "image_count": len(result.items),
    }
    if state is job_ledger.JobState.COMPLETED:
        if not pending and ledger_payload["batch"] == completed_binding:
            payload = {
                "ok": True,
                "batch_id": result.batch_id,
                "round": result.round,
                "state": job_ledger.JobState.COMPLETED.value,
                "attempted": 0,
                "failed": 0,
                "receipts": [],
                "ledger": str(job_path),
            }
            return EXIT_OK, _emit(payload, args.json)
        payload = {
            "ok": False,
            "stage": "ledger",
            "error_category": "recovery_required",
            "message": "a changed completed job cannot be resumed as a generation run",
        }
        return EXIT_FAILURE, _emit(payload, args.json)

    receipts: list[dict] = []
    failed = 0
    unknown = False

    for item in pending:
        attempt_id = reference_attempt_ids.get(item.idempotency_key) or uuid.uuid4().hex
        ledger.start_attempt(item, attempt_id)
        outcome = generation_runner.run_item(
            binary=codex_binary,
            item=item,
            round_number=result.round,
            workdir=destination / ".work",
            output_dir=destination / ".last-messages",
            generation_dir=generation_dir,
            timeout_seconds=args.timeout,
        )
        if not outcome.ok:
            assert outcome.failure is not None
            failed += 1
            if outcome.failure.code in ("timeout", "artifact_missing", "interrupted"):
                ledger.mark_attempt_unknown(item.id, attempt_id)
                unknown = True
                break
            if outcome.failure.code == "quota_exceeded":
                ledger.note_usage_limit(
                    limit_id=outcome.failure.limit_id or job_ledger.IMAGE_LIMIT_ID,
                    resets_at=outcome.failure.resets_at,
                )
                ledger.fail_attempt(item, attempt_id, "quota_exceeded")
                break
            ledger.fail_attempt(item, attempt_id, _error_category(outcome.failure.code))
            continue

        collected = artifact_collector.collect_artifact(
            item=item,
            batch_id=result.batch_id,
            generation_dir=generation_dir,
            destination_dir=destination,
            before=outcome.before_snapshot,
            min_dimension=result.min_dimension,
            # Judging repeats is the evaluator's job, not the collector's: collection
            # records what exists, evaluation decides whether two files being equal
            # is a problem for this batch.
            reject_duplicates=False,
        )
        if not collected.ok:
            assert collected.failure is not None
            failed += 1
            ledger.fail_attempt(item, attempt_id, _error_category(collected.failure.code))
            continue

        assert collected.receipt is not None
        receipt_store.write_receipt(job_path, collected.receipt)
        ledger.complete_attempt(item, attempt_id, collected.receipt["artifact_id"])
        receipts.append(collected.receipt)

    verified = receipt_store.load_verified_receipts(job_path, destination)
    receipt_store.rebuild_manifest(job_path, verified)

    final = job_ledger.JobState.UNKNOWN if unknown else (
        job_ledger.JobState.PARTIAL if failed else job_ledger.JobState.COMPLETED
    )
    ledger.transition(final)

    payload = {
        "ok": failed == 0,
        "batch_id": result.batch_id,
        "round": result.round,
        "state": final.value,
        "attempted": len(pending),
        "failed": failed,
        "receipts": receipts,
        "ledger": str(job_path),
    }
    code = EXIT_OK if failed == 0 else EXIT_FAILURE
    return code, _emit(payload, args.json)


# --------------------------------------------------------------------- recovery


def command_recover(args: argparse.Namespace) -> tuple[int, str]:
    """Reconcile verified receipts into the ledger without invoking Codex."""
    try:
        preflight_mutating_command_paths(args)
    except ValueError as error:
        return EXIT_USAGE, _emit({"ok": False, "error": str(error)}, args.json)

    result, _plan_path = args._validated_plan_cache
    if not result.ok:
        return EXIT_USAGE, _emit(_plan_error_payload(result), args.json)

    job_path = Path(args.job)
    destination = Path(args.destination)
    ledger = job_ledger.JobLedger(job_path)
    current = ledger.read()
    expected = {
        "batch_id": result.batch_id,
        "round": result.round,
        "plan_sha256": result.plan_sha256,
        "image_count": len(result.items),
    }
    if current["batch"] != expected:
        raise ValueError("recovery plan does not match the job batch")
    source_state = job_ledger.JobState(current["state"])
    if source_state not in (
        job_ledger.JobState.RUNNING,
        job_ledger.JobState.UNKNOWN,
        job_ledger.JobState.PARTIAL,
        job_ledger.JobState.COMPLETED,
    ):
        raise ValueError(f"job state {source_state.value} does not require recovery")

    plan_by_id = {item.id: item for item in result.items}
    current_keys = {item.idempotency_key for item in result.items}
    rows_by_id: dict[str, dict] = {}
    keys_seen: set[str] = set()
    for row in current["items"]:
        if row["idempotency_key"] not in current_keys:
            continue
        item = plan_by_id.get(row["item_id"])
        if item is None or row["idempotency_key"] != item.idempotency_key:
            raise ValueError("ledger item does not match the current plan")
        if row["item_id"] in rows_by_id or row["idempotency_key"] in keys_seen:
            raise ValueError("duplicate ledger item for the current plan")
        rows_by_id[row["item_id"]] = row
        keys_seen.add(row["idempotency_key"])

    # Verification and all consistency checks complete before ledger mutation.
    verified = receipt_store.load_verified_receipts(job_path, destination, current_keys)
    plan_by_key = {item.idempotency_key: item for item in result.items}
    applicable: dict[str, dict] = {}
    for key, receipt in verified.items():
        # The aggregate manifest is only a compatibility projection. Recovery
        # authority comes from the deterministic per-item receipt file.
        if not receipt_store.receipt_path(job_path, key).is_file():
            continue
        item = plan_by_key.get(key)
        if item is None or (
            receipt["batch_id"] != result.batch_id
            or receipt["round"] != result.round
            or receipt["item_id"] != item.id
        ):
            raise ValueError("verified receipt does not match the recovery plan")
        expected_prompt_sha256 = hashlib.sha256(item.prompt.encode("utf-8")).hexdigest()
        if receipt["prompt_sha256"] != expected_prompt_sha256:
            raise ValueError("verified receipt prompt hash does not match the planned prompt")
        if item.id not in rows_by_id:
            raise ValueError("verified receipt has no matching current-plan ledger item")
        applicable[key] = receipt

    reconciled: list[str] = []
    unknown: list[str] = []
    for item in result.items:
        row = rows_by_id.get(item.id)
        if row is None:
            continue
        receipt = applicable.get(item.idempotency_key)
        if row["state"] in ("Attempting", "Unknown") and receipt is not None:
            row["state"] = "Generated"
            row["receipt_id"] = receipt["artifact_id"]
            row["error_category"] = None
            reconciled.append(row["item_id"])
        elif row["state"] in ("Attempting", "Unknown") or (
            row["state"] == "Generated"
            and (
                receipt is None
                or row["receipt_id"] != receipt["artifact_id"]
            )
        ):
            row["state"] = "Unknown"
            row["receipt_id"] = None
            row["error_category"] = "unknown"
            unknown.append(row["item_id"])

    pending_item_ids = {
        item.id
        for item in result.items
        if item.id not in rows_by_id or rows_by_id[item.id]["state"] == "Pending"
    }
    pending_count = len(pending_item_ids)
    generated_count = sum(row["state"] == "Generated" for row in rows_by_id.values())
    failed_count = sum(row["state"] in ("Failed", "Skipped") for row in rows_by_id.values())
    unknown_count = sum(row["state"] == "Unknown" for row in rows_by_id.values())
    if unknown_count:
        target = job_ledger.JobState.UNKNOWN
    elif generated_count == len(result.items):
        target = job_ledger.JobState.COMPLETED
    else:
        target = job_ledger.JobState.PARTIAL

    if source_state is not target:
        current["history"].append(
            {
                "from_state": source_state.value,
                "to_state": target.value,
                "at": job_ledger._timestamp(),
                "note": "reconciled verified per-item receipts",
            }
        )
    current["state"] = target.value
    ledger._persist_mutation(current)
    receipt_store.rebuild_manifest(job_path, applicable)

    report = RecoveryReport(
        state=target.value,
        reconciled=tuple(reconciled),
        unknown=tuple(unknown),
        pending_count=pending_count,
        remaining_generation_calls=pending_count,
    )
    payload = {
        "ok": not unknown_count,
        **asdict(report),
        "completed_count": generated_count,
        "failed_count": failed_count,
        "unknown_count": unknown_count,
    }
    code = EXIT_RECOVERY_REQUIRED if unknown_count else EXIT_OK
    return code, _emit(payload, args.json)


# -------------------------------------------------------------------- evaluate


def _advisory_from_file(path: str | None) -> dict:
    if not path:
        return {}
    raw = _load_json(Path(path))
    if not isinstance(raw, dict):
        raise ValueError("advisory file must be a JSON object of item id to [score, reason]")
    return {key: tuple(value) if isinstance(value, list) else value for key, value in raw.items()}


def current_rows_by_key(payload: dict, current_keys: set[str]) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for row in payload["items"]:
        key = row.get("idempotency_key")
        if key not in current_keys:
            continue
        if key in rows:
            raise ValueError("duplicate current-round ledger rows")
        rows[key] = row
    return rows


def command_evaluate(args: argparse.Namespace) -> tuple[int, str]:
    try:
        preflight_mutating_command_paths(args)
    except ValueError as error:
        return EXIT_USAGE, _emit({"ok": False, "error": str(error)}, args.json)

    result, _plan_path = _validated_plan(args)
    if not result.ok:
        return EXIT_USAGE, _emit(_plan_error_payload(result), args.json)

    ledger = job_ledger.JobLedger(Path(args.job))
    current = ledger.read()
    expected = {
        "batch_id": result.batch_id,
        "round": result.round,
        "plan_sha256": result.plan_sha256,
        "image_count": len(result.items),
    }
    if current["batch"] != expected:
        raise ValueError("evaluation plan does not match the job batch")
    state = job_ledger.JobState(current["state"])
    if state not in (
        job_ledger.JobState.COMPLETED,
        job_ledger.JobState.PARTIAL,
        job_ledger.JobState.PENDING_APPROVAL,
    ):
        raise ValueError(f"job state {state.value} cannot be evaluated")
    if state is job_ledger.JobState.PARTIAL and ledger.pending_items(result.items):
        raise ValueError("a partial job with pending calls cannot be evaluated")

    current_keys = {item.idempotency_key for item in result.items}
    current_rows = current_rows_by_key(current, current_keys)
    verified = receipt_store.load_verified_receipts(
        Path(args.job), Path(args.destination), current_keys
    )
    receipts: dict[str, dict] = {}
    for item in result.items:
        row = current_rows.get(item.idempotency_key)
        receipt = verified.get(item.idempotency_key)
        if row is None or row["state"] in ("Pending", "Attempting", "Unknown"):
            raise ValueError(
                f"plan item {item.id!r} is not terminal and cannot be evaluated"
            )
        if row["state"] in ("Failed", "Skipped"):
            if receipt is not None:
                raise ValueError(
                    f"failed plan item {item.id!r} has contradictory receipt evidence"
                )
            continue
        if row["state"] != "Generated":
            raise ValueError(f"unsupported ledger state for plan item {item.id!r}")
        expected_prompt = hashlib.sha256(item.prompt.encode("utf-8")).hexdigest()
        if (
            receipt is None
            or receipt["batch_id"] != result.batch_id
            or receipt["round"] != result.round
            or receipt["item_id"] != item.id
            or receipt["prompt_sha256"] != expected_prompt
            or row["receipt_id"] != receipt["artifact_id"]
        ):
            raise ValueError(
                f"current receipt and ledger evidence do not match plan item {item.id!r}"
            )
        receipts[item.id] = receipt

    try:
        advisory = _advisory_from_file(args.advisory)
        labels = _load_json(Path(args.labels)) if args.labels else {}
    except ValueError as error:
        return EXIT_USAGE, _emit({"ok": False, "error": str(error)}, args.json)

    evaluation = evaluator.evaluate_batch(
        batch_id=result.batch_id,
        round_number=result.round,
        items=result.items,
        receipts=receipts,
        destination_dir=Path(args.destination),
        min_dimension=result.min_dimension,
        reject_duplicates=result.reject_duplicates,
        pass_threshold=result.pass_threshold,
        advisory_enabled=result.advisory_enabled,
        require_human_labels=result.require_human_labels,
        advisory=advisory,
        human_labels=labels,
    )
    scores_path = Path(args.scores)
    atomic_json.write_json_atomic(scores_path, evaluation.scores)
    scores_sha256 = hashlib.sha256(scores_path.read_bytes()).hexdigest()
    ledger.record_evaluation_final(scores_sha256, evaluation.scores["decision"])

    payload = {
        "ok": evaluation.ok,
        "decision": evaluation.scores["decision"],
        "all_gates_passed": evaluation.scores["deterministic_gates"]["all_passed"],
        "scores": str(scores_path),
    }
    code = EXIT_FAILURE if evaluation.scores["decision"] == "fail" else EXIT_OK
    return code, _emit(payload, args.json)


# -------------------------------------------------------------------- optimize


def command_optimize(args: argparse.Namespace) -> tuple[int, str]:
    try:
        preflight_mutating_command_paths(args)
    except ValueError as error:
        return EXIT_USAGE, _emit({"ok": False, "error": str(error)}, args.json)

    plan_path = Path(args.plan)
    plan = _load_json(plan_path)
    validation = plan_validator.validate_plan(plan, base_dir=plan_path.parent)
    if not validation.ok:
        return EXIT_USAGE, _emit(_plan_error_payload(validation), args.json)
    migration = contract_migrations.migrate_image_batch(plan)
    plan = migration.document
    scores_path = Path(args.scores)
    scores_bytes = scores_path.read_bytes()
    scores = json.loads(scores_bytes)
    scores_schema = json.loads(SCORES_SCHEMA_PATH.read_text(encoding="utf-8"))
    scores_errors = schema_lite.validate(scores, scores_schema)
    if scores_errors:
        raise ValueError(f"scores schema invalid: {'; '.join(scores_errors)}")
    ledger = job_ledger.JobLedger(Path(args.job))
    current = ledger.read()
    if current["state"] != job_ledger.JobState.EVALUATED.value:
        raise ValueError("optimization requires an Evaluated job")
    expected = {
        "batch_id": validation.batch_id,
        "round": validation.round,
        "plan_sha256": validation.plan_sha256,
        "image_count": len(validation.items),
    }
    if current["batch"] != expected:
        raise ValueError("optimization plan does not match the job batch")
    evaluation_record = current["evaluation"]
    if evaluation_record is None:
        raise ValueError("job has no persisted evaluation")
    if (
        hashlib.sha256(scores_bytes).hexdigest()
        != evaluation_record["scores_sha256"]
    ):
        raise ValueError("scores file does not match the persisted evaluation")
    if (
        not isinstance(scores, dict)
        or scores.get("batch_id") != validation.batch_id
        or scores.get("round") != validation.round
    ):
        raise ValueError("scores batch and round must match the current plan")
    if scores["decision"] != evaluation_record["decision"]:
        raise ValueError("scores decision does not match the persisted evaluation decision")
    expected_items = {item.id for item in validation.items}
    for section, rows in (
        ("deterministic", scores["deterministic_gates"]["per_item"]),
        ("human label", scores["human_labels"]),
    ):
        identifiers = [row["item_id"] for row in rows]
        if len(identifiers) != len(expected_items) or set(identifiers) != expected_items:
            raise ValueError(
                f"scores must contain exactly one {section} row for every plan item"
            )
    advisory_ids = [row["item_id"] for row in scores["advisory"]["items"]]
    if len(advisory_ids) != len(set(advisory_ids)) or not set(advisory_ids) <= expected_items:
        raise ValueError("scores advisory rows must be unique and belong to the current plan")
    rewrites = _load_json(Path(args.rewrites)) if args.rewrites else {}
    if not isinstance(rewrites, dict):
        return EXIT_USAGE, _emit({"ok": False, "error": "rewrites must be a JSON object"}, args.json)

    outcome = optimizer.plan_next_round(
        current_plan=plan,
        evaluation=scores,
        rewrites=rewrites,
        retry_unchanged=set(args.retry_unchanged or []),
    )
    if outcome.errors:
        payload = {
            "ok": False,
            "errors": [
                {"code": error.code, "message": error.message, "item_id": error.item_id}
                for error in outcome.errors
            ],
        }
        return EXIT_FAILURE, _emit(payload, args.json)

    if outcome.complete:
        payload = {"ok": True, "complete": True, "carried_forward": list(outcome.carried_forward)}
        return EXIT_OK, _emit(payload, args.json)

    assert outcome.next_plan is not None
    out_path = Path(args.out)
    next_validation = plan_validator.validate_plan(outcome.next_plan, base_dir=out_path.parent)
    if not next_validation.ok:
        return EXIT_FAILURE, _emit(_plan_error_payload(next_validation), args.json)
    if (
        next_validation.batch_id != validation.batch_id
        or next_validation.round != validation.round + 1
    ):
        raise ValueError("optimized plan must preserve batch id and advance exactly one round")
    atomic_json.write_json_atomic(out_path, outcome.next_plan)
    ledger.record_optimization(next_validation.plan_sha256, next_validation.round)
    payload = {
        "ok": True,
        "complete": False,
        "round": outcome.next_plan["round"],
        "rework": list(outcome.rework),
        "carried_forward": list(outcome.carried_forward),
        "plan": str(args.out),
    }
    return EXIT_OK, _emit(payload, args.json)


# ---------------------------------------------------------------------- status


def command_status(args: argparse.Namespace) -> tuple[int, str]:
    try:
        payload = job_ledger.load_ledger(Path(args.job))
    except job_ledger.LedgerCorruptError as error:
        return EXIT_FAILURE, _emit({"ok": False, "error": str(error)}, args.json)
    counts = {
        name: 0
        for name in ("attempting", "failed", "generated", "pending", "skipped", "unknown")
    }
    current_keys = set(payload.get("current_item_keys") or ())
    if not current_keys:
        current_keys = {row.get("idempotency_key") for row in payload["items"]}
    try:
        current_rows = list(current_rows_by_key(payload, current_keys).values())
    except ValueError as error:
        return EXIT_FAILURE, _emit(
            {"ok": False, "error": str(error)}, args.json
        )
    for row in current_rows:
        key = row["state"].lower()
        if key in counts:
            counts[key] += 1
    bound_count = payload["batch"]["image_count"] if payload["batch"] else 0
    counts["pending"] += max(0, bound_count - len(current_rows))
    current_approval = payload["approval"]["current"]
    approval = {
        "current": (
            None
            if current_approval is None
            else {
                "round": current_approval["round"],
                "image_count": current_approval["image_count"],
                "plan_sha256": current_approval["plan_sha256"],
            }
        ),
        "history_count": len(payload["approval"]["history"]),
    }
    report = {
        "ok": True,
        "job_id": payload["job_id"],
        "state": payload["state"],
        "revision": payload["revision"],
        "batch": payload["batch"],
        "approval": approval,
        "counts": counts,
        "evaluation": payload["evaluation"],
        "optimization": payload["optimization"],
        "limit": payload["usage_limit"],
        "error_category": payload["error_category"],
    }
    return EXIT_OK, _emit(report, args.json)


# ------------------------------------------------------------------------ wiring


def _positive_finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("timeout must be a positive finite number")
    return parsed


def command_prompt_search(args: argparse.Namespace) -> tuple[int, str]:
    return EXIT_OK, _emit(prompt_library.search(args.query, args.limit), args.json)


def build_parser() -> argparse.ArgumentParser:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--codex-home", default=None)
    shared.add_argument("--codex-bin", default=None)
    shared.add_argument("--generation-dir", default=None)
    shared.add_argument("--destination", default="image-factory-out")
    shared.add_argument("--json", action="store_true")

    parser = argparse.ArgumentParser(prog="image-factory", parents=[shared])
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("probe", parents=[shared])
    search = subparsers.add_parser("prompt-search", parents=[shared])
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=3)

    validate = subparsers.add_parser("validate-plan", parents=[shared])
    validate.add_argument("plan")

    quote = subparsers.add_parser("quote", parents=[shared])
    quote.add_argument("plan")

    run = subparsers.add_parser("run", parents=[shared])
    run.add_argument("--plan", required=True)
    run.add_argument("--job", required=True)
    run.add_argument("--approve", action="store_true")
    run.add_argument("--timeout", type=_positive_finite_float, default=DEFAULT_TIMEOUT_SECONDS)

    recover = subparsers.add_parser("recover", parents=[shared])
    recover.add_argument("--plan", required=True)
    recover.add_argument("--job", required=True)

    evaluate = subparsers.add_parser("evaluate", parents=[shared])
    evaluate.add_argument("--plan", required=True)
    evaluate.add_argument("--job", required=True)
    evaluate.add_argument("--scores", required=True)
    evaluate.add_argument("--advisory", default=None)
    evaluate.add_argument("--labels", default=None)

    optimize = subparsers.add_parser("optimize", parents=[shared])
    optimize.add_argument("--job", required=True)
    optimize.add_argument("--plan", required=True)
    optimize.add_argument("--scores", required=True)
    optimize.add_argument("--out", required=True)
    optimize.add_argument("--rewrites", default=None)
    optimize.add_argument("--retry-unchanged", action="append", default=None)

    status = subparsers.add_parser("status", parents=[shared])
    status.add_argument("--job", required=True)

    return parser


HANDLERS = {
    "prompt-search": command_prompt_search,
    "probe": command_probe,
    "validate-plan": command_validate_plan,
    "quote": command_quote,
    "run": command_run,
    "recover": command_recover,
    "evaluate": command_evaluate,
    "optimize": command_optimize,
    "status": command_status,
}


def run_cli(argv: list[str]) -> tuple[int, str]:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:  # argparse exits on bad usage
        return EXIT_USAGE, f"invalid arguments ({error.code})"
    handler = HANDLERS[args.command]
    try:
        if args.command in {"run", "evaluate", "optimize", "recover"}:
            try:
                preflight_mutating_command_paths(args)
            except ValueError as error:
                return EXIT_USAGE, _emit({"ok": False, "error": str(error)}, args.json)
            job_path = Path(args.job) if hasattr(args, "job") else Path(args.plan)
            with job_lock.JobLock(job_path):
                return handler(args)
        return handler(args)
    except job_lock.JobAlreadyRunningError as error:
        payload = {
            "ok": False,
            "error_category": "job_already_running",
            "error": str(error),
        }
        return EXIT_JOB_LOCKED, _emit(payload, args.json)
    except (OSError, ValueError, KeyError) as error:
        return EXIT_FAILURE, _emit({"ok": False, "error": str(error)}, args.json)


def main(argv: list[str] | None = None) -> int:
    code, output = run_cli(list(sys.argv[1:] if argv is None else argv))
    stream = sys.stdout if code == EXIT_OK else sys.stderr
    if output:
        stream.write(output + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
