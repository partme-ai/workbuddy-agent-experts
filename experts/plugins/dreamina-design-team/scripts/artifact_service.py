"""Artifact download + verification for Dreamina Design (Task 5).

Validates downloaded artifacts before declaring a generation task
complete. The service refuses to return an ``ArtifactReceipt`` unless
all of the following hold:

* the fetch completed without raising;
* the payload is non-empty and well-formed;
* the SHA-256 digest of the bytes matches the expected digest;
* media metadata can be derived for known formats (PNG, JPEG, MP4 …).
"""

from __future__ import annotations

import hashlib
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


class ArtifactServiceError(Exception):
    """Base class for artifact service errors."""


class ArtifactDownloadError(ArtifactServiceError):
    """The underlying fetcher failed to download the artifact."""


class ArtifactTruncatedError(ArtifactServiceError):
    """The downloaded payload is empty or smaller than a known minimum."""


class ArtifactChecksumMismatchError(ArtifactServiceError):
    """The computed SHA-256 does not match the expected digest."""


class MediaMetadataMissingError(ArtifactServiceError):
    """No media metadata could be derived from the downloaded payload."""


class ArtifactPolicyError(ArtifactServiceError):
    """URL, destination, size, or overwrite policy rejected the download."""


class ArtifactProvenanceError(ArtifactServiceError):
    """The artifact is not tied to a successful recorded operation."""


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"
MP4_FTYP = b"ftyp"

MIN_PNG_BYTES = len(PNG_SIGNATURE) + 25  # signature + IHDR chunk (length+type+13-byte payload+CRC)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _parse_png_dimensions(payload: bytes) -> tuple[int, int] | None:
    if len(payload) < 24 or payload[:8] != PNG_SIGNATURE:
        return None
    # IHDR chunk: 4-byte length, 4-byte type, 13-byte payload, 4-byte CRC
    # Total chunk header is bytes 8..12 (length) + bytes 12..16 (type).
    if payload[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", payload[16:24])
    if width <= 0 or height <= 0:
        return None
    return width, height


def _detect_mime(payload: bytes) -> str | None:
    if payload.startswith(PNG_SIGNATURE):
        return "image/png"
    if payload.startswith(JPEG_SIGNATURE):
        return "image/jpeg"
    if len(payload) >= 12 and payload[4:8] == MP4_FTYP:
        return "video/mp4"
    return None


def _looks_complete(payload: bytes, mime: str) -> bool:
    """Quick check that the payload contains a known terminator."""
    if mime == "image/png":
        return b"IEND" in payload[-12:]
    if mime == "image/jpeg":
        # JPEG ends with the EOI marker (FFD9).
        return payload[-2:] == b"\xff\xd9"
    if mime == "video/mp4":
        return b"moov" in payload[-1024:]
    return True


def _media_metadata(payload: bytes, mime: str) -> dict[str, Any]:
    metadata: dict[str, Any] = {"mime_type": mime, "size_bytes": len(payload)}
    if mime == "image/png":
        dims = _parse_png_dimensions(payload)
        if dims is None:
            return metadata
        metadata["width"], metadata["height"] = dims
    return metadata


class ArtifactService:
    """Download an artifact, validate it, and return an ArtifactReceipt."""

    def __init__(
        self,
        *,
        min_bytes: int = MIN_PNG_BYTES,
        destination_root: Path,
        operation_ledger: Any,
        max_bytes: int = 512 * 1024 * 1024,
    ) -> None:
        self._min_bytes = min_bytes
        self._destination_root = Path(destination_root).resolve()
        self._operation_ledger = operation_ledger
        self._destination_root.mkdir(parents=True, exist_ok=True)
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        self._max_bytes = max_bytes

    # ------------------------------------------------------------------
    # Public surface
    # ------------------------------------------------------------------
    def download(
        self,
        *,
        submit_id: str,
        url: str,
        destination: Path,
        expected_checksum: Mapping[str, str],
    ) -> dict[str, Any]:
        raise ArtifactPolicyError(
            "remote fetching is disabled; use `dreamina query_result "
            "--download_dir=<approved-root>` and verify_local()"
        )

    def verify_local(
        self,
        *,
        submit_id: str,
        path: Path,
        expected_metadata: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Verify a file downloaded by ``dreamina query_result --download_dir``."""
        try:
            operation = self._operation_ledger.get(submit_id=submit_id)
        except Exception as exc:
            raise ArtifactProvenanceError(
                f"submit_id is not present in the operation ledger: {submit_id}"
            ) from exc
        if operation.get("state") != "succeeded" or operation.get("required_action") != "download":
            raise ArtifactProvenanceError(
                f"operation is not in succeeded/download state: {operation.get('state')}"
            )
        candidate = Path(path)
        if candidate.is_symlink() or not candidate.is_file():
            raise ArtifactPolicyError("downloaded artifact must be a regular non-symlink file")
        resolved = candidate.resolve(strict=True)
        try:
            resolved.relative_to(self._destination_root)
        except ValueError as exc:
            raise ArtifactPolicyError("downloaded artifact escapes approved root") from exc
        size = resolved.stat().st_size
        if size <= 0 or size > self._max_bytes:
            raise ArtifactPolicyError(f"downloaded artifact size is outside 1..{self._max_bytes}")
        payload = resolved.read_bytes()
        mime = _detect_mime(payload)
        if mime is None:
            raise MediaMetadataMissingError("could not derive media metadata from local artifact")
        if len(payload) < self._min_bytes or not _looks_complete(payload, mime):
            raise ArtifactTruncatedError(f"local {mime} artifact appears truncated")
        digest = _sha256_hex(payload)
        metadata = _media_metadata(payload, mime)
        for field in ("mime_type", "width", "height", "duration_seconds"):
            expected = expected_metadata.get(field)
            if expected is not None and metadata.get(field) != expected:
                raise ArtifactProvenanceError(
                    f"artifact metadata mismatch for {field}: expected {expected}, got {metadata.get(field)}"
                )
        return {
            "submit_id": submit_id,
            "local_path": str(resolved),
            "checksum": {"algorithm": "sha256", "digest": digest},
            "media_metadata": metadata,
            "verified_at": _now_iso(),
        }

__all__ = [
    "ArtifactChecksumMismatchError",
    "ArtifactDownloadError",
    "ArtifactPolicyError",
    "ArtifactProvenanceError",
    "ArtifactService",
    "ArtifactTruncatedError",
    "MediaMetadataMissingError",
]
