#!/usr/bin/env python3
"""Durable, schema-checked storage for per-item artifact receipts."""

from __future__ import annotations

import json
from pathlib import Path

import artifact_collector
import atomic_json
import schema_lite


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "artifact_receipt.schema.json"


class ReceiptStoreError(ValueError):
    """A receipt is malformed, duplicated, unreadable, or fails artifact verification."""


def receipt_directory(job_path: Path) -> Path:
    return Path(str(job_path) + ".receipts")


def receipt_path(job_path: Path, idempotency_key: str) -> Path:
    return receipt_directory(job_path) / f"{idempotency_key}.json"


def manifest_path(job_path: Path) -> Path:
    return Path(str(job_path) + ".receipts.json")


def _validate(receipt: object, source: Path | None = None) -> dict:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    violations = schema_lite.validate(receipt, schema)
    if violations:
        location = f" at {source}" if source is not None else ""
        raise ReceiptStoreError(
            f"receipt{location} does not conform to its schema: {'; '.join(violations)}"
        )
    assert isinstance(receipt, dict)
    return receipt


def write_receipt(job_path: Path, receipt: dict) -> Path:
    validated = _validate(receipt)
    target = receipt_path(job_path, validated["idempotency_key"])
    if target.exists():
        raise ReceiptStoreError(
            f"duplicate idempotency key {validated['idempotency_key']!r}"
        )
    atomic_json.write_json_atomic(target, validated)
    return target


def _artifact_path(destination_dir: Path, receipt: dict) -> Path:
    destination = Path(destination_dir).resolve()
    target = (destination / receipt["path"]).resolve()
    if target != destination and destination not in target.parents:
        raise ReceiptStoreError(f"receipt artifact path escapes destination: {receipt['path']!r}")
    return target


def _verify_artifact(receipt: dict, source: Path, destination_dir: Path) -> None:
    artifact = _artifact_path(destination_dir, receipt)
    verification = artifact_collector.verify_receipt(receipt, artifact)
    if verification:
        raise ReceiptStoreError(
            f"receipt at {source} failed artifact verification: {'; '.join(verification)}"
        )


def _load_legacy_manifest(
    job_path: Path,
    destination_dir: Path,
    idempotency_keys: set[str] | None = None,
) -> dict[str, dict]:
    source = manifest_path(job_path)
    if not source.exists():
        return {}
    try:
        decoded = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ReceiptStoreError(f"receipt manifest at {source} could not be read: {error}") from error
    if not isinstance(decoded, list):
        raise ReceiptStoreError(f"receipt manifest at {source} must be a JSON array")

    loaded: dict[str, dict] = {}
    for index, candidate in enumerate(decoded):
        receipt = _validate(candidate, Path(f"{source}[{index}]"))
        key = receipt["idempotency_key"]
        if idempotency_keys is not None and key not in idempotency_keys:
            continue
        if key in loaded:
            raise ReceiptStoreError(f"duplicate idempotency key {key!r} in {source}")
        _verify_artifact(receipt, source, destination_dir)
        loaded[key] = receipt
    return loaded


def load_verified_receipts(
    job_path: Path,
    destination_dir: Path,
    idempotency_keys: set[str] | None = None,
) -> dict[str, dict]:
    loaded = _load_legacy_manifest(job_path, destination_dir, idempotency_keys)
    directory = receipt_directory(job_path)
    if not directory.exists():
        return loaded
    if not directory.is_dir():
        raise ReceiptStoreError(f"receipt store is not a directory: {directory}")

    for source in sorted(directory.glob("*.json")):
        if idempotency_keys is not None and source.stem not in idempotency_keys:
            continue
        try:
            decoded = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise ReceiptStoreError(f"receipt at {source} could not be read: {error}") from error
        receipt = _validate(decoded, source)
        key = receipt["idempotency_key"]
        if source.name != f"{key}.json":
            raise ReceiptStoreError(
                f"receipt filename {source.name!r} does not match idempotency key {key!r}"
            )
        if key in loaded and loaded[key] != receipt:
            raise ReceiptStoreError(
                f"conflicting receipts for idempotency key {key!r}"
            )
        _verify_artifact(receipt, source, destination_dir)
        loaded[key] = receipt
    return loaded


def rebuild_manifest(job_path: Path, receipts: dict[str, dict]) -> Path:
    # The compatibility manifest historically used append order. The verified
    # loader inserts legacy entries first and newly persisted entries after them.
    ordered = list(receipts.values())
    for receipt in ordered:
        _validate(receipt)
    target = manifest_path(job_path)
    atomic_json.write_json_atomic(target, ordered)
    return target
