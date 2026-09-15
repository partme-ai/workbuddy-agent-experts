"""Video request workflow for the Dreamina Design plugin (Task 4).

Mirrors :mod:`scripts.image_service` for the four video modes:

* ``text2video``
* ``image2video``
* ``frames2video``
* ``multimodal2video``

Responsibilities:

* Build a normalized video ``GenerationRequest`` from a current capability
  snapshot — never invent flags. Resolution, ratio, duration, and audio
  reference constraints are read from the snapshot only.
* Enforce the 4–30 second window required by the plugin plan; durations
  outside the snapshot's ``duration_min_seconds`` / ``duration_max_seconds``
  are rejected.
* For Seedance 2.5 (or any model that advertises ``web_prerequisite_required``)
  the very first submission is refused with
  :class:`VideoWebPrerequisiteRequired` until the user has acknowledged the
  web-console prerequisite. The flag is never silently bypassed.
* Bind submissions to an ``ApprovalReceipt`` whose ``request_fingerprint``
  matches the canonical SHA-256 of the request, including the references.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from scripts.dreamina_adapter import DreaminaResult


class VideoServiceError(Exception):
    """Base class for video workflow errors."""


class UnsupportedCapabilityError(VideoServiceError):
    """A requested model / resolution / ratio / mode is not in the snapshot."""


class DurationOutOfRangeError(VideoServiceError):
    """Duration is outside the [min, max] window advertised by the snapshot."""


class InvalidReferenceError(VideoServiceError):
    """Reference list violates mode-specific scope, role, or size rules."""


class MissingApprovalError(VideoServiceError):
    """A submission was attempted without an approval receipt."""


class ApprovalMismatchError(VideoServiceError):
    """The approval receipt's request_fingerprint does not match the request."""


class VideoWebPrerequisiteRequired(VideoServiceError):
    """The first-video web-console prerequisite has not been acknowledged."""


class BatchAllowanceCommitError(VideoServiceError):
    """Provider accepted the request but allowance terminalization is uncertain."""

    def __init__(self, *, submit_id: str, reservation_id: str,
                 request_fingerprint: str, shot_id: str, attempt: int) -> None:
        self.submit_id = submit_id
        self.reservation_id = reservation_id
        self.request_fingerprint = request_fingerprint
        self.shot_id = shot_id
        self.attempt = attempt
        super().__init__("allowance commit is indeterminate; query the known submit_id")


class PostInvokePersistenceError(VideoServiceError):
    """The provider boundary was crossed and local durable completion failed."""

    def __init__(self, *, submit_id: str | None, result_bytes: bytes,
                 allowance_id: str | None, reservation_id: str | None,
                 request_fingerprint: str, cause: Exception) -> None:
        self.submit_id = submit_id
        self.result_bytes = bytes(result_bytes)
        self.evidence_sha256 = hashlib.sha256(self.result_bytes).hexdigest()
        self.evidence_length = len(self.result_bytes)
        self.exception_type = _safe_exception_type(cause)
        self.classification = "known_submit_id" if submit_id else "unknown_remote_outcome"
        self.allowance_id = allowance_id
        self.reservation_id = reservation_id
        self.request_fingerprint = request_fingerprint
        self.remote_invoked = True
        self.cause = cause
        super().__init__("provider invocation crossed; reconcile known identity or require manual review")


REFERENCE_LIMIT = 8
VIDEO_REFERENCE_ROLES = {"style", "subject", "frame", "audio", "reference"}
MODE_REQUIRED_REFERENCES = {
    "image2video": {"subject", "style"},
    "frames2video": {"frame"},
    "multiframe2video": {"frame"},
}


