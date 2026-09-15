"""Rights-aware audio planning and local narration providers."""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import re
import stat
import tempfile
import secrets
import fcntl
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from scripts.json_contracts import ContractValidationError, canonical_fingerprint, validate_contract


AUDIO_POLICIES = frozenset({"full_redesign", "preserve_authorized_audio", "subtitles_only", "silent"})
AUDIO_CLASSES = frozenset({"voice", "dialogue", "music", "effects", "ambience"})
_DIGEST = re.compile(r"^[a-f0-9]{64}$")
_ATTESTATION_DOMAIN = b"codex-dreamina-design/audio-artifact/v1\x00"


class AudioReceiptKeyUnavailableError(PermissionError):
    """The durable audio receipt key is missing, replaced, or unsafe."""


class FileAudioReceiptKeyStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else Path.home() / ".config/codex-dreamina-design/audio-receipt.key"
        self.marker_path = self.path.with_name(self.path.name + ".initialized")
        self.history_path = self.path.with_name(self.path.name + ".bootstrap-history")
        self._ensure_private_parent()
        parent = self._validate_dir(self.path.parent, exact_private=True)
        self._parent_identity = (parent.st_dev, parent.st_ino)

    @staticmethod
    def _validate_dir(path: Path, *, exact_private: bool) -> os.stat_result:
        try:
            value = path.lstat()
        except OSError as exc:
            raise AudioReceiptKeyUnavailableError("audio key directory cannot be inspected") from exc
        if (not stat.S_ISDIR(value.st_mode) or path.is_symlink() or value.st_uid != os.getuid() or
                (exact_private and stat.S_IMODE(value.st_mode) != 0o700)):
            raise AudioReceiptKeyUnavailableError("audio key directory is unsafe")
        return value

    def _ensure_private_parent(self) -> None:
        parent = self.path.parent
        if parent.exists() or parent.is_symlink():
            self._validate_dir(parent, exact_private=True)
            return
        missing = []
        cursor = parent
        while not cursor.exists() and not cursor.is_symlink():
            missing.append(cursor.name)
            cursor = cursor.parent
        self._validate_dir(cursor, exact_private=False)
        descriptor = os.open(cursor, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0))
        try:
            for name in reversed(missing):
                try:
                    os.mkdir(name, 0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
                child = os.open(name, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0), dir_fd=descriptor)
                os.close(descriptor)
                descriptor = child
                current = os.fstat(descriptor)
                if current.st_uid != os.getuid() or stat.S_IMODE(current.st_mode) != 0o700:
                    raise AudioReceiptKeyUnavailableError("audio key directory is unsafe")
        except OSError as exc:
            raise AudioReceiptKeyUnavailableError("audio key directory cannot be created safely") from exc
        finally:
            os.close(descriptor)

    def _read_private_file(self, path: Path, *, maximum: int) -> bytes:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        parent_fd = os.open(self.path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0))
        try:
            parent_stat = os.fstat(parent_fd)
            if (parent_stat.st_dev, parent_stat.st_ino) != self._parent_identity:
                raise AudioReceiptKeyUnavailableError("audio key directory identity changed")
            fd = os.open(path.name, flags, dir_fd=parent_fd)
        except FileNotFoundError as exc:
            os.close(parent_fd)
            raise AudioReceiptKeyUnavailableError("audio receipt initialization state is missing") from exc
        except OSError as exc:
            os.close(parent_fd)
            raise AudioReceiptKeyUnavailableError("audio receipt initialization state cannot be opened") from exc
        try:
            before = os.fstat(fd); data = os.read(fd, maximum + 1); after = os.fstat(fd)
            current = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        finally:
            os.close(fd)
            os.close(parent_fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid() or
                stat.S_IMODE(before.st_mode) != 0o600 or len(data) > maximum or
                (before.st_dev, before.st_ino, before.st_size) != (after.st_dev, after.st_ino, after.st_size) or
                (current.st_dev, current.st_ino) != (after.st_dev, after.st_ino)):
            raise AudioReceiptKeyUnavailableError("audio receipt initialization state is unsafe")
        return data

    def load_existing(self) -> bytes:
        parent = self._validate_dir(self.path.parent, exact_private=True)
        if (parent.st_dev, parent.st_ino) != self._parent_identity:
            raise AudioReceiptKeyUnavailableError("audio key directory identity changed")
        key = self._read_private_file(self.path, maximum=32)
        if len(key) != 32:
            raise AudioReceiptKeyUnavailableError("audio receipt key is invalid")
        marker = self._read_private_file(self.marker_path, maximum=512)
        key_id = hashlib.sha256(key).hexdigest()
        expected = hmac.new(key, b"codex-dreamina-design/audio-key-marker/v1\x00" + key_id.encode(), hashlib.sha256).hexdigest()
        try:
            payload = json.loads(marker.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AudioReceiptKeyUnavailableError("audio receipt initialization marker is invalid") from exc
        if payload != {"version": 1, "key_id": key_id, "seal": expected}:
            raise AudioReceiptKeyUnavailableError("audio receipt initialization marker does not match key")
        return key

    def initialize(self, approval_provider: Any, *, action: str, purpose: str) -> bytes:
        """Create a receipt identity only after native approval bound to its path and new key ID."""
        if action not in {"first_bootstrap", "rebootstrap"} or not isinstance(purpose, str) or not purpose.strip():
            raise AudioReceiptKeyUnavailableError("audio receipt initialization request is invalid")
        self._validate_dir(self.path.parent, exact_private=True)
        lock_fd = os.open(self.path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0))
        try:
            parent_stat = os.fstat(lock_fd)
            if (parent_stat.st_dev, parent_stat.st_ino) != self._parent_identity:
                raise AudioReceiptKeyUnavailableError("audio key directory identity changed")
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            def exists(name: str) -> bool:
                try:
                    os.stat(name, dir_fd=lock_fd, follow_symlinks=False)
                    return True
                except FileNotFoundError:
                    return False
            key_exists = exists(self.path.name)
            marker_exists = exists(self.marker_path.name)
            if key_exists or marker_exists:
                if not (key_exists and marker_exists):
                    raise AudioReceiptKeyUnavailableError("audio receipt initialization state is incomplete")
                return self.load_existing()
            history_exists = exists(self.history_path.name)
            expected_action = "rebootstrap" if history_exists else "first_bootstrap"
            if action != expected_action:
                raise AudioReceiptKeyUnavailableError(f"audio receipt key requires explicit {expected_action}")
            key = secrets.token_bytes(32)
            key_id = hashlib.sha256(key).hexdigest()
            impact = ("previous signed receipts become unverifiable" if action == "rebootstrap" else
                      "a new local signing identity will be created")
            if approval_provider is None or not hasattr(approval_provider, "confirm_audio_receipt_key_initialization"):
                raise AudioReceiptKeyUnavailableError("native approval provider is required")
            token = approval_provider.confirm_audio_receipt_key_initialization(
                key_store_path=str(self.path), action=action, new_key_id=key_id,
                purpose=purpose.strip(), impact=impact,
            )
            if token != "native-audio-receipt-key-confirmed":
                raise AudioReceiptKeyUnavailableError("native approval was not granted")
            seal = hmac.new(key, b"codex-dreamina-design/audio-key-marker/v1\x00" + key_id.encode(), hashlib.sha256).hexdigest()
            marker = json.dumps({"version": 1, "key_id": key_id, "seal": seal}, sort_keys=True, separators=(",", ":")).encode()
            created = []
            try:
                for name, data in ((self.path.name, key), (self.marker_path.name, marker)):
                    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=lock_fd)
                    created.append(name)
                    try:
                        os.write(fd, data); os.fsync(fd)
                    finally:
                        os.close(fd)
                if not history_exists:
                    history = json.dumps({"version": 1}, sort_keys=True, separators=(",", ":")).encode()
                    fd = os.open(self.history_path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=lock_fd)
                    created.append(self.history_path.name)
                    try:
                        os.write(fd, history); os.fsync(fd)
                    finally:
                        os.close(fd)
                os.fsync(lock_fd)
            except Exception:
                for name in reversed(created):
                    try:
                        os.unlink(name, dir_fd=lock_fd)
                    except FileNotFoundError:
                        pass
                raise
            return self.load_existing()
        finally:
            os.close(lock_fd)

    def load(self, *, allow_create: bool) -> bytes:
        """Compatibility shim; creation is permitted only through initialize()."""
        if allow_create:
            raise AudioReceiptKeyUnavailableError("audio receipt key requires explicit initialization")
        return self.load_existing()


