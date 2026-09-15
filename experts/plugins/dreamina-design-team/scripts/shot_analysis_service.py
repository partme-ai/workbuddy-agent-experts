"""Validate Codex semantic shot annotations against immutable machine evidence."""

from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from scripts.json_contracts import (
    ContractValidationError,
    canonical_fingerprint,
    validate_contract,
)
from scripts.video_project_store import (
    VersionCommitIndeterminateError,
    VersionReconciliationError,
    VideoProjectStore,
)


SHOT_SIZES = frozenset({"extreme_wide", "wide", "full", "medium", "close_up", "extreme_close_up", "none"})
CAMERA_MOVES = frozenset({"static", "push_in", "pull_out", "pan", "tilt", "truck", "pedestal", "follow", "handheld", "orbit", "zoom", "unknown"})
RHYTHM_ROLES = frozenset({"hook", "setup", "build", "beat", "turn", "payoff", "breath", "close"})
NARRATIVE_CATEGORIES = frozenset({"establishing", "subject", "action", "detail", "transition", "text", "product", "reaction", "atmosphere", "other"})
REQUIRED_GATES = frozenset({
    "schema", "machine_fingerprint", "timeline", "duration", "shot_ids",
    "boundary_provenance", "keyframes", "taxonomy", "frame_specificity",
    "description_dedup", "cast_subjects", "category_evidence", "motion_camera",
    "rhythm_completeness", "transcript_provenance",
})


@dataclass(frozen=True)
class GateResult:
    name: str
    status: str
    violations: Sequence[str]


