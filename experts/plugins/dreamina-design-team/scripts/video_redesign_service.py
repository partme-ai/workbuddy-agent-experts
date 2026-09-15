"""Prepare immutable redesign candidates and commit rights-aware versions."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Mapping, TypedDict

from scripts.json_contracts import ContractValidationError, canonical_fingerprint, validate_contract
from scripts.video_project_store import VideoProjectStore
from scripts.video_project_store import (
    VersionCommitIndeterminateError,
    VersionReconciliationError,
)
from scripts.video_rights_service import REUSE_DIMENSIONS, RightsScopeError, VideoRightsService


FORBIDDEN_ORIGINAL_REUSE = frozenset({"likeness", "voice", "dialogue", "music", "effects", "ambience", "brand", "artwork", "distinctive_props"})
REQUIRED_REPLACEMENTS = frozenset({"likeness", "voice", "dialogue", "music", "brand", "artwork", "settings", "costume", "distinctive_props"})


class OriginalityPolicyError(ValueError):
    """An original redesign attempts expressive reuse or omits a replacement."""


class RedesignBindingError(PermissionError):
    """A candidate, analysis, project, or rights receipt binding is invalid."""


class SimilarityAudit(TypedDict):
    preserved: list[str]
    replaced: list[str]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class VideoRedesignService:
    """Keep candidates transient until originality or candidate-bound rights pass."""

    def __init__(self, project_store: VideoProjectStore) -> None:
        self._store = project_store

    def prepare_candidate(self, project_id: str, analysis_version: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        project = self._store.get(project_id)
        if re.fullmatch(r"v[0-9]{3,}", analysis_version) is None:
            raise RedesignBindingError("invalid analysis version")
        analysis = self._read(project_id, "analysis", analysis_version, "shot_analysis.schema.json")
        annotation = self._read(project_id, "annotation", analysis_version, "shot_annotation.schema.json")
        candidate_payload = json.loads(json.dumps(dict(payload), ensure_ascii=False, allow_nan=False))
        mode = candidate_payload.get("creative_mode")
        if mode != project["creative_mode"]:
            raise RedesignBindingError("creative mode differs from the project")
        if annotation["analysis_version"] != analysis_version or annotation["machine_fingerprint"] != analysis["machine_fingerprint"] or candidate_payload.get("machine_fingerprint") != analysis["machine_fingerprint"]:
            raise RedesignBindingError("redesign differs from passed measured analysis")
        preserve = candidate_payload.get("preserve")
        if not isinstance(preserve, list) or len(preserve) != len(set(preserve)) or not set(preserve) <= REUSE_DIMENSIONS:
            raise ContractValidationError("preserve must contain unique known reuse dimensions")
        self._assert_mode_policy(mode, candidate_payload, preserve)
        core = {
            "schema_version": "1.0", "project_id": project_id,
            "analysis_version": analysis_version, "source_sha256": analysis["source"]["source_sha256"],
            "machine_fingerprint": analysis["machine_fingerprint"], "creative_mode": mode,
            "payload": candidate_payload,
            "similarity_audit": self._audit(preserve),
        }
        fingerprint = canonical_fingerprint(core)
        # Reuse the committed contract to close every candidate payload field before
        # its fingerprint can be presented for a rights assertion.
        validate_contract(
            {
                **core,
                "version": "v001",
                "parent_version": None,
                "rights_receipt_id": None,
                "design_fingerprint": fingerprint,
                "committed_at": "candidate-validation",
            },
            "video_redesign.schema.json",
        )
        return {**core, "design_fingerprint": fingerprint}

    def commit_version(
        self,
        candidate: Mapping[str, Any],
        rights_receipt_id: str | None,
        *,
        indeterminate_commit: VersionCommitIndeterminateError | None = None,
    ) -> dict[str, Any]:
        project_id = candidate.get("project_id")
        if not isinstance(project_id, str):
            raise RedesignBindingError("candidate project binding is absent")
        core = {key: value for key, value in candidate.items() if key != "design_fingerprint"}
        fingerprint = candidate.get("design_fingerprint")
        if canonical_fingerprint(core) != fingerprint:
            raise RedesignBindingError("candidate changed after fingerprinting")
        self._validate_candidate_against_current_evidence(candidate)
        self._validate_closed_candidate(candidate)
        mode = candidate["creative_mode"]
        if mode == "authorized_replication":
            if not isinstance(rights_receipt_id, str):
                raise RedesignBindingError("authorized replication requires a rights receipt")
            receipt = self._find_receipt(project_id, rights_receipt_id)
            binding = {
                **{key: candidate[key] for key in ("project_id", "source_sha256", "creative_mode", "design_fingerprint")},
                "required_media": candidate["payload"]["required_media"],
                "purpose": candidate["payload"]["purpose"],
                "audience": candidate["payload"]["audience"],
                "territory": candidate["payload"]["territory"],
            }
            try:
                VideoRightsService(self._store, native_confirmer=None).assert_scope(receipt, required=set(candidate["payload"]["preserve"]), binding=binding)
            except RightsScopeError as exc:
                raise RedesignBindingError("rights receipt does not authorize this candidate") from exc
        elif rights_receipt_id is not None:
            raise RedesignBindingError("original redesign must not attach a replication receipt")
        if indeterminate_commit is not None:
            return self._reconcile_indeterminate(
                candidate, rights_receipt_id, indeterminate_commit
            )
        document = {
            **core, "rights_receipt_id": rights_receipt_id,
            "design_fingerprint": fingerprint,
            "committed_at": _now(),
        }
        return self._store.write_version(
            project_id,
            "redesign",
            document,
            schema_name="video_redesign.schema.json",
            parent_version_field="parent_version",
        )

    def _validate_closed_candidate(self, candidate: Mapping[str, Any]) -> None:
        payload = candidate.get("payload")
        if not isinstance(payload, Mapping):
            raise ContractValidationError("candidate payload is absent")
        preserve = payload.get("preserve")
        if not isinstance(preserve, list) or len(preserve) != len(set(preserve)) or not set(preserve) <= REUSE_DIMENSIONS:
            raise ContractValidationError("preserve must contain unique known reuse dimensions")
        self._assert_mode_policy(candidate.get("creative_mode"), payload, preserve)
        validate_contract(
            {
                **candidate,
                "version": "v001",
                "parent_version": None,
                "rights_receipt_id": None,
                "committed_at": "candidate-validation",
            },
            "video_redesign.schema.json",
        )

    @staticmethod
    def _assert_mode_policy(mode: Any, payload: Mapping[str, Any], preserve: list[str]) -> None:
        replacements = payload.get("replacements")
        if mode == "original_redesign":
            if set(preserve) & FORBIDDEN_ORIGINAL_REUSE:
                raise OriginalityPolicyError("original redesign cannot reuse source expressive identity or content")
            if not isinstance(replacements, Mapping) or set(replacements) != REQUIRED_REPLACEMENTS or any(not isinstance(value, str) or not value.strip() for value in replacements.values()):
                raise OriginalityPolicyError("original redesign requires explicit expressive replacements")
        elif replacements is not None:
            raise ContractValidationError("authorized replication must not declare original replacements")

    def _reconcile_indeterminate(
        self,
        candidate: Mapping[str, Any],
        rights_receipt_id: str | None,
        commit: VersionCommitIndeterminateError,
    ) -> dict[str, Any]:
        project_id = candidate["project_id"]
        expected_path = (
            self._store.project_root(project_id) / "redesign" / f"{commit.version}.json"
        )
        if (
            commit.project_id != project_id
            or commit.family != "redesign"
            or commit.path != expected_path
        ):
            raise VersionReconciliationError(
                project_id=project_id,
                family="redesign",
                version=commit.version,
                path=expected_path,
                reason="retry does not identify the exact indeterminate redesign commit",
            )
        design = self._store.reconcile_version(
            project_id,
            "redesign",
            commit.version,
            commit.payload_fingerprint,
            "video_redesign.schema.json",
        )
        expected = {
            **{key: value for key, value in candidate.items() if key != "design_fingerprint"},
            "design_fingerprint": candidate["design_fingerprint"],
            "rights_receipt_id": rights_receipt_id,
        }
        if any(design.get(key) != value for key, value in expected.items()):
            raise VersionReconciliationError(
                project_id=project_id,
                family="redesign",
                version=commit.version,
                path=expected_path,
                reason="retry candidate does not match the committed redesign",
            )
        return design

    def _validate_candidate_against_current_evidence(self, candidate: Mapping[str, Any]) -> None:
        analysis = self._read(candidate["project_id"], "analysis", candidate["analysis_version"], "shot_analysis.schema.json")
        annotation = self._read(candidate["project_id"], "annotation", candidate["analysis_version"], "shot_annotation.schema.json")
        if analysis["source"]["source_sha256"] != candidate["source_sha256"] or analysis["machine_fingerprint"] != candidate["machine_fingerprint"] or annotation["machine_fingerprint"] != candidate["machine_fingerprint"]:
            raise RedesignBindingError("candidate no longer matches immutable analysis evidence")
        audit = candidate.get("similarity_audit", {})
        preserved, replaced = audit.get("preserved", []), audit.get("replaced", [])
        declared = set(candidate.get("payload", {}).get("preserve", []))
        if set(preserved) != declared or set(preserved) | set(replaced) != REUSE_DIMENSIONS or set(preserved) & set(replaced) or len(preserved) + len(replaced) != len(REUSE_DIMENSIONS):
            raise RedesignBindingError("similarity audit must partition every reuse dimension exactly once")

    def _find_receipt(self, project_id: str, receipt_id: str) -> dict[str, Any]:
        try:
            return self._store.find_version_by_field(
                project_id,
                "rights_receipt",
                field="receipt_id",
                value=receipt_id,
                schema_name="video_rights_receipt.schema.json",
            )
        except VersionReconciliationError as exc:
            raise RedesignBindingError("rights receipt was not safely resolved") from exc

    def _read(self, project_id: str, family: str, version: str, schema: str) -> dict[str, Any]:
        try:
            return self._store.read_version(project_id, family, version, schema)
        except (ValueError, VersionReconciliationError) as exc:
            raise RedesignBindingError(f"required passed {family} version is unavailable") from exc

    @staticmethod
    def _audit(preserve: list[str]) -> SimilarityAudit:
        preserved = sorted(preserve)
        return {"preserved": preserved, "replaced": sorted(REUSE_DIMENSIONS - set(preserved))}


__all__ = ["FORBIDDEN_ORIGINAL_REUSE", "OriginalityPolicyError", "REQUIRED_REPLACEMENTS", "REUSE_DIMENSIONS", "RedesignBindingError", "SimilarityAudit", "VideoRedesignService"]