class AudioRightsError(PermissionError):
    """Audio reuse or supplied media lacks exact rights evidence."""


class NarrationProviderError(RuntimeError):
    """Narration request or artifact is invalid."""


def _digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            result.update(chunk)
    return result.hexdigest()


def _verify_private_artifact(path: Path, expected_digest: str, expected_size: int) -> None:
    """Hash one owned 0400/0600 regular file through a no-follow held descriptor."""
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(descriptor)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid()
                or stat.S_IMODE(before.st_mode) not in {0o400, 0o600} or before.st_size != expected_size):
            raise ContractValidationError("audio artifact owner, mode, type, or size is invalid")
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
        after = os.fstat(descriptor)
        current = os.lstat(path)
        if (digest.hexdigest() != expected_digest
                or (before.st_dev, before.st_ino, before.st_size) != (after.st_dev, after.st_ino, after.st_size)
                or (after.st_dev, after.st_ino) != (current.st_dev, current.st_ino)):
            raise ContractValidationError("audio artifact identity changed during verification")
    finally:
        os.close(descriptor)


def _artifact_receipt(*, provider: str, path: Path, mime_type: str, artifact_role: str, kind: str,
                      rights_declared: Sequence[str], approved_root: str | None,
                      source: str, voice: str | None, model: str | None, key_store: Any) -> dict[str, Any]:
    core = {"artifact_role": artifact_role, "provider": provider, "path": str(path), "sha256": _digest(path),
            "size_bytes": path.stat().st_size, "mime_type": mime_type,
            "provenance": {"kind": kind, "rights_declared": list(rights_declared),
                           "approved_root": approved_root, "source": source,
                           "voice": voice, "model": model, "source_voice_cloned": False}}
    key = key_store.load_existing() if hasattr(key_store, "load_existing") else key_store.load(allow_create=False)
    key_id = hashlib.sha256(key).hexdigest()
    signed = {**core, "attestation_version": 1, "attestation_key_id": key_id}
    signature = hmac.new(key, _ATTESTATION_DOMAIN + json.dumps(signed, sort_keys=True, separators=(",", ":")).encode(), hashlib.sha256).hexdigest()
    return {**signed, "attestation": signature}