class ShotAnalysisService:
    """Bind closed semantic annotations to one immutable analysis version."""

    def __init__(self, project_store: VideoProjectStore) -> None:
        self._store = project_store

    def validate_and_persist(
        self,
        project_id: str,
        analysis_version: str,
        annotations: Mapping[str, Any],
        *,
        indeterminate_commit: VersionCommitIndeterminateError | None = None,
    ) -> dict[str, Any]:
        analysis = self._load_analysis(project_id, analysis_version)
        try:
            candidate = dict(annotations)
            candidate.setdefault("transcript", None)
            schema_candidate = {
                **candidate, "version": "v001", "analysis_version": analysis_version
            }
            validate_contract(schema_candidate, "shot_annotation.schema.json")
        except (ContractValidationError, TypeError, ValueError):
            blocked = GateResult(
                "schema",
                "failed",
                ("annotation does not satisfy the closed semantic schema",),
            )
            skipped = [
                GateResult(name, "skipped", ("schema gate blocked evaluation",))
                for name in (
                    "machine_fingerprint", "timeline", "duration", "shot_ids",
                    "boundary_provenance", "keyframes", "taxonomy",
                    "frame_specificity", "description_dedup", "cast_subjects",
                    "category_evidence", "motion_camera", "rhythm_completeness",
                    "transcript_provenance",
                )
            ]
            return {
                "status": "failed",
                "gates": [asdict(blocked), *(asdict(gate) for gate in skipped)],
                "annotation_version": None,
            }

        checks: list[tuple[str, Callable[[], Sequence[str]]]] = [
            ("schema", lambda: ()),
            ("machine_fingerprint", lambda: self._fingerprint(candidate, analysis)),
            ("timeline", lambda: self._timeline(analysis)),
            ("duration", lambda: self._duration(analysis)),
            ("shot_ids", lambda: self._shot_ids(candidate, analysis)),
            ("boundary_provenance", lambda: self._boundaries(analysis)),
            ("keyframes", lambda: self._keyframes(analysis)),
            ("taxonomy", lambda: self._taxonomy(candidate)),
            ("frame_specificity", lambda: self._specificity(candidate)),
            ("description_dedup", lambda: self._dedup(candidate)),
            ("cast_subjects", lambda: self._cast(candidate)),
            ("category_evidence", lambda: self._category_evidence(candidate)),
            ("motion_camera", lambda: self._motion(candidate, analysis)),
            ("rhythm_completeness", lambda: self._rhythm(candidate)),
        ]
        gates = [self._gate(name, check()) for name, check in checks]
        transcript_gate, skip_allowed = self._transcript(candidate, analysis, self._store.get(project_id))
        gates.append(transcript_gate)
        blocking = any(g.status == "failed" for g in gates) or any(
            g.status == "skipped" and (g.name != "transcript_provenance" or not skip_allowed)
            for g in gates
        )
        result: dict[str, Any] = {"status": "failed" if blocking else "passed", "gates": [asdict(g) for g in gates], "annotation_version": None}
        if not blocking:
            document = {**candidate, "analysis_version": analysis_version}
            if indeterminate_commit is None:
                persisted = self._store.write_version(
                    project_id,
                    "annotation",
                    document,
                    schema_name="shot_annotation.schema.json",
                )
            else:
                expected_path = (
                    self._store.project_root(project_id)
                    / "annotation"
                    / f"{indeterminate_commit.version}.json"
                )
                candidate_document = {
                    **document,
                    "version": indeterminate_commit.version,
                }
                if (
                    indeterminate_commit.project_id != project_id
                    or indeterminate_commit.family != "annotation"
                    or indeterminate_commit.path != expected_path
                    or canonical_fingerprint(candidate_document)
                    != indeterminate_commit.payload_fingerprint
                ):
                    raise VersionReconciliationError(
                        project_id=project_id,
                        family="annotation",
                        version=indeterminate_commit.version,
                        path=expected_path,
                        reason="retry does not match the exact indeterminate annotation commit",
                    )
                persisted = self._store.reconcile_version(
                    project_id,
                    "annotation",
                    indeterminate_commit.version,
                    indeterminate_commit.payload_fingerprint,
                    "shot_annotation.schema.json",
                )
            result["annotation_version"] = persisted["version"]
            if self._store.get(project_id)["state"] == "analyzing":
                self._store.transition(project_id, expected="analyzing", next_state="analysis_review", evidence={"analysis_version": analysis_version, "annotation_version": persisted["version"], "machine_fingerprint": analysis["machine_fingerprint"]})
        return result

    def _load_analysis(self, project_id: str, version: str) -> dict[str, Any]:
        if re.fullmatch(r"v[0-9]{3,}", version) is None:
            raise KeyError(version)
        target = self._store.project_root(project_id) / "analysis" / f"{version}.json"
        try: payload = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc: raise KeyError(version) from exc
        validate_contract(payload, "shot_analysis.schema.json")
        return payload

    @staticmethod
    def _gate(name: str, violations: Sequence[str]) -> GateResult:
        return GateResult(name, "failed" if violations else "passed", tuple(violations))

    @staticmethod
    def _fingerprint(annotation, analysis):
        return () if annotation["machine_fingerprint"] == analysis["machine_fingerprint"] else ("annotation is bound to a different machine fingerprint",)

    @staticmethod
    def _timeline(analysis):
        cuts = analysis["cuts"]; shots = analysis["shots"]
        bad = len(cuts) != len(shots) + 1
        for index, shot in enumerate(shots):
            measured = shot["measured"]
            bad |= not (math.isclose(measured["start_seconds"], cuts[index], abs_tol=.001) and math.isclose(measured["end_seconds"], cuts[index + 1], abs_tol=.001))
        return ("measured shot boundaries do not form the declared continuous timeline",) if bad else ()

    @staticmethod
    def _duration(analysis):
        bad = any(not math.isclose(s["measured"]["duration_seconds"], s["measured"]["end_seconds"] - s["measured"]["start_seconds"], abs_tol=.001) for s in analysis["shots"])
        bad |= not math.isclose(sum(s["measured"]["duration_seconds"] for s in analysis["shots"]), analysis["source"]["duration_seconds"], abs_tol=.01)
        return ("shot duration arithmetic does not match source duration",) if bad else ()

    @staticmethod
    def _shot_ids(annotation, analysis):
        wanted = [f"S{i:02d}" for i in range(1, len(analysis["shots"]) + 1)]
        actual = [s["id"] for s in analysis["shots"]]
        annotated = [s["id"] for s in annotation["shots"]]
        return ("shot identifiers are not sequential and exactly matched",) if actual != wanted or annotated != wanted else ()

    @staticmethod
    def _boundaries(analysis):
        manual = set(analysis["manual_cuts"]); bad = False
        for index, shot in enumerate(analysis["shots"]):
            measured = shot["measured"]; expected = "source_start" if index == 0 else ("manual_split" if measured["start_seconds"] in manual else "scene")
            bad |= measured["boundary_source"] != expected
        return ("boundary source is inconsistent with declared manual cuts",) if bad else ()

    @staticmethod
    def _keyframes(analysis):
        frames = analysis["frame_checksums"]
        bad = any(f"{shot['id']}:{label}" not in frames for shot in analysis["shots"] for label in ("a", "b"))
        return ("each shot requires both interior keyframes",) if bad else ()

    @staticmethod
    def _taxonomy(annotation):
        bad = any(s["shot_size"] not in SHOT_SIZES or s["camera"] not in CAMERA_MOVES or s["category"] not in NARRATIVE_CATEGORIES or (s["rhythm_role"] is not None and s["rhythm_role"] not in RHYTHM_ROLES) for s in annotation["shots"])
        return ("annotation contains a value outside the closed taxonomies",) if bad else ()

    @staticmethod
    def _specificity(annotation):
        def specific(text):
            compact = re.sub(r"\s", "", text); chinese = len(re.findall(r"[\u3400-\u9fff]", compact))
            return chinese >= 12 or len(re.findall(r"\b[\w'-]+\b", text)) >= 8
        return ("frame descriptions must contain 12 Chinese characters or 8 English words",) if any(not specific(s["frame_description"]) for s in annotation["shots"]) else ()

    @staticmethod
    def _dedup(annotation):
        normalized = [re.sub(r"\W+", "", s["frame_description"].casefold()) for s in annotation["shots"]]
        return ("frame descriptions must be shot-specific",) if len(normalized) != len(set(normalized)) else ()

    @staticmethod
    def _cast(annotation):
        identities = {}; bad = False
        for shot in annotation["shots"]:
            for subject in shot["subjects"]:
                previous = identities.setdefault(subject["id"], subject["name"].casefold())
                bad |= previous != subject["name"].casefold()
        return ("a cast identity has inconsistent names",) if bad else ()

    @staticmethod
    def _category_evidence(annotation):
        signals = {"establishing": ("establish", "location", "wide"), "subject": ("subject", "person", "presenter"), "action": ("action", "moves", "doing"), "detail": ("detail", "isolates", "close"), "transition": ("transition", "change"), "text": ("text", "title", "words"), "product": ("product", "device"), "reaction": ("reaction", "responds"), "atmosphere": ("atmosphere", "mood"), "other": ("other",)}
        bad = any(not s["category_evidence"].strip() or not any(word in s["category_evidence"].casefold() for word in signals[s["category"]]) for s in annotation["shots"] if s["category"] in signals)
        return ("narrative category lacks category-specific evidence",) if bad else ()

    @staticmethod
    def _motion(annotation, analysis):
        by_id = {s["id"]: s for s in analysis["shots"]}; moving = CAMERA_MOVES - {"static", "unknown"}; bad = False
        for shot in annotation["shots"]:
            measured_shot = by_id.get(shot["id"])
            if measured_shot is None:
                bad = True
                continue
            median = measured_shot["measured"]["motion_median"]
            if median is not None: bad |= (shot["camera"] in moving and median <= 1.0) or (shot["camera"] == "static" and median >= 20.0)
        return ("camera claim conflicts with measured motion",) if bad else ()

    @staticmethod
    def _rhythm(annotation):
        states = [(s["rhythm_role"] is not None, bool(s["rhythm_evidence"])) for s in annotation["shots"]]
        complete = all(role and evidence for role, evidence in states); empty = all(not role and not evidence for role, evidence in states)
        return ("rhythm annotations must be complete for every shot or empty for every shot",) if not (complete or empty) else ()

    @staticmethod
    def _transcript(annotation, analysis, project):
        transcript = annotation.get("transcript")
        if transcript is None:
            return GateResult("transcript_provenance", "skipped", ("no transcript supplied",)), project["audio_policy"] == "silent"
        if transcript["policy"] == "user_supplied_script":
            return GateResult("transcript_provenance", "skipped", ("user supplied script does not claim ASR provenance",)), True
        previous = -1.0; violations = []
        if not transcript["provider"].strip() or not transcript["segments"]: violations.append("ASR provider and segments are required")
        for segment in transcript["segments"]:
            if segment["start_seconds"] < previous or segment["end_seconds"] <= segment["start_seconds"] or segment["end_seconds"] > analysis["source"]["duration_seconds"]: violations.append("ASR segment timing is invalid")
            previous = segment["end_seconds"]
        return GateResult("transcript_provenance", "failed" if violations else "passed", tuple(violations)), False


__all__ = ["CAMERA_MOVES", "GateResult", "NARRATIVE_CATEGORIES", "REQUIRED_GATES", "RHYTHM_ROLES", "SHOT_SIZES", "ShotAnalysisService"]
