"""Durable, allowance-scoped execution of an approved Dreamina video batch."""
from __future__ import annotations

import fcntl
import json
import os
import re
import stat
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from scripts.operation_ledger import OperationLedger
from scripts.json_contracts import canonical_fingerprint, validate_contract
from scripts.video_evaluation_service import REPAIR_BY_GATE
from scripts.video_evaluation_service import MEASURED_GATE_ORDER, SEMANTIC_GATE_ORDER
from scripts.video_evaluation_service import VideoEvaluationService
from scripts.media_adapter import MediaAdapter
from scripts.trusted_media_tools import TrustedMediaToolStore
from scripts.task_service import TaskService
from scripts.video_service import BatchAllowanceCommitError, PostInvokePersistenceError, VideoService


class VideoBatchExecutor:
    """Submit deterministically and resume only through known provider task ids."""
    _locks_guard = threading.Lock()
    _thread_locks: dict[str, threading.RLock] = {}

    @staticmethod
    def _open_private_child(parent_fd: int, name: str, *, create: bool) -> int:
        if not name or name in {".", ".."} or "/" in name:
            raise ValueError("download directory component is unsafe")
        try:
            entry = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            if not create:
                raise
            os.mkdir(name, mode=0o700, dir_fd=parent_fd)
            os.fsync(parent_fd)
            entry = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        descriptor = os.open(name, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
        metadata = os.fstat(descriptor)
        if ((entry.st_dev, entry.st_ino) != (metadata.st_dev, metadata.st_ino)
                or not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o700):
            os.close(descriptor)
            raise ValueError("existing download directory must be user-owned mode 0700")
        return descriptor

    @staticmethod
    def _assert_private_child(parent_fd: int, name: str, descriptor: int) -> None:
        entry = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        metadata = os.fstat(descriptor)
        if ((entry.st_dev, entry.st_ino) != (metadata.st_dev, metadata.st_ino)
                or not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o700):
            raise ValueError("download directory changed during use")

    def __init__(self, *, project_store: Any, allowance: Any, allowance_id: str,
                 video_service: VideoService | None, adapter: Any,
                 download_root: Path | None = None,
                 evaluation_service: VideoEvaluationService | None = None) -> None:
        self._store = project_store
        self._allowance = allowance
        self._allowance_id = allowance_id
        self._adapter = adapter
        if evaluation_service is not None and type(evaluation_service) is not VideoEvaluationService:
            raise TypeError("evaluation_service must be the production VideoEvaluationService")
        self._evaluation_service = evaluation_service or VideoEvaluationService(
            media_adapter=MediaAdapter(TrustedMediaToolStore()))
        project_root = project_store.project_root(self._project_id_from_allowance())
        project_fd = os.open(project_root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0))
        try:
            root_fd = self._open_private_child(project_fd, "video_batch_execution", create=True)
        finally:
            os.close(project_fd)
        self._root = project_root / "video_batch_execution"
        self._ledger = OperationLedger(self._root)
        self._service = video_service or VideoService({"modes": []}, self._root)
        self._tasks = TaskService(adapter)
        default_downloads = self._root / "downloads"
        if download_root is not None and Path(download_root).resolve() != default_downloads.resolve():
            raise ValueError("download_root must remain inside the project-scoped executor root")
        self._downloads = default_downloads
        try:
            self._downloads_fd = self._open_private_child(root_fd, "downloads", create=True)
        except Exception:
            os.close(root_fd)
            raise
        self._root_fd = root_fd

    def close(self) -> None:
        for attribute in ("_downloads_fd", "_root_fd"):
            descriptor = getattr(self, attribute, None)
            if descriptor is not None:
                os.close(descriptor)
                setattr(self, attribute, None)

    def __del__(self) -> None:
        try:
            self.close()
        except OSError:
            pass

    @contextmanager
    def _transaction(self):
        lock_path = self._root / f"{self._allowance_id}.transaction.lock"
        key = str(lock_path.resolve())
        with self._locks_guard:
            thread_lock = self._thread_locks.setdefault(key, threading.RLock())
        with thread_lock:
            descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
            try:
                os.fchmod(descriptor, 0o600)
                fcntl.flock(descriptor, fcntl.LOCK_EX)
                yield
            finally:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
                os.close(descriptor)

    def _project_id_from_allowance(self) -> str:
        return str(self._allowance.get(self._allowance_id)["project_id"])

    def _quote(self, project_id: str, batch_version: str) -> dict[str, Any]:
        allowance = self._allowance.get(self._allowance_id)
        if allowance.get("project_id") != project_id or allowance.get("quote_version") != batch_version:
            raise ValueError("batch identity is outside the activated allowance")
        return self._store.read_version(project_id, "video_batch_quote", batch_version, "video_batch_quote.schema.json")

    @staticmethod
    def _ordered_attempts(quote: dict[str, Any]) -> list[dict[str, Any]]:
        ordered = []
        for shot_index, item in enumerate(quote["items"]):
            for attempt in item["attempts"]:
                ordered.append({"shot_index": shot_index, "shot_id": item["shot_id"], **attempt})
        return sorted(ordered, key=lambda item: (item["shot_index"], item["attempt_number"]))

    def _load(self, project_id: str, batch_version: str) -> dict[str, Any]:
        state = self._ledger.load_batch(project_id=project_id, batch_version=batch_version)
        return state or {"project_id": project_id, "batch_version": batch_version,
                         "allowance_id": self._allowance_id, "state": "ready", "tasks": []}

    def _save(self, state: dict[str, Any]) -> None:
        self._ledger.save_batch(project_id=state["project_id"], batch_version=state["batch_version"], payload=state)

    @staticmethod
    def aggregate_state(tasks: list[dict[str, Any]]) -> tuple[str, str]:
        """Return an order-independent batch state and its required action."""
        states = {str(task.get("state", "manual_review")) for task in tasks}
        states.discard("retry_superseded")
        precedence = (
            ("manual_review", "manual_review", "manual_review"),
            ("failed", "failed", "report_failure"),
            ("rejected", "failed", "report_failure"),
            ("missing_artifact", "missing_artifact", "retry_download"),
            ("awaiting_evaluation", "awaiting_evaluation", "evaluate"),
        )
        for member, aggregate, action in precedence:
            if member in states:
                return aggregate, action
        if states.intersection({"submitting", "queued", "querying", "downloading", "generating"}):
            return "generating", "query"
        if "evaluation_retryable" in states:
            return "evaluation_retryable", "run_next"
        if tasks and states == {"accepted"}:
            return "completed", "none"
        return "ready", "run_next"

    def _apply_aggregate(self, state: dict[str, Any], quote: dict[str, Any]) -> None:
        aggregate, action = self.aggregate_state(state["tasks"])
        if aggregate == "completed":
            required = {(item["shot_id"], 1) for item in quote["items"]}
            observed = {(item["shot_id"], item["attempt"]) for item in state["tasks"]}
            if not required <= observed:
                aggregate, action = "ready", "run_next"
        state["state"] = aggregate
        state["required_action"] = action

    def _persist_aggregate(self, state: dict[str, Any], quote: dict[str, Any]) -> None:
        """Atomically persist one coherent aggregate state/action pair."""
        self._apply_aggregate(state, quote)
        self._save(state)

    def run_next(self, project_id: str, batch_version: str, max_new_submissions: int) -> dict[str, Any]:
        with self._transaction():
            return self._run_next_locked(project_id, batch_version, max_new_submissions)

    def _run_next_locked(self, project_id: str, batch_version: str, max_new_submissions: int) -> dict[str, Any]:
        if isinstance(max_new_submissions, bool) or not isinstance(max_new_submissions, int) or not 1 <= max_new_submissions <= 4:
            raise ValueError("max_new_submissions must be between 1 and 4")
        quote, state = self._quote(project_id, batch_version), self._load(project_id, batch_version)
        if state["tasks"]:
            state = self._reconcile_locked(project_id, batch_version)
        else:
            self._persist_aggregate(state, quote)
        if state["state"] not in {"ready", "generating", "evaluation_retryable"}:
            return {**state, "new_submissions": 0}
        known = {(item["shot_id"], item["attempt"]) for item in state["tasks"]}
        new_count = 0
        for planned in self._ordered_attempts(quote):
            key = (planned["shot_id"], planned["attempt_number"])
            if key in known or new_count >= max_new_submissions: continue
            if planned["attempt_number"] > 1:
                previous = next((item for item in state["tasks"] if item["shot_id"] == planned["shot_id"]
                                 and item["attempt"] == planned["attempt_number"] - 1), None)
                if previous is None or previous["state"] != "evaluation_retryable":
                    continue
                recorded = previous.get("evaluation_decision")
                if not isinstance(recorded, dict) or recorded.get("action") != "retry" \
                        or recorded.get("request_fingerprint") != planned["request_fingerprint"] \
                        or recorded.get("repair_directive") != planned.get("repair_directive"):
                    previous["state"] = "manual_review"
                    previous["error_code"] = "RETRY_DECISION_BINDING_MISMATCH"
                    self._persist_aggregate(state, quote)
                    continue
                previous["state"] = "retry_superseded"
                previous["retry_consumed_by_attempt"] = planned["attempt_number"]
            task = {"shot_index": planned["shot_index"], "shot_id": planned["shot_id"],
                    "attempt": planned["attempt_number"], "request_fingerprint": planned["request_fingerprint"],
                    "state": "submitting", "artifacts": []}
            state["tasks"].append(task); self._persist_aggregate(state, quote)
            try:
                result = self._service.submit_with_batch_allowance(
                    planned["request"], adapter=self._adapter, allowance=self._allowance,
                    allowance_id=self._allowance_id, shot_id=planned["shot_id"],
                    attempt=planned["attempt_number"])
            except Exception as exc:
                error_code = (
                    "POST_INVOKE_PERSISTENCE_ERROR" if isinstance(exc, PostInvokePersistenceError)
                    else "BATCH_ALLOWANCE_COMMIT_ERROR" if isinstance(exc, BatchAllowanceCommitError)
                    else "UNEXPECTED_SUBMISSION_ERROR"
                )
                task.update(state="manual_review", error_code=error_code)
                for field in ("submit_id", "reservation_id", "request_fingerprint", "shot_id", "attempt"):
                    value = getattr(exc, field, None)
                    if value is not None:
                        task[field] = value
                evidence_sha256 = getattr(exc, "evidence_sha256", None)
                evidence_length = getattr(exc, "evidence_length", None)
                if isinstance(evidence_sha256, str) and len(evidence_sha256) == 64 \
                        and all(character in "0123456789abcdef" for character in evidence_sha256):
                    task["evidence_sha256"] = evidence_sha256
                if isinstance(evidence_length, int) and not isinstance(evidence_length, bool) and evidence_length >= 0:
                    task["evidence_length"] = evidence_length
                self._persist_aggregate(state, quote); break
            task.update(state="queued", submit_id=result["submit_id"],
                        reservation_id=result["reservation"]["reservation_id"])
            new_count += 1; self._persist_aggregate(state, quote)
        self._persist_aggregate(state, quote)
        return {**state, "new_submissions": new_count}

    def reconcile(self, project_id: str, batch_version: str) -> dict[str, Any]:
        with self._transaction():
            return self._reconcile_locked(project_id, batch_version)

    def _reconcile_locked(self, project_id: str, batch_version: str) -> dict[str, Any]:
        quote = self._quote(project_id, batch_version)
        state = self._load(project_id, batch_version)
        for task in sorted(state["tasks"], key=lambda item: (item["shot_index"], item["attempt"])):
            if task["state"] == "downloading" and task.get("download_dir"):
                try: recovered = self._tasks.verify_download_dir(task["download_dir"])
                except (OSError, ValueError): recovered = []
                if recovered:
                    task["artifacts"] = recovered; task["state"] = "awaiting_evaluation"
                    self._persist_aggregate(state, quote); continue
            if task["state"] == "submitting" and not task.get("submit_id"):
                allowance = self._allowance.get(self._allowance_id)
                reservation = next((item for item in allowance.get("reservations", [])
                                    if item.get("shot_id") == task["shot_id"] and item.get("attempt") == task["attempt"]), None)
                if reservation is not None:
                    task["reservation_id"] = reservation.get("reservation_id")
                    if reservation.get("submit_id"):
                        task["submit_id"] = reservation["submit_id"]; task["state"] = "queued"
                        self._persist_aggregate(state, quote)
                    else:
                        task["state"] = "manual_review"
                        task["error_code"] = "PREINVOKE_RESERVATION_REQUIRES_OPERATOR_REVIEW"
                        self._persist_aggregate(state, quote); continue
                else:
                    task["state"] = "manual_review"
                    task["error_code"] = "PROCESS_INTERRUPTED_BEFORE_RESERVATION"
                    self._persist_aggregate(state, quote); continue
            if not task.get("submit_id") or task["state"] in {
                "failed", "evaluation_retryable", "retry_superseded",
                "awaiting_evaluation", "accepted", "rejected"
            }: continue
            task["state"] = "querying"; self._persist_aggregate(state, quote)
            try:
                queried = self._tasks.query(task["submit_id"])
            except (OSError, ValueError):
                task["state"] = "manual_review"
                task["error_code"] = "UNKNOWN_EXTERNAL_TASK_STATUS"
                self._persist_aggregate(state, quote)
                continue
            status = str(queried["status"])
            if status in {"fail", "failed"}:
                task["state"] = "failed"; self._persist_aggregate(state, quote); continue
            if status != "success":
                task["state"] = "queued" if status == "querying" else "manual_review"
                self._persist_aggregate(state, quote); continue
            shot_root = self._downloads / task["shot_id"]
            attempt_root = shot_root / f"attempt-{task['attempt']}"
            shot_fd = attempt_fd = target_fd = None
            try:
                self._assert_private_child(self._root_fd, "downloads", self._downloads_fd)
                shot_fd = self._open_private_child(self._downloads_fd, task["shot_id"], create=True)
                attempt_name = f"attempt-{task['attempt']}"
                attempt_fd = self._open_private_child(shot_fd, attempt_name, create=True)
                sequence = len([name for name in os.listdir(attempt_fd) if name.startswith("download-")]) + 1
                target_name = f"download-{sequence:03d}"
                target_fd = self._open_private_child(attempt_fd, target_name, create=True)
                target = attempt_root / target_name
                task["state"] = "downloading"; task["download_dir"] = str(target); self._persist_aggregate(state, quote)
                downloaded = self._tasks.query(task["submit_id"], download_dir=str(target))
                self._assert_private_child(self._root_fd, "downloads", self._downloads_fd)
                self._assert_private_child(self._downloads_fd, task["shot_id"], shot_fd)
                self._assert_private_child(shot_fd, attempt_name, attempt_fd)
                self._assert_private_child(attempt_fd, target_name, target_fd)
            except (OSError, ValueError):
                task["state"] = "manual_review"
                task["error_code"] = "INVALID_DOWNLOADED_ARTIFACT"
                self._persist_aggregate(state, quote)
                continue
            finally:
                for descriptor in (target_fd, attempt_fd, shot_fd):
                    if descriptor is not None:
                        os.close(descriptor)
            task["artifacts"] = downloaded["artifacts"]
            task["state"] = "awaiting_evaluation" if task["artifacts"] else "missing_artifact"
            self._persist_aggregate(state, quote)
        self._persist_aggregate(state, quote)
        return state

    def apply_evaluation_decision(self, receipt: dict[str, Any]) -> dict[str, Any]:
        """Validate and persist one canonical receipt after artifact re-verification."""
        try:
            validate_contract(receipt, "shot_evaluation.schema.json")
        except ValueError as exc:
            raise ValueError("evaluation receipt contract is invalid") from exc
        core = {name: value for name, value in receipt.items() if name != "evaluation_fingerprint"}
        if canonical_fingerprint(core) != receipt["evaluation_fingerprint"]:
            raise ValueError("evaluation receipt fingerprint mismatch")
        binding = receipt["binding"]
        if binding["allowance_id"] != self._allowance_id:
            raise ValueError("evaluation decision binding is incomplete")
        action = receipt["decision"]["action"]
        statuses = {**{name: receipt["measured_gates"][name]["status"] for name in MEASURED_GATE_ORDER},
                    **{name: receipt["semantic_gates"][name]["status"] for name in SEMANTIC_GATE_ORDER}}
        observed_failed = [name for name in (*MEASURED_GATE_ORDER, *SEMANTIC_GATE_ORDER)
                           if statuses[name] in {"failed", "skipped"}]
        if observed_failed != receipt["failed_gates"]:
            raise ValueError("evaluation failed gates are inconsistent")
        if action == "accepted" and observed_failed:
            raise ValueError("evaluation decision is inconsistent with gates")
        if action in {"retry", "rejected"} and not observed_failed:
            raise ValueError("evaluation decision is inconsistent with gates")
        with self._transaction():
            quote = self._quote(binding["project_id"], binding["batch_version"])
            allowance = self._allowance.get(self._allowance_id)
            if (binding.get("design_version"), binding.get("design_fingerprint"), binding.get("quote_fingerprint")) != (
                    quote.get("design_version"), quote.get("design_fingerprint"), quote.get("quote_fingerprint")):
                raise ValueError("evaluation decision quote or design binding is stale")
            allowance_binding = {"project_id": allowance.get("project_id"),
                                 "batch_version": allowance.get("quote_version"),
                                 "design_version": allowance.get("design_version"),
                                 "design_fingerprint": allowance.get("design_fingerprint"),
                                 "quote_fingerprint": allowance.get("quote_fingerprint")}
            if any(allowance_binding.get(name) != binding.get(name) for name in allowance_binding):
                raise ValueError("evaluation decision allowance binding is stale")
            state = self._load(binding["project_id"], binding["batch_version"])
            task = next((item for item in state["tasks"] if item["shot_id"] == binding["shot_id"]
                         and item["attempt"] == binding["attempt"]), None)
            if task is None or task.get("state") != "awaiting_evaluation":
                raise ValueError("evaluation decision requires an artifact awaiting evaluation")
            if binding.get("submit_id") != task.get("submit_id"):
                raise ValueError("evaluation receipt submit id is stale")
            artifact = next((item for item in task.get("artifacts", [])
                             if item.get("sha256") == binding["artifact_sha256"]), None)
            if artifact is None:
                raise ValueError("evaluation artifact digest is stale")
            current = self._tasks.verify_download_dir(str(Path(artifact["path"]).parent))
            if not any(item.get("sha256") == binding["artifact_sha256"]
                       and item.get("path") == artifact.get("path") for item in current):
                raise ValueError("evaluation artifact digest is stale")
            if receipt["artifact_evidence"].get("sha256") != binding["artifact_sha256"] \
                    or any(receipt["artifact_evidence"].get(name) != artifact.get(name)
                           for name in ("path", "mime_type", "size_bytes", "sha256", "provenance")):
                raise ValueError("evaluation artifact evidence is stale")
            planned_current = next((item for item in self._ordered_attempts(quote)
                                    if item["shot_id"] == binding["shot_id"]
                                    and item["attempt_number"] == binding["attempt"]), None)
            if planned_current is None:
                raise ValueError("evaluation shot attempt is outside quote")
            profile = quote.get("output_profile", {})
            design_shot = {**binding, "id": binding["shot_id"], "width": profile.get("width"),
                           "height": profile.get("height"), "codec": profile.get("codec"),
                           "duration_seconds": planned_current["request"].get("duration_seconds"),
                           "aspect_ratio": planned_current["request"].get("ratio")}
            verification_artifact = {**artifact, **binding}
            try:
                self._evaluation_service.verify_receipt(receipt, artifact=verification_artifact,
                    design_shot=design_shot, allowance=allowance, quote=quote)
            except (ValueError, OSError) as exc:
                raise ValueError("evaluation receipt failed trusted recomputation") from exc
            if action == "retry":
                decision = receipt["decision"]
                directives = {REPAIR_BY_GATE.get(name) for name in receipt["failed_gates"]}
                if directives != {decision.get("repair_directive")}:
                    raise ValueError("retry decision does not match failed gates")
                planned = next((item for item in self._ordered_attempts(quote)
                                if item["shot_id"] == binding["shot_id"]
                                and item["attempt_number"] == binding["attempt"] + 1), None)
                if planned is None or decision.get("request_fingerprint") != planned.get("request_fingerprint") \
                        or decision.get("repair_directive") != planned.get("repair_directive"):
                    raise ValueError("retry decision is not the exact next prequoted request")
                requests = allowance.get("requests", [])
                if not any(item.get("shot_id") == binding["shot_id"]
                           and item.get("attempt") == binding["attempt"] + 1
                           and item.get("request_fingerprint") == decision["request_fingerprint"] for item in requests) \
                        or any(item.get("shot_id") == binding["shot_id"]
                               and item.get("attempt") == binding["attempt"] + 1
                               for item in allowance.get("reservations", [])):
                    raise ValueError("retry decision is unavailable in allowance")
            task["evaluation_decision"] = json.loads(json.dumps(receipt["decision"]))
            task["evaluation_receipt"] = json.loads(json.dumps(receipt))
            task["state"] = "evaluation_retryable" if action == "retry" else action
            self._persist_aggregate(state, quote)
            return state

    def resume(self, project_id: str, batch_version: str) -> dict[str, Any]:
        """Reconcile known submit ids; this method never creates a submission."""
        return self.reconcile(project_id, batch_version)


__all__ = ["VideoBatchExecutor"]