def _require_artifact(value: Mapping[str, Any], *, role: str, key_store: Any, required_right: str | None = None) -> dict[str, Any]:
    expected = {"artifact_role", "provider", "path", "sha256", "size_bytes", "mime_type", "provenance", "attestation", "attestation_version", "attestation_key_id"}
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ContractValidationError("audio artifact receipt is incomplete or provider is forbidden")
    provenance = value.get("provenance")
    pfields = {"kind", "rights_declared", "approved_root", "source", "voice", "model", "source_voice_cloned"}
    if not isinstance(provenance, Mapping) or set(provenance) != pfields or provenance.get("source_voice_cloned") is not False:
        raise ContractValidationError("audio artifact provenance is incomplete")
    artifact_role = value.get("artifact_role")
    rights = provenance.get("rights_declared")
    role_rights = {"new_narration": ["voice"], "existing_voice": ["voice"],
                   "existing_dialogue": ["dialogue"], "existing_voice_dialogue": ["dialogue", "voice"],
                   "music": ["music"], "effect": ["effects"], "ambience": ["ambience"],
                   "subtitle_srt": ["subtitles"], "subtitle_ass": ["subtitles"]}
    common_existing = value.get("provider") == "existing-audio" and value.get("mime_type") == "audio/wav" and provenance.get("kind") == "user_supplied" and provenance.get("source") == "user_supplied" and provenance.get("voice") is None and provenance.get("model") is None
    valid_role = artifact_role == role and rights == role_rights.get(role) and (
        (role == "new_narration" and value.get("provider") == "macos-say" and value.get("mime_type") == "audio/aiff" and provenance.get("kind") == "new_narration" and provenance.get("source") == "rewritten_script" and isinstance(provenance.get("voice"), str) and bool(provenance.get("voice")) and provenance.get("model") == "macos-say") or
        (role in {"existing_voice", "existing_dialogue", "existing_voice_dialogue", "music", "effect", "ambience"} and common_existing) or
        (role == "subtitle_srt" and value.get("provider") == "subtitle-service" and value.get("mime_type") == "application/x-subrip" and provenance.get("kind") == "generated_subtitle" and provenance.get("source") in {"rewritten_script", "narration_timing"} and provenance.get("voice") is None and provenance.get("model") is None) or
        (role == "subtitle_ass" and value.get("provider") == "subtitle-service" and value.get("mime_type") == "text/x-ssa" and provenance.get("kind") == "generated_subtitle" and provenance.get("source") in {"rewritten_script", "narration_timing"} and provenance.get("voice") is None and provenance.get("model") is None)
    )
    if not valid_role:
        raise ContractValidationError("audio artifact role fields are inconsistent")
    core = {key: value[key] for key in expected if key != "attestation"}
    key = key_store.load_existing() if hasattr(key_store, "load_existing") else key_store.load(allow_create=False)
    if value.get("attestation_version") != 1 or value.get("attestation_key_id") != hashlib.sha256(key).hexdigest():
        raise AudioReceiptKeyUnavailableError("audio receipt was signed by another key")
    wanted = hmac.new(key, _ATTESTATION_DOMAIN + json.dumps(core, sort_keys=True, separators=(",", ":")).encode(), hashlib.sha256).hexdigest()
    if not isinstance(value.get("attestation"), str) or not hmac.compare_digest(value["attestation"], wanted):
        raise ContractValidationError("audio artifact attestation is invalid")
    if required_right and required_right not in provenance.get("rights_declared", []):
        raise AudioRightsError(f"artifact lacks declared {required_right} rights")
    path = Path(str(value.get("path", "")))
    if not path.is_absolute():
        raise ContractValidationError("audio artifact path binding is invalid")
    try:
        _verify_private_artifact(path, value.get("sha256"), value.get("size_bytes"))
    except OSError as exc:
        raise ContractValidationError("audio artifact cannot be safely opened") from exc
    if provenance.get("kind") == "user_supplied":
        root = Path(str(provenance.get("approved_root", "")))
        if not root.is_absolute() or not path.resolve().is_relative_to(root.resolve()):
            raise AudioRightsError("user audio is outside its approved root")
    return json.loads(json.dumps(dict(value)))


