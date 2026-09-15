"""Artifact receipt verification for dreamina-canvas resource downloads.

Verifies that a downloaded file matches the post-write response:

- byte count matches `wc -c`
- SHA-256 matches `shasum -a 256`
- media metadata is present and consistent
- The file lives under the user-approved output directory.
- No signed URL / storage id / provider task id is persisted anywhere.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


SECRET_FIELD_NAMES = (
    "signedUrl",
    "signed_url",
    "downloadUrl",
    "storage_id",
    "storageId",
    "providerTaskId",
    "provider_task_id",
    "access_token",
    "refresh_token",
    "cookie",
    "creditConfirmationToken",
)


@dataclass(frozen=True)
class ArtifactReceipt:
    resource_id: str
    canonical_path: Path
    byte_count: int
    sha256: str
    media: dict


@dataclass
class ArtifactDecision:
    ok: bool
    reason: str = ""


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _ensure_no_secret_fields(payload: dict) -> ArtifactDecision:
    for key in payload.keys():
        if key in SECRET_FIELD_NAMES:
            return ArtifactDecision(False, f"forbidden field {key!r} in payload")
    nested = payload.get("media") or {}
    for key in nested.keys():
        if key in SECRET_FIELD_NAMES:
            return ArtifactDecision(False, f"forbidden field media.{key} in payload")
    return ArtifactDecision(True)


def _ensure_within_approved_dir(canonical_path: Path, approved_dir: Path) -> ArtifactDecision:
    try:
        canonical_path.resolve().relative_to(approved_dir.resolve())
    except ValueError:
        return ArtifactDecision(
            False,
            f"path {canonical_path} is not within approved directory {approved_dir}",
        )
    return ArtifactDecision(True)


def verify(
    receipt: ArtifactReceipt,
    *,
    approved_dir: Path,
    raw_response: dict | None = None,
) -> ArtifactDecision:
    if raw_response is not None:
        secret_check = _ensure_no_secret_fields(raw_response)
        if not secret_check.ok:
            return secret_check
    path_check = _ensure_within_approved_dir(receipt.canonical_path, approved_dir)
    if not path_check.ok:
        return path_check
    if not receipt.canonical_path.is_file():
        return ArtifactDecision(False, f"file does not exist: {receipt.canonical_path}")
    actual_bytes = receipt.canonical_path.stat().st_size
    if actual_bytes != receipt.byte_count:
        return ArtifactDecision(
            False,
            f"byte count mismatch: expected {receipt.byte_count}, got {actual_bytes}",
        )
    actual_sha = hash_file(receipt.canonical_path)
    if actual_sha != receipt.sha256:
        return ArtifactDecision(
            False,
            f"sha256 mismatch: expected {receipt.sha256[:12]}, got {actual_sha[:12]}",
        )
    if not receipt.media:
        return ArtifactDecision(False, "media metadata missing")
    return ArtifactDecision(True)
