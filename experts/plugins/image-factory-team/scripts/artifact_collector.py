#!/usr/bin/env python3
"""Collect the image a generation step produced and write a verifiable receipt.

Nothing here trusts the producer. Every hash, byte count, and pixel dimension in
a receipt is recomputed from the file on disk by this module, and the artifact is
published with an atomic rename so a partially written image can never be
mistaken for a finished one.

Produced images are located by diffing the generation directory before and after
the step rather than by predicting a filename. Codex names its output from an
internal session and call identifier, so a predictor would be a guess; the diff
is evidence.

Two checks exist specifically to catch a rewrite in the middle of collection:
the source is hashed again after the copy, and the published file is hashed again
after publication. Either mismatch fails the collection and removes the output
instead of recording a receipt for a file that no longer matches it.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import struct
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from plan_validator import PlanItem

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
PNG_HEADER_BYTES = 24
PLUGIN_ID = "codex-image-factory"
SCHEMA_VERSION = "1.0.0"
HASH_CHUNK = 64 * 1024
SIBLING_POLICIES = ("reject", "newest")

Snapshot = dict  # relative posix path -> (mtime_ns, size)


@dataclass(frozen=True)
class CollectFailure:
    code: str
    message: str


@dataclass(frozen=True)
class CollectResult:
    ok: bool
    receipt: dict | None = None
    failure: CollectFailure | None = None
    ignored: tuple[str, ...] = ()


def file_sha256(target: Path) -> str:
    digest = hashlib.sha256()
    with Path(target).open("rb") as handle:
        while True:
            block = handle.read(HASH_CHUNK)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def parse_png_size(target: Path) -> tuple[int, int] | None:
    """Return (width, height) for a PNG, or None when the file is not a usable PNG."""
    try:
        with Path(target).open("rb") as handle:
            header = handle.read(PNG_HEADER_BYTES)
    except OSError:
        return None
    if len(header) < PNG_HEADER_BYTES or header[:8] != PNG_MAGIC:
        return None
    width, height = struct.unpack(">II", header[16:24])
    if width <= 0 or height <= 0:
        return None
    return width, height


def snapshot(directory: Path) -> Snapshot:
    """Record every file under a directory as relpath -> (mtime_ns, size)."""
    root = Path(directory)
    if not root.is_dir():
        return {}
    entries: Snapshot = {}
    for current, _dirs, files in os.walk(root):
        for name in files:
            target = Path(current) / name
            try:
                info = target.stat()
            except OSError:
                continue
            entries[target.relative_to(root).as_posix()] = (info.st_mtime_ns, info.st_size)
    return entries


def new_entries(before: Snapshot, after: Snapshot) -> tuple[str, ...]:
    """Paths that are new or whose mtime/size changed, sorted for determinism."""
    changed = [
        relative
        for relative, signature in after.items()
        if before.get(relative) != signature
    ]
    return tuple(sorted(changed))


def _select_new_file(
    candidates: tuple[str, ...],
    generation_dir: Path,
    sibling_policy: str,
) -> tuple[Path | None, tuple[str, ...], CollectFailure | None]:
    if not candidates:
        return None, (), CollectFailure(
            "artifact_missing",
            "no new image appeared in the generation directory; nothing was produced",
        )
    if len(candidates) == 1:
        return generation_dir / candidates[0], (), None
    if sibling_policy == "reject":
        listed = ", ".join(candidates)
        return None, candidates, CollectFailure(
            "duplicate_artifact",
            f"{len(candidates)} new images appeared for a single item ({listed}); "
            "resolve which one belongs to the item, or rerun with the newest sibling policy",
        )
    newest = max(
        candidates,
        key=lambda relative: (
            (generation_dir / relative).stat().st_mtime_ns,
            relative,
        ),
    )
    return generation_dir / newest, tuple(name for name in candidates if name != newest), None


def _artifact_id(item: PlanItem) -> str:
    return f"{item.id}-r{item.round}-{item.idempotency_key[:12]}"


def _publish(source: Path, destination: Path) -> None:
    """Copy to a temporary file in the destination directory, then rename atomically."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        dir=str(destination.parent), prefix=".incoming-", suffix=".png"
    )
    os.close(handle)
    temporary = Path(temporary_name)
    try:
        shutil.copyfile(source, temporary)
        with temporary.open("rb+") as stream:
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def collect_artifact(
    *,
    item: PlanItem,
    batch_id: str,
    generation_dir: Path,
    destination_dir: Path,
    before: Snapshot,
    min_dimension: int,
    known_hashes: frozenset[str] | set[str] | tuple[str, ...] = (),
    reject_duplicates: bool = True,
    sibling_policy: str = "reject",
    now: str | None = None,
) -> CollectResult:
    if sibling_policy not in SIBLING_POLICIES:
        raise ValueError(f"sibling_policy must be one of {SIBLING_POLICIES}, got {sibling_policy!r}")

    generation_dir = Path(generation_dir)
    destination_dir = Path(destination_dir)
    after = snapshot(generation_dir)
    source, ignored, failure = _select_new_file(new_entries(before, after), generation_dir, sibling_policy)
    if failure is not None:
        return CollectResult(ok=False, failure=failure, ignored=ignored)
    assert source is not None

    size = parse_png_size(source)
    if size is None:
        return CollectResult(
            ok=False,
            failure=CollectFailure("not_a_png", f"new artifact is not a usable PNG: {source.name}"),
            ignored=ignored,
        )
    width, height = size
    if width < min_dimension or height < min_dimension:
        return CollectResult(
            ok=False,
            failure=CollectFailure(
                "below_min_dimension",
                f"{width}x{height} is below the {min_dimension}px minimum",
            ),
            ignored=ignored,
        )

    recorded_hash = file_sha256(source)
    if reject_duplicates and recorded_hash in set(known_hashes):
        return CollectResult(
            ok=False,
            failure=CollectFailure(
                "duplicate_content",
                "an identical image was already collected for this batch",
            ),
            ignored=ignored,
        )

    relative = Path(batch_id) / f"round-{item.round}" / f"{_artifact_id(item)}.png"
    destination = destination_dir / relative
    _publish(source, destination)

    source_hash_after = file_sha256(source)
    if source_hash_after != recorded_hash:
        destination.unlink(missing_ok=True)
        return CollectResult(
            ok=False,
            failure=CollectFailure(
                "hash_mismatch",
                "the source image changed while it was being collected",
            ),
            ignored=ignored,
        )

    published_hash = file_sha256(destination)
    if published_hash != recorded_hash:
        destination.unlink(missing_ok=True)
        return CollectResult(
            ok=False,
            failure=CollectFailure(
                "hash_mismatch",
                "the published image does not match the collected source",
            ),
            ignored=ignored,
        )

    session_id, call_id = _locate(source, generation_dir)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "plugin_id": PLUGIN_ID,
        "batch_id": batch_id,
        "item_id": item.id,
        "round": item.round,
        "artifact_id": _artifact_id(item),
        "path": relative.as_posix(),
        "sha256": recorded_hash,
        "bytes": source.stat().st_size,
        "width": width,
        "height": height,
        "prompt_sha256": hashlib.sha256(item.prompt.encode("utf-8")).hexdigest(),
        "idempotency_key": item.idempotency_key,
        "source": {
            "kind": "codex_image_gen",
            "session_id": session_id,
            "call_id": call_id,
            # The plugin never infers the model: Codex selects it and reports it, or not.
            "model_reported": None,
        },
        "collected_at": now or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    return CollectResult(ok=True, receipt=receipt, ignored=ignored)