class MacOSSayProvider:
    """Synthesize new narration with an enrolled /usr/bin/say-compatible tool."""

    def __init__(self, adapter: Any, private_root: Path, *, voices: Iterable[str], key_store: Any | None = None) -> None:
        self._adapter = adapter
        self._root = Path(private_root)
        self._voices = frozenset(voices)
        self._key_store = key_store or FileAudioReceiptKeyStore()
        if (not self._root.is_absolute() or self._root.is_symlink() or not self._root.is_dir() or
                self._root.stat().st_uid != os.getuid() or stat.S_IMODE(self._root.stat().st_mode) != 0o700):
            raise NarrationProviderError("narration root must be an absolute private directory")
        if not self._voices or any(not isinstance(v, str) or not v.strip() for v in self._voices):
            raise NarrationProviderError("discovered voice allowlist is invalid")

    def synthesize(self, cues: Sequence[Mapping[str, Any]], *, voice: str, output_path: Path) -> dict[str, Any]:
        if voice not in self._voices:
            raise NarrationProviderError("voice is not in the discovered allowlist")
        output = Path(output_path)
        if not output.is_absolute() or output.is_symlink() or output.parent.resolve(strict=True) != self._root.resolve(strict=True):
            raise NarrationProviderError("narration output must be directly inside the private root")
        texts = []
        for cue in cues:
            text = cue.get("text")
            if not isinstance(text, str) or not text.strip() or "\x00" in text:
                raise NarrationProviderError("narration cue text is invalid")
            texts.append(" ".join(text.split()))
        descriptor, name = tempfile.mkstemp(prefix=".narration-", suffix=".txt", dir=self._root)
        script = Path(name)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                handle.write("\n".join(texts) + ("\n" if texts else ""))
                handle.flush(); os.fsync(handle.fileno())
            result = self._adapter.run("narration", ["-v", voice, "-f", str(script), "-o", str(output)], timeout_seconds=300)
            if result.exit_code != 0 or not output.is_file() or output.is_symlink():
                raise NarrationProviderError("local narration generation failed")
            os.chmod(output, 0o600)
            return _artifact_receipt(provider="macos-say", path=output, mime_type="audio/aiff", artifact_role="new_narration",
                kind="new_narration", rights_declared=["voice"], approved_root=None,
                source="rewritten_script", voice=voice, model="macos-say", key_store=self._key_store)
        finally:
            script.unlink(missing_ok=True)