@dataclass(frozen=True)
class _VideoModelSpec:
    name: str
    modes: frozenset[str]
    resolutions: frozenset[str]
    ratios: frozenset[str]
    duration_min_seconds: int
    duration_max_seconds: int
    web_prerequisite_required: bool
    audio_reference_max_seconds: int | None
    ratio_forbidden_modes: frozenset[str]
    max_references: int

    @classmethod
    def from_snapshot(cls, entry: Mapping[str, Any]) -> "_VideoModelSpec":
        audio_max = entry.get("audio_reference_max_seconds")
        return cls(
            name=str(entry["name"]),
            modes=frozenset(entry.get("modes", [])),
            resolutions=frozenset(entry.get("resolutions", [])),
            ratios=frozenset(entry.get("ratios", [])),
            duration_min_seconds=int(entry.get("duration_min_seconds", 4)),
            duration_max_seconds=int(entry.get("duration_max_seconds", 30)),
            web_prerequisite_required=bool(entry.get("web_prerequisite_required", False)),
            audio_reference_max_seconds=int(audio_max) if audio_max is not None else None,
            ratio_forbidden_modes=frozenset(entry.get("ratio_forbidden_modes", [])),
            max_references=int(entry.get("max_references", REFERENCE_LIMIT)),
        )


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(dict(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_video_request_fingerprint(payload: Mapping[str, Any]) -> str:
    """SHA-256 hex digest over canonical JSON serialization."""
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _safe_exception_type(exc: Exception) -> str:
    name = type(exc).__name__
    if (len(name) > 64 or re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name) is None
            or re.search(r"token|secret|password|cookie|authorization", name, re.I)):
        return "ADAPTER_ERROR"
    return name


class VideoService:
    """Build and submit Dreamina video requests against a capability snapshot."""

    def __init__(self, snapshot: Mapping[str, Any], ledger_dir: Path | None, reference_policy: Any | None = None) -> None:
        if "modes" not in snapshot:
            raise UnsupportedCapabilityError("snapshot missing modes")
        self._snapshot = snapshot
        self._modes = frozenset(snapshot.get("modes", []))
        self._ratios = frozenset(snapshot.get("ratios", []))
        self._video_resolutions = frozenset(snapshot.get("resolutions", {}).get("video", []))
        self._mode_limits = snapshot.get("mode_limits", {})
        self._models = {
            entry["name"]: _VideoModelSpec.from_snapshot(entry)
            for entry in snapshot.get("models", [])
            if isinstance(entry, Mapping) and "name" in entry
        }
        self._ledger_dir = Path(ledger_dir) if ledger_dir is not None else None
        if self._ledger_dir is not None:
            self._ledger_dir.mkdir(parents=True, exist_ok=True)
        self._reference_policy = reference_policy
        from scripts.operation_ledger import OperationLedger
        self._operation_ledger = OperationLedger(root=self._ledger_dir) if self._ledger_dir is not None else None
        self._web_prerequisite_acknowledged = False

    # ------------------------------------------------------------------
    # Web prerequisite acknowledgement
    # ------------------------------------------------------------------
    def record_web_prerequisite_acknowledgement(self) -> None:
        """Mark the web-console first-video prerequisite as acknowledged.

        The plugin plan forbids silent bypass. Callers must explicitly invoke
        this method after the user has performed the prerequisite in the
        Dreamina web console.
        """
        self._web_prerequisite_acknowledged = True
        if self._ledger_dir is None:
            raise VideoServiceError("ledger_dir is required to record acknowledgement")
        flag_path = self._ledger_dir / "web_prerequisite.ack"
        flag_path.write_text("acknowledged\n", encoding="utf-8")

    def is_web_prerequisite_acknowledged(self) -> bool:
        return self._web_prerequisite_acknowledged

    # ------------------------------------------------------------------
    # Request construction
    # ------------------------------------------------------------------
    def build_request(
        self,
        *,
        mode: str,
        prompt: str,
        model: str | None,
        video_resolution: str | None = None,
        ratio: str | None = None,
        duration_seconds: int | None = None,
        references: list[Mapping[str, Any]] | None = None,
        transitions: list[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if mode not in self._modes:
            raise UnsupportedCapabilityError(f"mode not in snapshot: {mode}")
        spec = self._models.get(model)
        if mode == "multiframe2video" and model is None:
            spec = self._multiframe_spec()
        if spec is None:
            raise UnsupportedCapabilityError(f"unknown model: {model}")
        if mode not in spec.modes:
            raise UnsupportedCapabilityError(f"model {model} does not support mode {mode}")
        if not video_resolution:
            raise UnsupportedCapabilityError("video_resolution is required for video requests")
        advertised_resolutions = spec.resolutions or self._video_resolutions
        if video_resolution not in advertised_resolutions:
            raise UnsupportedCapabilityError(f"video_resolution not advertised: {video_resolution}")
        advertised_ratios = spec.ratios or self._ratios
        if ratio is not None and ratio not in advertised_ratios:
            raise UnsupportedCapabilityError(f"ratio not advertised: {ratio}")
        if ratio is not None and mode in spec.ratio_forbidden_modes:
            raise UnsupportedCapabilityError(
                f"ratio is not accepted for model {model} in mode {mode}"
            )
        effective_duration = duration_seconds if duration_seconds is not None else spec.duration_min_seconds
        if not (spec.duration_min_seconds <= effective_duration <= spec.duration_max_seconds):
            raise DurationOutOfRangeError(
                f"duration_seconds must be between {spec.duration_min_seconds} "
                f"and {spec.duration_max_seconds}, got {effective_duration}"
            )
        normalized_refs = self._validate_references(
            mode=mode,
            references=references or [],
            spec=spec,
            reference_policy=self._reference_policy,
        )
        normalized_transitions = list(transitions or [])
        if mode == "multiframe2video":
            if ratio is not None or model is not None:
                raise UnsupportedCapabilityError("multiframe2video does not accept model or ratio")
            if not spec.max_references >= len(normalized_refs) >= int(self._mode_limits[mode]["min_references"]) or any(ref["role"] != "frame" for ref in normalized_refs):
                raise InvalidReferenceError(
                    f"multiframe2video requires {self._mode_limits[mode]['min_references']}..{spec.max_references} ordered frame references"
                )
            if normalized_transitions and len(normalized_transitions) != len(normalized_refs) - 1:
                raise VideoServiceError("multiframe2video requires exactly N-1 transitions")
            limits = self._mode_limits[mode]
            for transition in normalized_transitions:
                raw_seconds = transition.get("duration_seconds")
                if isinstance(raw_seconds, bool) or not isinstance(raw_seconds, int):
                    raise VideoServiceError("transition duration_seconds must be an integer")
                seconds = raw_seconds
                if not str(transition.get("prompt", "")).strip() or not int(limits["transition_duration_min_seconds"]) <= seconds <= int(limits["transition_duration_max_seconds"]):
                    raise VideoServiceError("transition violates advertised duration limits")

        request: dict[str, Any] = {
            "mode": mode,
            "prompt": prompt,
            "video_resolution": video_resolution,
            "duration_seconds": effective_duration,
        }
        if model is not None:
            request["model"] = model
        if ratio is not None:
            request["ratio"] = ratio
        if normalized_refs:
            request["references"] = normalized_refs
        if normalized_transitions:
            request["transitions"] = normalized_transitions
        return request

    def _multiframe_spec(self) -> _VideoModelSpec:
        limits = self._mode_limits.get("multiframe2video") if isinstance(self._mode_limits, Mapping) else None
        required = ("min_references", "max_references", "request_duration_min_seconds", "request_duration_max_seconds", "transition_duration_min_seconds", "transition_duration_max_seconds")
        if not isinstance(limits, Mapping) or any(key not in limits for key in required):
            raise UnsupportedCapabilityError("snapshot missing multiframe2video mode limits")
        return _VideoModelSpec(
            name="__snapshot_mode__", modes=frozenset({"multiframe2video"}),
            resolutions=self._video_resolutions, ratios=frozenset(),
            duration_min_seconds=int(limits["request_duration_min_seconds"]),
            duration_max_seconds=int(limits["request_duration_max_seconds"]),
            web_prerequisite_required=False, audio_reference_max_seconds=None,
            ratio_forbidden_modes=frozenset({"multiframe2video"}),
            max_references=int(limits["max_references"]),
        )

    @staticmethod
    def _validate_references(
        *,
        mode: str,
        references: list[Mapping[str, Any]],
        spec: _VideoModelSpec,
        reference_policy: Any | None,
    ) -> list[dict[str, Any]]:
        required_roles = MODE_REQUIRED_REFERENCES.get(mode, set())
        if required_roles and not references:
            raise InvalidReferenceError(f"mode {mode} requires references with roles {sorted(required_roles)}")
        if not references:
            return []
        if len(references) > spec.max_references:
            raise InvalidReferenceError(f"too many references (max {spec.max_references})")
        if references and reference_policy is None:
            raise InvalidReferenceError("a ReferencePolicy is required for local uploads")
        normalized: list[dict[str, Any]] = []
        for ref in references:
            if not isinstance(ref, Mapping):
                raise InvalidReferenceError("reference must be an object")
            role = str(ref.get("role", "")).strip().lower()
            if role not in VIDEO_REFERENCE_ROLES:
                raise InvalidReferenceError(f"unknown reference role: {role}")
            path = ref.get("path")
            if not path:
                raise InvalidReferenceError("reference.path is required")
            entry: dict[str, Any] = {"path": str(path), "role": role}
            mime = ref.get("mime_type")
            if mime is not None:
                entry["mime_type"] = str(mime)
            size = ref.get("size_bytes")
            if size is not None:
                entry["size_bytes"] = int(size)
            sha256 = ref.get("sha256")
            if sha256 is not None:
                entry["sha256"] = str(sha256)
            audio_seconds = ref.get("duration_seconds")
            if role == "audio" and audio_seconds is not None:
                entry["duration_seconds"] = int(audio_seconds)
                if (
                    spec.audio_reference_max_seconds is not None
                    and int(audio_seconds) > spec.audio_reference_max_seconds
                ):
                    raise InvalidReferenceError(
                        f"audio reference duration {audio_seconds}s exceeds snapshot cap "
                        f"{spec.audio_reference_max_seconds}s"
                    )
            try:
                normalized.append(reference_policy.validate(entry))
            except (ValueError, OSError) as exc:
                raise InvalidReferenceError(str(exc)) from exc
        if required_roles and not required_roles.intersection({r["role"] for r in normalized}):
            raise InvalidReferenceError(
                f"mode {mode} requires references with at least one of {sorted(required_roles)}"
            )
        if mode == "image2video" and (
            len(normalized) != 1 or normalized[0]["role"] not in {"subject", "style"}
        ):
            raise InvalidReferenceError(
                "image2video requires exactly one subject or style reference"
            )
        if mode == "frames2video" and (
            len(normalized) != 2 or any(r["role"] != "frame" for r in normalized)
        ):
            raise InvalidReferenceError("frames2video requires exactly two frame references")
        return normalized

    # ------------------------------------------------------------------
    # Submission
    # ------------------------------------------------------------------
    def submit(
        self,
        request: Mapping[str, Any],
        *,
        adapter: Any,
        approval_guard: Any,
        session_id: str | None,
        approval_id: str | None,
        web_prerequisite_cleared: bool,
    ) -> dict[str, Any]:
        if approval_guard is None or not session_id or not approval_id:
            raise MissingApprovalError("approval receipt is required before submission")
        spec = self._models.get(request.get("model"))
        if spec is None and request["mode"] == "multiframe2video":
            spec = self._multiframe_spec()
        if spec.web_prerequisite_required and not self._web_prerequisite_acknowledged:
            # The caller can pass web_prerequisite_cleared=True to indicate the
            # web console step has been observed in the same session, but we
            # still require an in-process acknowledgement record.
            if not web_prerequisite_cleared or not self._web_prerequisite_acknowledged:
                raise VideoWebPrerequisiteRequired(
                    "first Dreamina video requires the user to acknowledge the web-console "
                    "prerequisite via record_web_prerequisite_acknowledgement(); "
                    "no silent bypass is permitted"
                )
        from scripts.approval_guard import ApprovalGuard, ApprovalGuardError
        if not isinstance(approval_guard, ApprovalGuard):
            raise MissingApprovalError("approval_guard must be an ApprovalGuard instance")
        fingerprint = build_video_request_fingerprint(dict(request))
        self._operation_ledger.begin_submission(
            session_id=session_id,
            mode=str(request["mode"]),
            request_fingerprint=fingerprint,
        )
        try:
            approval_guard.consume_approval(
                session_id, request=request, approval_id=approval_id,
                fingerprint_builder=build_video_request_fingerprint,
            )
        except ApprovalGuardError as exc:
            self._operation_ledger.abort_submission_intent(
                request_fingerprint=fingerprint, reason="APPROVAL_REJECTED"
            )
            raise ApprovalMismatchError(str(exc)) from exc
        return self._invoke_once(
            request, adapter=adapter, session_id=session_id,
            request_fingerprint=fingerprint, begin_intent=False,
        )

    def submit_with_batch_allowance(
        self,
        request: Mapping[str, Any],
        *,
        adapter: Any,
        allowance: Any,
        allowance_id: str,
        shot_id: str,
        attempt: int,
    ) -> dict[str, Any]:
        """Reserve an exact approved batch request and cross the provider boundary once."""
        if self._operation_ledger is None:
            raise VideoServiceError("ledger_dir is required for batch submission")
        fingerprint = build_video_request_fingerprint(dict(request))
        reservation = allowance.reserve(
            allowance_id, shot_id=shot_id, attempt=attempt,
            request_fingerprint=fingerprint,
        )
        try:
            result = self._invoke_once(
                request, adapter=adapter, session_id=allowance_id,
                request_fingerprint=fingerprint, begin_intent=True,
                allowance_id=allowance_id,
                reservation_id=reservation["reservation_id"],
            )
        except PostInvokePersistenceError as exc:
            try:
                allowance.mark_ambiguous(
                    reservation["reservation_id"], type(exc).__name__.upper(),
                    submit_id=exc.submit_id,
                )
            except Exception:
                # Never replace the typed post-invoke evidence with a local
                # allowance persistence error; the executor must retain ID.
                pass
            raise
        try:
            committed = allowance.commit(reservation["reservation_id"], result["submit_id"])
        except Exception as exc:
            try:
                allowance.mark_ambiguous(
                    reservation["reservation_id"], "ALLOWANCE_COMMIT_INDETERMINATE",
                    submit_id=result["submit_id"],
                )
            except Exception:
                # A committed or ambiguous terminal record is already safe; the
                # executor will reconcile it by the known provider identifier.
                pass
            raise BatchAllowanceCommitError(
                submit_id=result["submit_id"], reservation_id=reservation["reservation_id"],
                request_fingerprint=fingerprint, shot_id=shot_id, attempt=attempt,
            ) from exc
        return {**result, "reservation": committed}

    def _invoke_once(
        self,
        request: Mapping[str, Any],
        *,
        adapter: Any,
        session_id: str,
        request_fingerprint: str,
        begin_intent: bool,
        allowance_id: str | None = None,
        reservation_id: str | None = None,
    ) -> dict[str, Any]:
        """Persist an invocation intent, invoke once, and durably bind its submit id."""
        # Direct submission already persisted its intent before approval. Batch
        # submission reaches this seam immediately after its durable reservation.
        if begin_intent:
            self._operation_ledger.begin_submission(
                session_id=session_id, mode=str(request["mode"]),
                request_fingerprint=request_fingerprint,
                allowance_id=allowance_id, reservation_id=reservation_id,
            )
        argv = self._request_to_argv(request)
        try:
            result: DreaminaResult = adapter.run(argv)
        except Exception as exc:
            invocation_started = getattr(exc, "invocation_started", True)
            outcome_ambiguous = getattr(exc, "outcome_ambiguous", True)
            if not invocation_started or not outcome_ambiguous:
                try:
                    self._operation_ledger.abort_submission_intent(
                        request_fingerprint=request_fingerprint,
                        reason="PREINVOKE_OR_DEFINITE_LOCAL_FAILURE")
                except Exception:
                    pass
                raise
            known_submit_id = getattr(exc, "submit_id", None)
            try:
                self._operation_ledger.complete_submission_intent(
                    request_fingerprint=request_fingerprint, submit_id=known_submit_id,
                    error_code=_safe_exception_type(exc), allowance_id=allowance_id,
                    reservation_id=reservation_id)
            except Exception:
                pass
            if known_submit_id:
                try:
                    self._operation_ledger.record(
                        session_id=session_id, submit_id=known_submit_id,
                        mode=str(request["mode"]), request_fingerprint=request_fingerprint,
                        allowance_id=allowance_id, reservation_id=reservation_id,
                    )
                except Exception:
                    pass
            if not begin_intent:
                raise
            evidence_bytes = getattr(exc, "result_bytes", None)
            if not isinstance(evidence_bytes, bytes):
                evidence_bytes = str(exc).encode("utf-8", "replace")
            raise PostInvokePersistenceError(
                submit_id=known_submit_id, result_bytes=evidence_bytes,
                allowance_id=allowance_id, reservation_id=reservation_id,
                request_fingerprint=request_fingerprint, cause=exc) from exc
        if not result.submit_id:
            missing = VideoServiceError("Dreamina returned no recoverable submit_id")
            try:
                self._operation_ledger.complete_submission_intent(
                    request_fingerprint=request_fingerprint, submit_id=None,
                    error_code="MISSING_SUBMIT_ID", allowance_id=allowance_id,
                    reservation_id=reservation_id)
            except Exception:
                pass
            raise PostInvokePersistenceError(
                submit_id=None,
                result_bytes=json.dumps(result.payload or {}, sort_keys=True, default=str).encode("utf-8"),
                allowance_id=allowance_id, reservation_id=reservation_id,
                request_fingerprint=request_fingerprint, cause=missing)
        result_bytes = json.dumps(result.payload or {}, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        try:
            self._operation_ledger.complete_submission_intent(
                request_fingerprint=request_fingerprint, submit_id=result.submit_id,
                allowance_id=allowance_id, reservation_id=reservation_id)
            self._operation_ledger.record(
                session_id=session_id, submit_id=result.submit_id, mode=str(request["mode"]),
                request_fingerprint=request_fingerprint, allowance_id=allowance_id,
                reservation_id=reservation_id)
        except Exception as exc:
            raise PostInvokePersistenceError(
                submit_id=result.submit_id, result_bytes=result_bytes,
                allowance_id=allowance_id, reservation_id=reservation_id,
                request_fingerprint=request_fingerprint, cause=exc) from exc
        payload = result.payload or {}
        items = payload.get("items") if isinstance(payload, Mapping) else None
        if items is None and isinstance(payload, Mapping):
            items = [{"submit_id": payload.get("submit_id"), "index": 0}]
        return {
            "submit_id": result.submit_id,
            "items": list(items or []),
            "stderr": result.stderr,
        }

    @staticmethod
    def _request_to_argv(request: Mapping[str, Any]) -> list[str]:
        if request["mode"] == "multiframe2video":
            argv = ["multiframe2video", "--prompt", str(request["prompt"]), "--video_resolution", str(request["video_resolution"]), "--duration", str(request["duration_seconds"]), "--images", ",".join(str(ref["path"]) for ref in request.get("references", []))]
            for transition in request.get("transitions", []):
                argv.extend(["--transition-prompt", str(transition["prompt"]), "--transition-duration", str(transition["duration_seconds"])])
            return argv
        argv: list[str] = [
            str(request["mode"]),
            "--model_version", str(request["model"]),
            "--prompt", str(request["prompt"]),
            "--video_resolution", str(request["video_resolution"]),
            "--duration", str(request["duration_seconds"]),
        ]
        if "ratio" in request:
            argv.extend(["--ratio", str(request["ratio"])])
        references = list(request.get("references", []) or [])
        if request["mode"] == "image2video" and references:
            argv.extend(["--image", str(references[0]["path"])])
        elif request["mode"] == "frames2video":
            argv.extend(["--first", str(references[0]["path"])])
            argv.extend(["--last", str(references[1]["path"])])
        elif request["mode"] == "multimodal2video":
            flag_by_role = {"audio": "--audio", "frame": "--image", "style": "--image", "subject": "--image", "reference": "--video"}
            for ref in references:
                argv.extend([flag_by_role[ref["role"]], str(ref["path"])])
        return argv


__all__ = [
    "ApprovalMismatchError",
    "BatchAllowanceCommitError",
    "PostInvokePersistenceError",
    "DurationOutOfRangeError",
    "InvalidReferenceError",
    "MissingApprovalError",
    "UnsupportedCapabilityError",
    "VideoService",
    "VideoWebPrerequisiteRequired",
    "build_video_request_fingerprint",
]
