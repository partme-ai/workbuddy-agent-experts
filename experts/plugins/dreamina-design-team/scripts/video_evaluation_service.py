"""Canonical, fail-closed evaluation of generated video shots."""
from __future__ import annotations

import copy
import hashlib
import math
import os
import re
import stat
import tempfile
from contextlib import AbstractContextManager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.json_contracts import canonical_fingerprint, parse_rfc3339, validate_contract


class EvaluationContractError(ValueError):
    """An evaluation input violates its closed two-source contract."""


MEASURED_GATE_ORDER = ("artifact_integrity", "dimensions", "codec", "duration", "aspect_ratio",
                       "frame_readability", "start_anchor", "end_anchor")
SEMANTIC_GATE_ORDER = ("intent", "composition", "identity_continuity", "camera_behavior",
                       "rhythm_function", "temporal_defects", "source_copying", "subtitle_safe_area")
MEASURED_GATES = frozenset(MEASURED_GATE_ORDER)
SEMANTIC_GATES = frozenset(SEMANTIC_GATE_ORDER)
BINDING_FIELDS = frozenset({"project_id", "batch_version", "shot_id", "attempt", "submit_id", "artifact_sha256",
                            "design_version", "design_fingerprint", "quote_fingerprint", "allowance_id"})
REPAIR_BY_GATE = {"identity_continuity": "identity_consistency", "camera_behavior": "camera_match",
                  "composition": "camera_match", "rhythm_function": "camera_match",
                  "dimensions": "camera_match", "aspect_ratio": "camera_match",
                  "duration": "temporal_stability", "temporal_defects": "temporal_stability",
                  "source_copying": "remove_text", "subtitle_safe_area": "remove_text"}
MANUAL_REVIEW_REASONS = frozenset({
    "allowance_binding_conflict", "allowance_inactive", "anchor_evidence_unavailable",
    "artifact_binding_conflict", "artifact_evidence_unavailable", "design_binding_conflict",
    "measured_evidence_unavailable", "mixed_repair_directives", "quote_binding_conflict",
    "repair_directive_unavailable", "retry_not_prequoted", "retry_unavailable",
    "semantic_binding_conflict", "semantic_evaluator_invalid", "semantic_evidence_invalid",
    "semantic_evidence_unavailable",
})
_DIGEST = re.compile(r"[a-f0-9]{64}")
_SUBMIT_ID = re.compile(r"[A-Za-z0-9._:-]{1,160}")
_MAX_ARTIFACT_BYTES = 2 * 1024 * 1024 * 1024
_MAX_EVALUATOR_AGE = timedelta(days=1)
_MAX_FUTURE_SKEW = timedelta(minutes=5)