class ExistingAudioProvider:
    """Accept an immutable, rights-declared user track from approved roots."""

    def __init__(self, approved_roots: Iterable[Path], *, key_store: Any | None = None) -> None:
        roots = []
        for root in approved_roots:
            candidate = Path(root)
            if not candidate.is_absolute() or candidate.is_symlink() or not candidate.is_dir():
                raise AudioRightsError("approved audio roots are invalid")
            roots.append(candidate.resolve(strict=True))
        if not roots:
            raise AudioRightsError("at least one approved audio root is required")
        self._roots = tuple(roots)
        self._key_store = key_store or FileAudioReceiptKeyStore()

    def accept(self, path: Path, *, expected_sha256: str, rights: Mapping[str, bool]) -> dict[str, Any]:
        source = Path(path)
        if not source.is_absolute() or source.is_symlink() or not source.is_file():
            raise AudioRightsError("audio must be an absolute regular non-symlink file")
        resolved = source.resolve(strict=True)
        if not any(resolved.is_relative_to(root) for root in self._roots):
            raise AudioRightsError("audio is outside approved roots")
        declared = sorted(key for key, value in rights.items() if key in AUDIO_CLASSES and value is True)
        artifact_roles = {("voice",): "existing_voice", ("dialogue",): "existing_dialogue",
                          ("dialogue", "voice"): "existing_voice_dialogue", ("music",): "music",
                          ("effects",): "effect", ("ambience",): "ambience"}
        artifact_role = artifact_roles.get(tuple(declared))
        if set(rights).difference(AUDIO_CLASSES) or artifact_role is None or _DIGEST.fullmatch(expected_sha256) is None or _digest(resolved) != expected_sha256:
            raise AudioRightsError("audio digest, provenance, or rights declaration is invalid")
        return _artifact_receipt(provider="existing-audio", path=resolved, mime_type="audio/wav", artifact_role=artifact_role,
            kind="user_supplied", rights_declared=declared,
            approved_root=str(next(root for root in self._roots if resolved.is_relative_to(root))),
            source="user_supplied", voice=None, model=None, key_store=self._key_store)


