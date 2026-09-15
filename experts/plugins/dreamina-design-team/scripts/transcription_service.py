"""Local-only Whisper transcription through the enrolled media adapter."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.media_adapter import MediaAdapterError, MediaOutputError
from scripts.json_contracts import ContractValidationError, canonical_fingerprint, validate_contract
from scripts.trusted_media_tools import TrustedMediaToolError


_LANGUAGE = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
_MAX_SEGMENTS = 10_000
_MAX_SEGMENT_TEXT_LENGTH = 500
_MAX_TRANSCRIPT_SECONDS = 21_600
_MAX_SOURCE_BYTES = 512 * 1024 * 1024
_MAX_JSON_BYTES = 4 * 1024 * 1024
_WHISPER_LANGUAGES = frozenset({"zh", "en", "ja", "ko", "fr", "de", "es", "it", "pt", "ru", "ar", "hi"})


class TranscriptionUnavailableError(RuntimeError):
    """No enrolled local ASR provider can produce trustworthy evidence."""

    status = "blocked"
    reason = "asr_provider_unavailable"


class WhisperCliProvider:
    """Invoke one fixed local Whisper model using JSON-only output."""

    def __init__(self, adapter: Any, model_path: Path, output_root: Path) -> None:
        self._adapter = adapter
        self._model = self._regular_absolute(model_path, "model")
        self._model_stat = self._model.stat()
        self._model_sha256 = self._digest_file(self._model, _MAX_SOURCE_BYTES)
        identity = getattr(adapter, "executable_identity", None)
        if identity is None and hasattr(adapter, "trusted_identity"):
            identity = adapter.trusted_identity("whisper")
        if (not isinstance(identity, Mapping) or identity.get("kind") != "whisper"
                or not isinstance(identity.get("path"), str)
                or re.fullmatch(r"[a-f0-9]{64}", str(identity.get("sha256"))) is None):
            raise ValueError("Whisper executable identity must be enrolled and pinned")
        self._executable_identity = dict(identity)
        self._output_root = Path(output_root)
        if not self._output_root.is_absolute() or self._output_root.is_symlink():
            raise ValueError("Whisper output root must be an absolute non-symlink directory")
        if not self._output_root.exists():
            self._output_root.mkdir(mode=0o700, parents=True)
        self._output_root = self._output_root.resolve(strict=True)
        metadata = self._output_root.stat()
        if (not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o700):
            raise ValueError("Whisper output root must be private mode 0700")

    def transcribe(self, audio_path: Path, *, language: str | None) -> list[dict[str, Any]]:
        source = self._regular_absolute(audio_path, "audio")
        if language is not None and _LANGUAGE.fullmatch(language) is None:
            raise ValueError("language must be a valid BCP-47 tag")
        whisper_language = language.split("-", 1)[0].lower() if language is not None else None
        if whisper_language is not None and whisper_language not in _WHISPER_LANGUAGES:
            raise ValueError("language is not supported by the enrolled Whisper contract")
        self._reverify_model()
        call_root = Path(tempfile.mkdtemp(prefix="whisper-", dir=self._output_root))
        os.chmod(call_root, 0o700)
        try:
            staged = call_root / ("source" + source.suffix.lower())
            source_digest = self._copy_pinned_source(source, staged)
            argv = ["--model", str(self._model), "--output_format", "json", "--output_dir", str(call_root)]
            if whisper_language is not None:
                argv.extend(["--language", whisper_language])
            result = self._adapter.run("whisper", [*argv, str(staged)], timeout_seconds=1800)
            if result.exit_code != 0:
                raise MediaOutputError(f"whisper failed with exit {result.exit_code}")
            outputs = list(call_root.glob("*.json"))
            expected = call_root / f"{staged.stem}.json"
            if outputs != [expected]:
                raise MediaOutputError("whisper must emit exactly the expected JSON artifact")
            payload = self._read_private_json(expected)
        finally:
            shutil.rmtree(call_root, ignore_errors=True)
        if not isinstance(payload, dict) or not isinstance(payload.get("segments"), list):
            raise MediaOutputError("whisper JSON lacks segments")
        detected = payload.get("language")
        effective_language = language or detected
        if not isinstance(effective_language, str) or _LANGUAGE.fullmatch(effective_language) is None:
            raise MediaOutputError("whisper JSON lacks a valid language")
        self._last_evidence = {
            "source_sha256": source_digest,
            "model": {"path": str(self._model), "sha256": self._model_sha256},
            "executable": dict(self._executable_identity),
            "language": effective_language,
        }
        return self._normalize(payload["segments"], effective_language, source_digest)

    def _normalize(self, segments: Sequence[Mapping[str, Any]], language: str, digest: str) -> list[dict[str, Any]]:
        if len(segments) > _MAX_SEGMENTS:
            raise ValueError("whisper segment count exceeds the local evidence limit")
        normalized: list[dict[str, Any]] = []
        previous_end = 0.0
        for item in segments:
            if not isinstance(item, Mapping):
                raise MediaOutputError("whisper segment must be an object")
            start, end = item.get("start"), item.get("end")
            avg_logprob, no_speech = item.get("avg_logprob"), item.get("no_speech_prob")
            text = item.get("text")
            if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in (start, end, avg_logprob, no_speech)):
                raise ValueError("segment times and probability evidence must be finite numbers")
            if (start < 0 or end <= start or start < previous_end or end > _MAX_TRANSCRIPT_SECONDS
                    or not isinstance(text, str) or not text.strip()
                    or len(text) > _MAX_SEGMENT_TEXT_LENGTH or not -20 <= avg_logprob <= 0
                    or not 0 <= no_speech <= 1):
                raise ValueError("segment timeline, text, or probability evidence is invalid")
            normalized.append({
                "start": float(start), "end": float(end), "language": language,
                "text": " ".join(text.split()), "avg_logprob": float(avg_logprob),
                "no_speech_probability": float(no_speech),
                "requires_review": avg_logprob < -0.5 or no_speech > 0.5, "provider": "whisper",
                "model": str(self._model), "artifact_sha256": digest,
            })
            previous_end = float(end)
        return normalized

    @staticmethod
    def _regular_absolute(path: Path, label: str) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute() or candidate.is_symlink() or not candidate.is_file():
            raise ValueError(f"{label} path must be an absolute regular non-symlink file")
        resolved = candidate.resolve(strict=True)
        metadata = resolved.stat()
        if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
            raise ValueError(f"{label} path must be an owner-only private file")
        return resolved

    def _reverify_model(self) -> None:
        current = self._model.stat()
        if ((current.st_dev, current.st_ino, current.st_size) !=
                (self._model_stat.st_dev, self._model_stat.st_ino, self._model_stat.st_size)
                or self._digest_file(self._model, _MAX_SOURCE_BYTES) != self._model_sha256):
            raise ValueError("Whisper model identity changed after enrollment")

    @staticmethod
    def _digest_file(path: Path, maximum: int) -> str:
        digest = hashlib.sha256(); total = 0
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                total += len(chunk)
                if total > maximum:
                    raise ValueError("private media input exceeds the configured bound")
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _copy_pinned_source(source: Path, staged: Path) -> str:
        descriptor = os.open(source, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        digest = hashlib.sha256(); total = 0
        try:
            before = os.fstat(descriptor)
            with staged.open("xb") as writer:
                os.chmod(staged, 0o600)
                while chunk := os.read(descriptor, 1024 * 1024):
                    total += len(chunk)
                    if total > _MAX_SOURCE_BYTES:
                        raise ValueError("source audio exceeds the configured bound")
                    digest.update(chunk); writer.write(chunk)
                writer.flush(); os.fsync(writer.fileno())
            after = os.fstat(descriptor)
            current = os.stat(source, follow_symlinks=False)
            identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
            if identity(before) != identity(after) or identity(after) != identity(current):
                raise ValueError("source audio changed during pinned intake")
            return digest.hexdigest()
        finally:
            os.close(descriptor)

    @staticmethod
    def _read_private_json(path: Path) -> Any:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            metadata = os.fstat(descriptor)
            if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid()
                    or stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_size > _MAX_JSON_BYTES):
                raise MediaOutputError("whisper JSON artifact is unsafe or oversized")
            data = os.read(descriptor, _MAX_JSON_BYTES + 1)
            if len(data) != metadata.st_size:
                raise MediaOutputError("whisper JSON artifact changed while reading")
            current = os.stat(path, follow_symlinks=False)
            if (current.st_dev, current.st_ino) != (metadata.st_dev, metadata.st_ino):
                raise MediaOutputError("whisper JSON artifact path changed while reading")
            return json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MediaOutputError("whisper JSON artifact is invalid") from exc
        finally:
            os.close(descriptor)


class TranscriptionService:
    """Expose explicit blocked results while allowing strict callers to fail closed."""

    def __init__(self, provider: WhisperCliProvider, *, project_store: Any | None = None) -> None:
        self._provider = provider
        self._project_store = project_store

    def transcribe(self, audio_path: Path, *, language: str | None) -> dict[str, Any]:
        try:
            segments = self._provider.transcribe(audio_path, language=language)
        except (MediaOutputError, ValueError, json.JSONDecodeError) as exc:
            return {"status": "degraded", "reason": "asr_output_invalid", "segments": [], "detail": type(exc).__name__}
        except (TrustedMediaToolError, OSError) as exc:
            return {"status": "blocked", "reason": "asr_provider_unavailable", "segments": [], "detail": type(exc).__name__}
        except MediaAdapterError as exc:
            return {"status": "blocked", "reason": "asr_provider_unavailable", "segments": [], "detail": type(exc).__name__}
        evidence = self._provider._last_evidence
        return {"status": "complete", "provider": "whisper", "model": evidence["model"],
                "executable": evidence["executable"], "source_sha256": evidence["source_sha256"],
                "language": evidence["language"], "segments": segments}

    def require_transcript(self, audio_path: Path, *, language: str | None) -> list[dict[str, Any]]:
        result = self.transcribe(audio_path, language=language)
        if result["status"] != "complete":
            raise TranscriptionUnavailableError(result["reason"])
        return result["segments"]

    def transcribe_and_commit(self, project_id: str, audio_path: Path, *, language: str | None) -> dict[str, Any]:
        """Persist only complete local-ASR evidence as one immutable project version."""
        if self._project_store is None:
            raise RuntimeError("transcript persistence requires a VideoProjectStore")
        result = self.transcribe(audio_path, language=language)
        if result["status"] != "complete":
            raise TranscriptionUnavailableError(result["reason"])
        core = {"schema_version": "1.0", "project_id": project_id, **result}
        payload = {**core, "transcript_fingerprint": canonical_fingerprint(core)}
        return self._project_store.write_version(
            project_id, "transcript", payload, schema_name="transcript_receipt.schema.json")

    def verify_receipt(self, receipt: Mapping[str, Any]) -> dict[str, Any]:
        """Resolve an exact immutable transcript version and reject caller-created evidence."""
        if self._project_store is None:
            raise ContractValidationError("transcript verification requires a VideoProjectStore")
        candidate = json.loads(json.dumps(dict(receipt), ensure_ascii=False, allow_nan=False))
        validate_contract(candidate, "transcript_receipt.schema.json")
        persisted = self._project_store.read_version(
            candidate["project_id"], "transcript", candidate["version"], "transcript_receipt.schema.json")
        if persisted != candidate:
            raise ContractValidationError("transcript receipt does not match persisted evidence")
        core = {key: value for key, value in candidate.items() if key not in {"version", "transcript_fingerprint"}}
        if candidate["transcript_fingerprint"] != canonical_fingerprint(core):
            raise ContractValidationError("transcript receipt fingerprint is invalid")
        return candidate


__all__ = ["TranscriptionService", "TranscriptionUnavailableError", "WhisperCliProvider"]