def _locate(source: Path, generation_dir: Path) -> tuple[str, str]:
    """Derive the session and call identifiers from the path Codex used."""
    try:
        relative = source.relative_to(generation_dir)
    except ValueError:
        return "unknown", source.stem
    parts = relative.parts
    if len(parts) >= 2:
        return parts[-2], source.stem
    return source.parent.name or "unknown", source.stem


def verify_receipt(receipt: dict, path: Path) -> list[str]:
    """Independently re-check a receipt against the file on disk."""
    target = Path(path)
    if not target.is_file():
        return ["artifact is missing"]
    errors: list[str] = []
    actual_bytes = target.stat().st_size
    if receipt.get("bytes") != actual_bytes:
        errors.append(f"bytes mismatch: receipt says {receipt.get('bytes')}, file has {actual_bytes}")
    size = parse_png_size(target)
    if size is None:
        errors.append("artifact is not a usable PNG")
    elif (receipt.get("width"), receipt.get("height")) != size:
        errors.append(
            f"dimension mismatch: receipt says {receipt.get('width')}x{receipt.get('height')}, file is {size[0]}x{size[1]}"
        )
    actual_hash = file_sha256(target)
    if receipt.get("sha256") != actual_hash:
        errors.append(f"sha256 mismatch: receipt says {receipt.get('sha256')}, file has {actual_hash}")
    return errors