class AudioPlanService:
    """Build a closed, fingerprinted handoff for Task 12 composition."""

    def __init__(self, *, key_store: Any | None = None, project_store: Any | None = None,
                 now: Callable[[], str] | None = None) -> None:
        self._key_store = key_store or FileAudioReceiptKeyStore()
        self._project_store = project_store
        self._now = now

    def create_plan(self, *, project_id: str, design_fingerprint: str, batch_fingerprint: str,
                    creative_mode: str, source_rights: Mapping[str, Any] | None,
                    transcript: Mapping[str, Any] | None, rewritten_script: Sequence[Mapping[str, Any]],
                    narration: Mapping[str, Any] | None, music: Mapping[str, Any] | None,
                    effects: Sequence[Mapping[str, Any]], subtitles: Sequence[Mapping[str, Any]],
                    target_duration_seconds: float, audio_policy: str = "full_redesign",
                    preserve: Sequence[str] = (), ambience: Sequence[Mapping[str, Any]] = ()) -> dict[str, Any]:
        if audio_policy not in AUDIO_POLICIES or creative_mode not in {"authorized_replication", "original_redesign"}:
            raise ValueError("creative mode or audio policy is unsupported")
        if isinstance(target_duration_seconds, bool) or not isinstance(target_duration_seconds, (int, float)) or target_duration_seconds <= 0:
            raise ValueError("target duration must be positive")
        requested = set(preserve)
        if not requested <= AUDIO_CLASSES or len(requested) != len(preserve):
            raise AudioRightsError("preserved audio classes must be closed and unique")
        transcript_value = self._verify_transcript(transcript) if transcript is not None else None
        if creative_mode == "original_redesign" and (source_rights is not None or requested.intersection({"voice", "dialogue", "music"})):
            raise AudioRightsError("original redesign cannot reuse source voice, dialogue, or music")
        if audio_policy in {"preserve_authorized_audio", "subtitles_only"} and requested:
            allowed = set(source_rights.get("allowed_reuse", [])) if source_rights else set()
            if creative_mode != "authorized_replication" or not requested or requested != allowed:
                raise AudioRightsError("rights receipt does not cover every requested audio class")
            self._verify_current_rights(
                project_id=project_id,
                design_fingerprint=design_fingerprint,
                audio_policy=audio_policy,
                source_rights=source_rights,
                requested=requested,
            )
        elif audio_policy == "preserve_authorized_audio":
            raise AudioRightsError("preserve_authorized_audio requires at least one preserved class")
        elif requested or source_rights is not None:
            raise AudioRightsError("source audio reuse requires an authorized audio policy")
        if audio_policy == "full_redesign" and (not rewritten_script or narration is None):
            raise ValueError("full redesign requires a rewritten script and new narration")
        if audio_policy == "silent" and (narration is not None or music is not None or effects or ambience):
            raise ValueError("subtitle-only or silent plans cannot invent audio")
        if audio_policy == "subtitles_only" and not requested and (narration is not None or music is not None or effects or ambience):
            raise ValueError("subtitle-only audio must be an explicitly authorized preserved source")
        narration_value = None
        if narration is not None:
            role = str(narration.get("artifact_role", ""))
            narration_value = _require_artifact(narration, role=role, key_store=self._key_store)
            if audio_policy == "full_redesign" and not (narration_value["provider"] == "macos-say" or
                    (narration_value["provenance"]["source"] == "user_new_narration" and "voice" in narration_value["provenance"]["rights_declared"])):
                raise AudioRightsError("full redesign narration must be trusted new narration")
            if audio_policy == "subtitles_only" and narration_value["provider"] != "existing-audio":
                raise AudioRightsError("subtitle-only mode cannot synthesize new narration")
        def placed_artifacts(values: Sequence[Mapping[str, Any]], role: str, right: str) -> list[dict[str, Any]]:
            placed = []
            for item in values:
                raw = dict(item); at = raw.pop("at_seconds", None); duration = raw.pop("duration_seconds", None)
                if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
                       for value in (at, duration)) or at < 0 or duration <= 0 or at + duration > target_duration_seconds:
                    raise ValueError("effect placement must use bounded at_seconds and duration_seconds")
                placed.append({**_require_artifact(raw, role=role, key_store=self._key_store, required_right=right),
                               "at_seconds": float(at), "duration_seconds": float(duration)})
            return placed
        effects_value = placed_artifacts(effects, "effect", "effects")
        ambience_value = placed_artifacts(ambience, "ambience", "ambience")
        subtitles_value = [_require_artifact(item, role=str(item.get("artifact_role", "")), key_store=self._key_store) for item in subtitles]
        music_value = None
        if music is not None:
            raw = dict(music)
            intent = {"loop": raw.pop("loop", False), "trim_to_seconds": raw.pop("trim_to_seconds", None),
                      "use_full_track": raw.pop("use_full_track", None)}
            if intent["use_full_track"] is None:
                intent["use_full_track"] = intent["loop"] is False and intent["trim_to_seconds"] is None
            if not isinstance(intent["loop"], bool) or (
                    intent["trim_to_seconds"] is not None and (
                        isinstance(intent["trim_to_seconds"], bool)
                        or not isinstance(intent["trim_to_seconds"], (int, float))
                        or not math.isfinite(intent["trim_to_seconds"])
                        or intent["trim_to_seconds"] <= 0
                        or intent["trim_to_seconds"] > target_duration_seconds
                    )) or not isinstance(intent["use_full_track"], bool) or (
                        intent["trim_to_seconds"] is None and (intent["loop"] or not intent["use_full_track"])
                    ) or (intent["trim_to_seconds"] is not None and intent["use_full_track"]):
                raise ValueError("music loop and trim intent must be closed and bounded")
            music_value = {**_require_artifact(raw, role="music", key_store=self._key_store, required_right="music"), "intent": intent}
        if audio_policy in {"preserve_authorized_audio", "subtitles_only"} and requested:
            concrete = {}
            if narration_value is not None and narration_value["provider"] == "existing-audio":
                for name in ("voice", "dialogue"):
                    if name in narration_value["provenance"]["rights_declared"]:
                        concrete[name] = narration_value
            if music_value is not None:
                concrete["music"] = music_value
            if effects_value:
                concrete["effects"] = effects_value
            if ambience_value:
                concrete["ambience"] = ambience_value
            if set(concrete) != requested:
                raise AudioRightsError("preserved classes and concrete source artifacts must match exactly")
            bindings = source_rights.get("artifact_bindings", {}) if source_rights else {}
            actual_bindings = {}
            for name, value in concrete.items():
                values = value if isinstance(value, list) else [value]
                members = [{"path": item["path"], "sha256": item["sha256"]} for item in values]
                if len({(item["path"], item["sha256"]) for item in members}) != len(members):
                    raise AudioRightsError("duplicate preserved audio artifact")
                actual_bindings[name] = sorted(members, key=lambda item: (item["path"], item["sha256"]))
            normalized_bindings = {name: sorted(value if isinstance(value, list) else [value], key=lambda item: (item.get("path", ""), item.get("sha256", ""))) for name, value in bindings.items()}
            if set(bindings) != requested or normalized_bindings != actual_bindings:
                raise AudioRightsError("rights receipt artifact bindings do not match preserved sources")
        core = {
            "schema_version": "1.0", "version": "v001", "project_id": project_id,
            "design_fingerprint": design_fingerprint, "batch_fingerprint": batch_fingerprint,
            "creative_mode": creative_mode, "audio_policy": audio_policy,
            "target_duration_seconds": float(target_duration_seconds), "source_rights": dict(source_rights) if source_rights else None,
            "preserve": sorted(requested), "transcript": transcript_value,
            "rewritten_script": list(rewritten_script), "narration": narration_value,
            "music": music_value, "effects": effects_value, "ambience": ambience_value, "subtitles": subtitles_value,
            "provenance": {"remote_services_used": False, "source_voice_cloned": False},
        }
        result = {**core, "plan_fingerprint": canonical_fingerprint({key: value for key, value in core.items() if key != "version"})}
        validate_contract(result, "audio_plan.schema.json")
        return result

    def _verify_current_rights(self, *, project_id: str, design_fingerprint: str, audio_policy: str,
                               source_rights: Mapping[str, Any], requested: set[str]) -> None:
        """Reload and validate the exact current design and rights receipt before reuse."""
        if self._project_store is None:
            raise AudioRightsError("preserved source audio requires the persisted project rights store")
        try:
            project = self._project_store.get(project_id)
            design = self._project_store.find_version_by_field(
                project_id, "redesign", field="design_fingerprint", value=design_fingerprint,
                schema_name="video_redesign.schema.json",
            )
            receipt_id = source_rights["receipt_id"]
            receipt = self._project_store.find_version_by_field(
                project_id, "rights_receipt", field="receipt_id", value=receipt_id,
                schema_name="video_rights_receipt.schema.json",
            )
            if (project["creative_mode"] != "authorized_replication"
                    or project["audio_policy"] != audio_policy
                    or design["creative_mode"] != "authorized_replication"
                    or design["rights_receipt_id"] != receipt_id
                    or canonical_fingerprint(receipt) != source_rights["receipt_fingerprint"]
                    or "audio" not in receipt["allowed_media"]):
                raise AudioRightsError("audio rights identity or persisted binding is stale")
            payload = design["payload"]
            from scripts.video_rights_service import VideoRightsService

            rights = (VideoRightsService(self._project_store, native_confirmer=None, now=self._now)
                      if self._now is not None
                      else VideoRightsService(self._project_store, native_confirmer=None))
            rights.assert_scope(
                receipt,
                required=requested,
                binding={
                    "project_id": project_id,
                    "source_sha256": design["source_sha256"],
                    "creative_mode": "authorized_replication",
                    "design_fingerprint": design_fingerprint,
                    "required_media": payload["required_media"],
                    "purpose": payload["purpose"],
                    "audience": payload["audience"],
                    "territory": payload["territory"],
                },
            )
        except AudioRightsError:
            raise
        except Exception as exc:
            raise AudioRightsError("current audio rights scope, expiry, or binding is invalid") from exc

    def _verify_transcript(self, transcript: Mapping[str, Any]) -> dict[str, Any]:
        if self._project_store is None:
            raise ContractValidationError("audio plans accept only persisted transcript receipts")
        value = json.loads(json.dumps(dict(transcript), ensure_ascii=False, allow_nan=False))
        validate_contract(value, "transcript_receipt.schema.json")
        persisted = self._project_store.read_version(
            value["project_id"], "transcript", value["version"], "transcript_receipt.schema.json")
        core = {key: item for key, item in value.items() if key not in {"version", "transcript_fingerprint"}}
        if persisted != value or value["transcript_fingerprint"] != canonical_fingerprint(core):
            raise ContractValidationError("transcript receipt is not the exact persisted evidence")
        return value

    def commit_plan(self, plan: Mapping[str, Any], *, indeterminate_commit: Any | None = None) -> dict[str, Any]:
        """Persist one immutable audio-plan version or reconcile an exact prior commit."""
        if self._project_store is None:
            raise RuntimeError("audio plan persistence requires a VideoProjectStore")
        document = json.loads(json.dumps(dict(plan), ensure_ascii=False, allow_nan=False))
        validate_contract(document, "audio_plan.schema.json")
        expected = canonical_fingerprint({key: value for key, value in document.items() if key not in {"version", "plan_fingerprint"}})
        if document["plan_fingerprint"] != expected:
            raise ContractValidationError("audio plan fingerprint is invalid")
        document = self.verify_for_use(document)
        if indeterminate_commit is not None:
            expected_path = self._project_store.project_root(document["project_id"]) / "audio_plan" / f"{indeterminate_commit.version}.json"
            if (indeterminate_commit.project_id != document["project_id"]
                    or indeterminate_commit.family != "audio_plan"
                    or indeterminate_commit.path != expected_path):
                raise ContractValidationError("indeterminate audio-plan identity is invalid")
            recovered = self._project_store.reconcile_version(
                document["project_id"], "audio_plan", indeterminate_commit.version,
                indeterminate_commit.payload_fingerprint, "audio_plan.schema.json",
            )
            if ({key: value for key, value in recovered.items() if key != "version"}
                    != {key: value for key, value in document.items() if key != "version"}):
                raise ContractValidationError("indeterminate audio-plan retry does not match committed content")
            return recovered
        payload = {key: value for key, value in document.items() if key != "version"}
        return self._project_store.write_version(
            document["project_id"], "audio_plan", payload,
            schema_name="audio_plan.schema.json",
        )

    def verify_for_use(self, plan: Mapping[str, Any]) -> dict[str, Any]:
        """Reload current policy/rights and reverify every signed artifact before a side effect."""
        document = json.loads(json.dumps(dict(plan), ensure_ascii=False, allow_nan=False))
        validate_contract(document, "audio_plan.schema.json")
        expected = canonical_fingerprint({key: value for key, value in document.items() if key not in {"version", "plan_fingerprint"}})
        if document["plan_fingerprint"] != expected:
            raise ContractValidationError("audio plan fingerprint is invalid")
        if self._project_store is None:
            raise ContractValidationError("audio plan use requires the current persisted project")
        project = self._project_store.get(document["project_id"])
        if project["creative_mode"] != document["creative_mode"] or project["audio_policy"] != document["audio_policy"]:
            raise ContractValidationError("audio plan no longer matches the current project")
        if document["preserve"]:
            self._verify_current_rights(project_id=document["project_id"], design_fingerprint=document["design_fingerprint"],
                audio_policy=document["audio_policy"], source_rights=document["source_rights"], requested=set(document["preserve"]))
        if document["transcript"] is not None:
            self._verify_transcript(document["transcript"])
        artifacts = (([document["narration"]] if document["narration"] else [])
                     + list(document["effects"]) + list(document["ambience"]) + list(document["subtitles"]))
        for artifact in artifacts:
            receipt = {key: value for key, value in artifact.items() if key not in {"at_seconds", "duration_seconds"}}
            _require_artifact(receipt, role=receipt["artifact_role"], key_store=self._key_store,
                              required_right={"effect": "effects", "ambience": "ambience"}.get(receipt["artifact_role"]))
        if document["music"]:
            music = {key: value for key, value in document["music"].items() if key != "intent"}
            _require_artifact(music, role="music", key_store=self._key_store, required_right="music")
        return document


__all__ = ["AUDIO_POLICIES", "AudioPlanService", "AudioReceiptKeyUnavailableError", "AudioRightsError", "ExistingAudioProvider", "FileAudioReceiptKeyStore", "MacOSSayProvider", "NarrationProviderError"]