def _binding(source: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(source, Mapping) or set(source) != BINDING_FIELDS:
        raise EvaluationContractError("evaluation binding must be complete and closed")
    result = copy.deepcopy(dict(source))
    if isinstance(result["attempt"], bool) or not isinstance(result["attempt"], int) or not 1 <= result["attempt"] <= 3:
        raise EvaluationContractError("evaluation attempt is invalid")
    for name in ("artifact_sha256", "design_fingerprint", "quote_fingerprint"):
        if not isinstance(result[name], str) or _DIGEST.fullmatch(result[name]) is None:
            raise EvaluationContractError(f"evaluation {name} is invalid")
    if not isinstance(result["submit_id"], str) or _SUBMIT_ID.fullmatch(result["submit_id"]) is None:
        raise EvaluationContractError("evaluation submit_id is invalid")
    return result


def _validate_gates(payload: Mapping[str, Any], order: tuple[str, ...]) -> dict[str, dict[str, str]]:
    if not isinstance(payload, Mapping) or set(payload) != set(order):
        raise EvaluationContractError("every domain gate is required exactly once")
    result: dict[str, dict[str, str]] = {}
    for name in order:
        gate = payload[name]
        if not isinstance(gate, Mapping) or set(gate) != {"status", "evidence"} \
                or gate.get("status") not in {"passed", "failed", "skipped"} \
                or not isinstance(gate.get("evidence"), str) or not 1 <= len(gate["evidence"]) <= 256:
            raise EvaluationContractError(f"evaluation gate {name} is invalid")
        result[name] = copy.deepcopy(dict(gate))
    return result


def _file_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (metadata.st_dev, metadata.st_ino, metadata.st_uid, stat.S_IMODE(metadata.st_mode),
            metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns)


class _ArtifactSnapshot(AbstractContextManager):
    """One private descriptor-derived copy whose source remains identity-stable."""

    def __init__(self, artifact: Mapping[str, Any], *, max_bytes: int) -> None:
        self.source_path = Path(str(artifact.get("path", "")))
        self.source_fd: int | None = None
        self.snapshot_fd: int | None = None
        self.temporary: tempfile.TemporaryDirectory[str] | None = None
        self.path: Path | None = None
        if not self.source_path.is_absolute():
            raise EvaluationContractError("artifact path must be absolute")
        try:
            self.source_fd = os.open(self.source_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            before = os.fstat(self.source_fd)
            declared_size = artifact.get("size_bytes")
            if not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid() \
                    or stat.S_IMODE(before.st_mode) & 0o077 \
                    or isinstance(declared_size, bool) or not isinstance(declared_size, int) \
                    or declared_size != before.st_size or not 0 < before.st_size <= max_bytes:
                raise EvaluationContractError("artifact must be a private bounded regular file with exact size")
            self.before = _file_identity(before)
            self.temporary = tempfile.TemporaryDirectory(prefix="dreamina-evaluation-")
            root = Path(self.temporary.name)
            root.chmod(0o700)
            self.path = root / "artifact.snapshot"
            self.snapshot_fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_EXCL
                                       | getattr(os, "O_NOFOLLOW", 0), 0o600)
            digest = hashlib.sha256()
            copied = 0
            while True:
                chunk = os.read(self.source_fd, min(1024 * 1024, max_bytes - copied + 1))
                if not chunk:
                    break
                copied += len(chunk)
                if copied > max_bytes or copied > declared_size:
                    raise EvaluationContractError("artifact exceeded its trusted size bound")
                digest.update(chunk)
                view = memoryview(chunk)
                while view:
                    written = os.write(self.snapshot_fd, view)
                    if written <= 0:
                        raise EvaluationContractError("artifact snapshot write made no progress")
                    view = view[written:]
            if copied != declared_size:
                raise EvaluationContractError("artifact changed while snapshotting")
            os.fsync(self.snapshot_fd)
            os.fchmod(self.snapshot_fd, 0o400)
            os.fsync(self.snapshot_fd)
            os.lseek(self.snapshot_fd, 0, os.SEEK_SET)
            self.snapshot_identity = _file_identity(os.fstat(self.snapshot_fd))
            self.digest, self.size_bytes = digest.hexdigest(), copied
            self.assert_stable()
        except Exception:
            self._cleanup(active_exception=True)
            raise

    def assert_stable(self) -> None:
        if self.source_fd is None or self.snapshot_fd is None or self.path is None:
            raise EvaluationContractError("artifact snapshot is unavailable")
        try:
            source_now = _file_identity(os.fstat(self.source_fd))
            source_path_now = _file_identity(os.stat(self.source_path, follow_symlinks=False))
            snapshot_now = _file_identity(os.fstat(self.snapshot_fd))
            snapshot_path_now = _file_identity(os.stat(self.path, follow_symlinks=False))
        except OSError as exc:
            raise EvaluationContractError("artifact identity changed during evaluation") from exc
        if source_now != self.before or source_path_now != self.before \
                or snapshot_now != self.snapshot_identity or snapshot_path_now != self.snapshot_identity:
            raise EvaluationContractError("artifact identity changed during evaluation")

    def _cleanup(self, *, active_exception: bool) -> None:
        first_error: BaseException | None = None
        for name in ("snapshot_fd", "source_fd"):
            descriptor = getattr(self, name)
            setattr(self, name, None)
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except BaseException as error:
                    if first_error is None:
                        first_error = error
        temporary = self.temporary
        self.temporary = None
        if temporary is not None:
            try:
                temporary.cleanup()
            except BaseException as error:
                if first_error is None:
                    first_error = error
        if first_error is not None and not active_exception:
            raise first_error

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._cleanup(active_exception=exc_type is not None or exc_value is not None)


class VideoEvaluationService:
    """Keep trusted measurements separate from model semantic judgments."""

    def __init__(self, *, media_adapter: Any, now: Any | None = None,
                 max_artifact_bytes: int = _MAX_ARTIFACT_BYTES) -> None:
        if media_adapter is None or not callable(getattr(media_adapter, "probe_json", None)) \
                or not callable(getattr(media_adapter, "verify_video_frames", None)):
            raise TypeError("a trusted media adapter is required")
        if isinstance(max_artifact_bytes, bool) or not isinstance(max_artifact_bytes, int) or max_artifact_bytes < 1:
            raise ValueError("max_artifact_bytes must be a positive integer")
        self._media_adapter = media_adapter
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._max_artifact_bytes = max_artifact_bytes

    def _trusted_now(self) -> tuple[datetime, str]:
        current = self._now()
        if isinstance(current, str):
            current = parse_rfc3339(current, label="created_at")
        if not isinstance(current, datetime) or current.tzinfo is None:
            raise EvaluationContractError("trusted evaluation clock must be timezone aware")
        current = current.astimezone(timezone.utc)
        return current, current.isoformat(timespec="seconds").replace("+00:00", "Z")

    def measure_clip(self, artifact: Mapping[str, Any], design_shot: Mapping[str, Any], *,
                     binding: Mapping[str, Any], expected_media: Mapping[str, Any] | None = None) -> dict[str, Any]:
        trusted_binding = _binding(binding)
        reasons: set[str] = set()
        artifact_conflict = any(name in artifact and artifact.get(name) != trusted_binding[name]
                                for name in BINDING_FIELDS)
        design_conflict = any(name in design_shot and design_shot.get(name) != trusted_binding[name]
                              for name in BINDING_FIELDS)
        if artifact_conflict:
            reasons.add("artifact_binding_conflict")
        if design_conflict:
            reasons.add("design_binding_conflict")
        digest = None
        raw_probe: Mapping[str, Any] = {}
        frame_evidence: Mapping[str, Any] = {}
        snapshot_error = False
        try:
            with _ArtifactSnapshot(artifact, max_bytes=self._max_artifact_bytes) as snapshot:
                digest = snapshot.digest
                assert snapshot.path is not None
                raw_probe = self._media_adapter.probe_json(snapshot.path, source_fd=snapshot.snapshot_fd)
                snapshot.assert_stable()
                format_data = raw_probe.get("format", {}) if isinstance(raw_probe, Mapping) else {}
                duration_for_frames = float(format_data["duration"])
                if not math.isfinite(duration_for_frames) or duration_for_frames <= 0:
                    raise EvaluationContractError("trusted probe duration is unavailable")
                frame_evidence = self._media_adapter.verify_video_frames(
                    snapshot.path, duration_for_frames, source_fd=snapshot.snapshot_fd)
                snapshot.assert_stable()
        except Exception:
            snapshot_error = True
            reasons.add("artifact_evidence_unavailable")
            raw_probe, frame_evidence = {}, {}

        streams = raw_probe.get("streams", []) if isinstance(raw_probe, Mapping) else []
        stream = next((item for item in streams if isinstance(item, Mapping)
                       and item.get("codec_type") == "video"), {})
        format_data = raw_probe.get("format", {}) if isinstance(raw_probe, Mapping) \
            and isinstance(raw_probe.get("format"), Mapping) else {}
        width, height, codec = stream.get("width"), stream.get("height"), stream.get("codec_name")
        try:
            duration = float(format_data["duration"])
            if not math.isfinite(duration) or duration <= 0:
                duration = None
        except (KeyError, TypeError, ValueError):
            duration = None
        start_frame = frame_evidence.get("start_anchor") if isinstance(frame_evidence, Mapping) else None
        end_frame = frame_evidence.get("end_anchor") if isinstance(frame_evidence, Mapping) else None
        readable = frame_evidence.get("readable") if isinstance(frame_evidence, Mapping) \
            and isinstance(frame_evidence.get("readable"), bool) else None

        def gate(passed: bool | None, evidence: str) -> dict[str, str]:
            if passed is None:
                reasons.add("measured_evidence_unavailable")
            return {"status": "skipped" if passed is None else "passed" if passed else "failed",
                    "evidence": evidence}

        expected = expected_media if isinstance(expected_media, Mapping) else design_shot
        expected_width, expected_height = expected.get("width"), expected.get("height")
        ratio = None if not isinstance(width, int) or not isinstance(height, int) or height <= 0 else width / height
        expected_ratio = None if not isinstance(expected_width, int) or not isinstance(expected_height, int) \
            or expected_height <= 0 else expected_width / expected_height
        expected_duration = expected.get("duration_seconds")
        anchor_contract = expected.get("anchor_contract")
        anchor_required = bool(expected.get("anchor_required"))

        def anchor_gate(name: str, frame: Any) -> dict[str, str]:
            if not isinstance(frame, Mapping) or _DIGEST.fullmatch(str(frame.get("sha256", ""))) is None:
                reasons.add("anchor_evidence_unavailable")
                return gate(None, f"trusted decoded {name} unavailable")
            if not anchor_required:
                return gate(True, f"trusted decoded {name}; no approved anchor constraint")
            contract = anchor_contract.get(name) if isinstance(anchor_contract, Mapping) else None
            if not isinstance(contract, Mapping) or _DIGEST.fullmatch(str(contract.get("frame_sha256", ""))) is None:
                reasons.add("anchor_evidence_unavailable")
                return gate(None, f"approved {name} evidence unavailable")
            return gate(frame["sha256"] == contract["frame_sha256"], f"trusted {name} digest comparison")

        gates = {
            "artifact_integrity": gate(None if artifact_conflict or snapshot_error or digest is None
                else digest == trusted_binding["artifact_sha256"] == artifact.get("sha256"),
                "trusted artifact identity conflict" if artifact_conflict else "trusted snapshot digest verification"),
            "dimensions": gate(None if design_conflict or None in (width, height, expected_width, expected_height)
                else (width, height) == (expected_width, expected_height),
                "trusted design identity conflict" if design_conflict else "trusted probe dimensions"),
            "codec": gate(None if design_conflict or codec is None or expected.get("codec") is None
                else codec == expected["codec"], "trusted design identity conflict" if design_conflict
                else "trusted probe codec"),
            "duration": gate(None if duration is None or not isinstance(expected_duration, (int, float))
                or isinstance(expected_duration, bool) else abs(duration - expected_duration) <= 0.1,
                "trusted probe duration"),
            "aspect_ratio": gate(None if ratio is None or expected_ratio is None
                else abs(ratio - expected_ratio) <= 0.001, "trusted probe aspect ratio"),
            "frame_readability": gate(readable, "trusted complete PNG frame decode"),
            "start_anchor": anchor_gate("start_anchor", start_frame),
            "end_anchor": anchor_gate("end_anchor", end_frame),
        }
        evidence = {"width": width, "height": height, "codec": codec, "duration_seconds": duration,
                    "readable": readable, "start_anchor": copy.deepcopy(start_frame),
                    "end_anchor": copy.deepcopy(end_frame)}
        return {"binding": trusted_binding, "gates": gates, "evidence": evidence,
                "manual_review_reasons": sorted(reasons)}

    def validate_semantic_evaluation(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping) or set(payload) != {"binding", "gates"}:
            raise EvaluationContractError("semantic evaluation must be closed")
        return {"binding": _binding(payload["binding"]),
                "gates": _validate_gates(payload["gates"], SEMANTIC_GATE_ORDER)}

    @staticmethod
    def _manual(reasons: set[str]) -> dict[str, Any]:
        closed = sorted(reason for reason in reasons if reason in MANUAL_REVIEW_REASONS)
        return {"action": "manual_review",
                "manual_review_reasons": closed or ["measured_evidence_unavailable"]}

    @classmethod
    def _decision(cls, binding: Mapping[str, Any], measured: Mapping[str, Any], semantic: Mapping[str, Any],
                  allowance: Mapping[str, Any], quote: Mapping[str, Any], reasons: set[str]) \
            -> tuple[dict[str, Any], list[str]]:
        gates = {**measured, **semantic}
        failed_gates = [name for name in (*MEASURED_GATE_ORDER, *SEMANTIC_GATE_ORDER)
                        if gates[name]["status"] in {"failed", "skipped"}]
        unavailable = [name for name in failed_gates if gates[name]["status"] == "skipped"]
        semantic_skipped = [semantic[name] for name in SEMANTIC_GATE_ORDER
                            if semantic[name]["status"] == "skipped"]
        if semantic_skipped:
            evidence = {gate["evidence"] for gate in semantic_skipped}
            if evidence == {"semantic binding conflict"}:
                reasons.add("semantic_binding_conflict")
            elif evidence == {"semantic evidence invalid"}:
                reasons.add("semantic_evidence_invalid")
            else:
                reasons.add("semantic_evidence_unavailable")
        expected = (binding["project_id"], binding["batch_version"], binding["design_version"],
                    binding["design_fingerprint"], binding["quote_fingerprint"])
        if (quote.get("project_id"), quote.get("quote_version"), quote.get("design_version"),
                quote.get("design_fingerprint"), quote.get("quote_fingerprint")) != expected:
            reasons.add("quote_binding_conflict")
        if (allowance.get("project_id"), allowance.get("quote_version"), allowance.get("design_version"),
                allowance.get("design_fingerprint"), allowance.get("quote_fingerprint")) != expected \
                or allowance.get("allowance_id") != binding["allowance_id"]:
            reasons.add("allowance_binding_conflict")
        if reasons or unavailable:
            return cls._manual(reasons), failed_gates
        failed = [name for name in failed_gates if gates[name]["status"] == "failed"]
        if not failed:
            return {"action": "accepted"}, []
        if "artifact_integrity" in failed:
            return {"action": "rejected"}, failed_gates
        directives = {REPAIR_BY_GATE.get(name) for name in failed}
        if None in directives:
            reasons.add("repair_directive_unavailable")
            return cls._manual(reasons), failed_gates
        if len(directives) != 1:
            reasons.add("mixed_repair_directives")
            return cls._manual(reasons), failed_gates
        if allowance.get("state") != "active":
            reasons.add("allowance_inactive")
            return cls._manual(reasons), failed_gates
        directive = next(iter(directives))
        next_attempt = binding["attempt"] + 1
        item = next((entry for entry in quote.get("items", []) if isinstance(entry, Mapping)
                     and entry.get("shot_id") == binding["shot_id"]), None)
        planned = next((entry for entry in item.get("attempts", []) if isinstance(entry, Mapping)
                        and entry.get("attempt_number") == next_attempt), None) if isinstance(item, Mapping) else None
        if not isinstance(planned, Mapping) or planned.get("repair_directive") != directive:
            reasons.add("retry_not_prequoted")
            return cls._manual(reasons), failed_gates
        fingerprint = planned.get("request_fingerprint")
        request_exists = any(request.get("shot_id") == binding["shot_id"] and request.get("attempt") == next_attempt
                             and request.get("request_fingerprint") == fingerprint
                             for request in allowance.get("requests", []))
        consumed = any(reservation.get("shot_id") == binding["shot_id"] and reservation.get("attempt") == next_attempt
                       for reservation in allowance.get("reservations", []))
        if not request_exists or consumed or not isinstance(fingerprint, str) or _DIGEST.fullmatch(fingerprint) is None:
            reasons.add("retry_unavailable")
            return cls._manual(reasons), failed_gates
        return {"action": "retry", "repair_directive": directive,
                "request_fingerprint": fingerprint}, failed_gates

    def _normalize_evaluator(self, evaluator: Any, *, created: datetime) -> tuple[dict[str, Any], set[str]]:
        result = {"provider_claim": "unavailable", "model_claim": "unavailable",
                  "claimed_evaluated_at": None, "trust_level": "untrusted"}
        reasons: set[str] = set()
        if not isinstance(evaluator, Mapping) or set(evaluator) != {"provider", "model", "evaluated_at"}:
            reasons.add("semantic_evaluator_invalid")
            return result, reasons
        provider, model = evaluator.get("provider"), evaluator.get("model")
        if provider != "codex" or not isinstance(model, str) \
                or re.fullmatch(r"[A-Za-z0-9._:/-]{1,128}", model) is None:
            reasons.add("semantic_evaluator_invalid")
            return result, reasons
        try:
            claimed = parse_rfc3339(evaluator.get("evaluated_at"), label="claimed_evaluated_at")
        except ValueError:
            reasons.add("semantic_evaluator_invalid")
            return result, reasons
        if claimed > created + _MAX_FUTURE_SKEW or created - claimed > _MAX_EVALUATOR_AGE:
            reasons.add("semantic_evaluator_invalid")
            return result, reasons
        result.update(provider_claim=provider, model_claim=model,
                      claimed_evaluated_at=claimed.isoformat(timespec="seconds").replace("+00:00", "Z"))
        return result, reasons

    def evaluate(self, artifact: Mapping[str, Any], design_shot: Mapping[str, Any],
                 semantic_payload: Mapping[str, Any], *, binding: Mapping[str, Any], allowance: Mapping[str, Any],
                 quote: Mapping[str, Any], evaluation_id: str, evaluator: Mapping[str, Any],
                 _created_at: str | None = None) -> dict[str, Any]:
        trusted_binding = _binding(binding)
        now, issued_at = self._trusted_now()
        if _created_at is not None:
            issued = parse_rfc3339(_created_at, label="created_at")
            if issued > now + _MAX_FUTURE_SKEW or now - issued > _MAX_EVALUATOR_AGE:
                raise EvaluationContractError("receipt created_at is outside the trusted clock window")
            issued_at = issued.isoformat(timespec="seconds").replace("+00:00", "Z")
        item = next((entry for entry in quote.get("items", []) if isinstance(entry, Mapping)
                     and entry.get("shot_id") == trusted_binding["shot_id"]), None)
        attempt = next((entry for entry in item.get("attempts", []) if isinstance(entry, Mapping)
                        and entry.get("attempt_number") == trusted_binding["attempt"]), None) if isinstance(item, Mapping) else None
        request = attempt.get("request", {}) if isinstance(attempt, Mapping) else {}
        profile = quote.get("output_profile", {}) if isinstance(quote.get("output_profile"), Mapping) else {}
        anchor_contract = attempt.get("anchor_contract") if isinstance(attempt, Mapping) else None
        if request.get("mode") in {"frames2video", "multiframe2video"}:
            indexed = [(index, entry) for index, entry in enumerate(request.get("references", []))
                       if isinstance(entry, Mapping) and entry.get("role") == "frame"]
            expected_references = ((indexed[0][1].get("sha256"), indexed[0][0], "frame"),
                                   (indexed[-1][1].get("sha256"), indexed[-1][0], "frame")) \
                if len(indexed) >= 2 else ((None, None, None), (None, None, None))
            contract_references = ((
                anchor_contract.get("start_anchor", {}).get("reference_sha256"),
                anchor_contract.get("start_anchor", {}).get("reference_index"),
                anchor_contract.get("start_anchor", {}).get("role")), (
                anchor_contract.get("end_anchor", {}).get("reference_sha256"),
                anchor_contract.get("end_anchor", {}).get("reference_index"),
                anchor_contract.get("end_anchor", {}).get("role"),
            )) if isinstance(anchor_contract, Mapping) else ((None, None, None), (None, None, None))
            if contract_references != expected_references:
                anchor_contract = None
        expected_media = {"width": profile.get("width"), "height": profile.get("height"),
                          "codec": profile.get("codec"), "duration_seconds": request.get("duration_seconds"),
                          "anchor_required": request.get("mode") in {"frames2video", "multiframe2video"},
                          "anchor_contract": anchor_contract}
        measured = self.measure_clip(artifact, design_shot, binding=trusted_binding, expected_media=expected_media)
        reasons = set(measured["manual_review_reasons"])
        try:
            semantic = self.validate_semantic_evaluation(semantic_payload)
            if semantic["binding"] != trusted_binding:
                raise EvaluationContractError("semantic binding conflict")
        except EvaluationContractError as exc:
            fallback = "semantic binding conflict" if "binding conflict" in str(exc) else "semantic evidence invalid"
            semantic = {"binding": trusted_binding, "gates": {
                name: {"status": "skipped", "evidence": fallback}
                for name in SEMANTIC_GATE_ORDER}}
        evaluator_receipt, evaluator_reasons = self._normalize_evaluator(evaluator, created=now)
        reasons.update(evaluator_reasons)
        decision, failed = self._decision(measured["binding"], measured["gates"], semantic["gates"],
                                          allowance, quote, reasons)
        artifact_evidence = {name: copy.deepcopy(artifact.get(name)) for name in
                             ("path", "mime_type", "size_bytes", "sha256", "provenance")}
        artifact_evidence["probe"] = {name: measured["evidence"].get(name) for name in
                                      ("width", "height", "codec", "duration_seconds")}
        artifact_evidence["frames"] = {name: measured["evidence"].get(name) for name in
                                       ("readable", "start_anchor", "end_anchor")}
        receipt = {"schema_version": "1.0", "evaluation_id": evaluation_id, "created_at": issued_at,
                   "binding": measured["binding"], "artifact_evidence": artifact_evidence,
                   "measured_gates": measured["gates"], "semantic_gates": semantic["gates"],
                   "failed_gates": failed, "decision": decision, "semantic_evaluator": evaluator_receipt}
        receipt["evaluation_fingerprint"] = canonical_fingerprint(receipt)
        try:
            validate_contract(receipt, "shot_evaluation.schema.json")
        except ValueError as exc:
            raise EvaluationContractError("evaluation receipt is invalid") from exc
        return receipt

    def verify_receipt(self, receipt: Mapping[str, Any], *, artifact: Mapping[str, Any],
                       design_shot: Mapping[str, Any], allowance: Mapping[str, Any],
                       quote: Mapping[str, Any]) -> dict[str, Any]:
        """Rebuild from one current immutable snapshot and compare every decision field."""
        evaluator = receipt.get("semantic_evaluator", {})
        rebuilt = self.evaluate(artifact, design_shot,
            {"binding": receipt.get("binding"), "gates": receipt.get("semantic_gates")},
            binding=receipt.get("binding"), allowance=allowance, quote=quote,
            evaluation_id=receipt.get("evaluation_id"), evaluator={
                "provider": evaluator.get("provider_claim"), "model": evaluator.get("model_claim"),
                "evaluated_at": evaluator.get("claimed_evaluated_at")}, _created_at=receipt.get("created_at"))
        if rebuilt != dict(receipt):
            raise EvaluationContractError("evaluation receipt does not match trusted recomputation")
        return rebuilt


__all__ = ["EvaluationContractError", "VideoEvaluationService", "MEASURED_GATES", "SEMANTIC_GATES"]
