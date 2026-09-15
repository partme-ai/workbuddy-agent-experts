"""Snapshot-isolated Blender subprocess jobs with explicit recovery and resume."""

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from uuid import uuid4

from .errors import HarnessError
from .frame_pipeline import inspect_frame_sequence, validate_compose_parameters, validate_render_parameters
from .job_journal import JobEvent, JobJournal, RecoveryPlan
from .resource_estimator import estimate as _resource_estimate
from .scheduler import (
    Scheduler,
    check_disk_space,
    rotate_log_path,
    _QueueEntry,
)


class JobManager:
    SUPPORTED_KINDS = {
        "EXPORT", "RENDER_STILL", "BAKE_POINT_CACHES",
        "RENDER_ANIMATION_FRAMES", "COMPOSE_VIDEO",
    }

    def __init__(self, bpy_module, output_root=None, process_factory=subprocess.Popen, scheduler=None,
                 journal=None):
        self.bpy = bpy_module
        self.root = Path(output_root).resolve() / "jobs" if output_root else None
        self.processes = {}
        self.process_factory = process_factory
        # Default scheduler: no disk reserve (backward-compatible).
        # Production code passes an explicit Scheduler with the full policy.
        self.scheduler = scheduler or Scheduler(
            process_factory=process_factory,
            disk_reserve_fraction=0.0,
            disk_reserve_minimum=0,
        )
        # Event log: list of dicts with sequential revision numbers
        self._events: list[dict] = []
        self._next_revision: int = 1
        # Durable journal (optional; None = in-memory only, for tests).
        self._journal: JobJournal | None = journal
        if self.root:
            self.root.mkdir(parents=True, exist_ok=True)

    def _available(self):
        if self.root is None:
            raise HarnessError("OUTPUT_NOT_AUTHORIZED", "background jobs require an approved output root")

    def _id(self, value):
        value = value or "job_" + uuid4().hex
        if not isinstance(value, str) or re.fullmatch(r"job_[A-Za-z0-9_-]{1,80}", value) is None:
            raise HarnessError("INVALID_ARGUMENT", "jobId must start with job_")
        return value

    def _record_event(self, job_id: str, event_type: str, message: str = "") -> dict:
        """Append an event with a monotonically increasing revision number."""
        event = {
            "revision": self._next_revision,
            "jobId": job_id,
            "type": event_type,
            "message": message,
        }
        self._events.append(event)
        self._next_revision += 1
        # Also persist to the durable journal if configured.
        if self._journal is not None:
            self._journal.append(JobEvent(
                job_id=job_id, type=event_type, message=message,
            ))
        return event

    # ------------------------------------------------------------------
    # New commands: estimate, list, events
    # ------------------------------------------------------------------

    def estimate(self, arguments):
        """Resource estimate for a hypothetical job.  Pure computation, no I/O."""
        kind = str(arguments.get("kind", "")).upper()
        parameters = arguments.get("parameters", {})
        receipt = _resource_estimate(kind, parameters)
        return {"changedObjects": [], "result": receipt}

    def list(self, arguments):
        """List jobs filtered by state with pagination.

        Arguments: state? (str), offset? (int >= 0), limit? (int 1..100)
        """
        self._available()
        state_filter = arguments.get("state")
        offset = int(arguments.get("offset", 0))
        limit = int(arguments.get("limit", 50))
        if offset < 0:
            raise HarnessError("INVALID_ARGUMENT", "offset must be >= 0")
        if not (1 <= limit <= 100):
            raise HarnessError("INVALID_ARGUMENT", "limit must be 1..100")
        valid_states = {"queued", "running", "completed", "failed", "cancelled", "interrupted"}
        if state_filter is not None:
            if state_filter not in valid_states:
                raise HarnessError("INVALID_ARGUMENT", f"unknown state: {state_filter}")

        # Collect all jobs from disk
        entries = []
        for job_dir in sorted(self.root.iterdir()):
            status_path = job_dir / "status.json"
            if not status_path.is_file():
                continue
            try:
                status = json.loads(status_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            state = status.get("state")
            if state_filter is not None and state != state_filter:
                continue
            entries.append(status)

        total = len(entries)
        page = entries[offset:offset + limit]
        next_offset = offset + limit if offset + limit < total else None
        return {
            "changedObjects": [],
            "result": {"items": page, "total": total, "nextOffset": next_offset},
        }

    def events(self, arguments):
        """Return recorded job events, optionally filtered by afterRevision.

        Arguments: jobId? (str), afterRevision? (int >= 1)
        """
        job_id = arguments.get("jobId")
        after_rev = arguments.get("afterRevision")
        if after_rev is not None:
            after_rev = int(after_rev)
            if after_rev < 0:
                raise HarnessError("INVALID_ARGUMENT", "afterRevision must be >= 0")

        filtered = self._events
        if job_id is not None:
            filtered = [e for e in filtered if e["jobId"] == job_id]
        if after_rev is not None:
            filtered = [e for e in filtered if e["revision"] > after_rev]

        return {"changedObjects": [], "result": {"events": list(filtered)}}

    def _dir(self, job_id):
        self._available()
        job_id = self._id(job_id)
        directory = (self.root / job_id).resolve()
        if not directory.is_relative_to(self.root):
            raise HarnessError("OUTPUT_NOT_AUTHORIZED", "job path escaped output root")
        return directory

    @staticmethod
    def _write(path, payload, exclusive=False):
        if exclusive and path.exists():
            raise FileExistsError(f"file already exists: {path}")
        directory = path.parent
        tmp = directory / (path.name + ".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(str(tmp), str(path))
        except BaseException:
            try:
                tmp.unlink()
            except OSError:
                pass
            raise

    def _launch(self, directory, spec, status):
        spec_path = directory / "spec.json"
        log = (directory / "worker.log").open("a", encoding="utf-8")
        command = [self.bpy.app.binary_path, "--background", str(spec["snapshot"]["path"]),
                   "--python", str(Path(__file__).with_name("job_worker.py")), "--", str(spec_path)]
        try:
            process = self.process_factory(command, cwd=str(directory), stdout=log,
                                           stderr=subprocess.STDOUT, start_new_session=True)
        finally:
            log.close()
        self.processes[spec["jobId"]] = process
        self.scheduler._active[spec["jobId"]] = {"entry": None, "launched_at": 0}
        current = json.loads((directory / "status.json").read_text(encoding="utf-8"))
        if current.get("state") == "queued":
            status["pid"] = process.pid
            status["state"] = "running"
            self._write(directory / "status.json", status)
            current = status
        self._record_event(spec["jobId"], "launched", f"pid={process.pid}")
        return current

    def _validate_request(self, kind, fmt, parameters):
        if kind not in self.SUPPORTED_KINDS:
            raise HarnessError("INVALID_ARGUMENT", "unsupported job kind")
        if kind == "EXPORT" and fmt not in {"blend", "glb", "gltf", "fbx", "obj"}:
            raise HarnessError("INVALID_ARGUMENT", "unsupported background export format")
        if not isinstance(parameters, dict):
            raise HarnessError("INVALID_ARGUMENT", "parameters must be an object")
        if kind == "RENDER_ANIMATION_FRAMES":
            return validate_render_parameters(parameters), None
        if kind == "COMPOSE_VIDEO":
            normalized = validate_compose_parameters(parameters)
            source_dir = self._dir(normalized["sourceJobId"])
            manifest_path = source_dir / "frame-sequence.json"
            if not manifest_path.is_file():
                raise HarnessError("FRAME_SEQUENCE_NOT_FOUND", "source frame sequence manifest was not found")
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise HarnessError("ARTIFACT_INVALID", "source frame sequence manifest is invalid") from exc
            inspection = inspect_frame_sequence(manifest, source_dir)
            if not inspection["ready"]:
                raise HarnessError("FRAME_SEQUENCE_INCOMPLETE", "source sequence has missing or corrupt frames")
            source = {"jobId": normalized["sourceJobId"], "manifestPath": str(manifest_path),
                      "manifestSha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest()}
            return normalized, source
        allowed = {"frame", "width", "height"} if kind == "RENDER_STILL" else set()
        if set(parameters) - allowed:
            raise HarnessError("INVALID_ARGUMENT", "job parameters contain unsupported fields")
        if kind == "RENDER_STILL":
            for key in ("width", "height"):
                value = parameters.get(key, 512)
                if type(value) is not int or not 1 <= value <= 16384:
                    raise HarnessError("INVALID_ARGUMENT", f"{key} must be 1..16384")
            if "frame" in parameters and type(parameters["frame"]) is not int:
                raise HarnessError("INVALID_ARGUMENT", "frame must be integer")
        return dict(parameters), None

    def submit(self, arguments):
        self._available()
        # Policy 5/6: check disk reserve before saving snapshot
        ok, free_bytes, reserve_bytes = check_disk_space(
            self.root.parent,  # volume containing the output root
            reserve_fraction=self.scheduler.disk_reserve_fraction,
            reserve_minimum=self.scheduler.disk_reserve_minimum,
        )
        if not ok:
            raise HarnessError(
                "DISK_RESERVE_EXCEEDED",
                f"free {free_bytes} < reserve {reserve_bytes}; "
                "cannot save snapshot or start process",
            )
        kind = str(arguments.get("kind", "")).upper()
        fmt = str(arguments.get("format", "")).lower()
        parameters, source = self._validate_request(kind, fmt, arguments.get("parameters", {}))
        job_id = self._id(arguments.get("jobId"))
        directory = self._dir(job_id)
        try:
            directory.mkdir()
        except FileExistsError as exc:
            raise HarnessError("JOB_EXISTS", f"job already exists: {job_id}") from exc
        snapshot = directory / "source.blend"
        try:
            result = self.bpy.ops.wm.save_as_mainfile(filepath=str(snapshot), copy=True)
            if result != {"FINISHED"}:
                raise RuntimeError("snapshot did not finish")
            snap = {"path": str(snapshot), "sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
                    "sceneFile": getattr(self.bpy.data, "filepath", "")}
            spec = {"jobId": job_id, "kind": kind, "format": fmt, "parameters": parameters, "snapshot": snap}
            if source is not None:
                spec["sourceSequence"] = source
            self._write(directory / "spec.json", spec, exclusive=True)
            version = "3.0.0" if kind in {"RENDER_ANIMATION_FRAMES", "COMPOSE_VIDEO"} else "2.0.0"
            initial = {"receiptVersion": version, "jobId": job_id, "kind": kind, "state": "queued",
                       "attempt": 1, "snapshot": snap}
            self._write(directory / "status.json", initial, exclusive=True)
            self._record_event(job_id, "submitted", f"kind={kind}")
            # Policy 1/2: enqueue and dispatch through the scheduler
            priority = int(arguments.get("priority", 0))
            entry = _QueueEntry(
                sort_key=(-priority, 0.0),
                job_id=job_id,
                kind=kind,
                parameters=parameters,
                priority=priority,
                spec=spec,
                status=initial,
                directory=directory,
            )
            self.scheduler.enqueue(entry)
            launched = self.scheduler.try_dispatch(
                self.root.parent,
                launch_fn=lambda e: self._launch(e.directory, e.spec, e.status),
            )
            if launched:
                return {"changedObjects": [], "result": launched[0]}
            # Job is queued, not yet launched
            return {"changedObjects": [], "result": initial}
        except Exception as exc:
            self._write(directory / "status.json", {"receiptVersion": "3.0.0", "jobId": job_id,
                        "kind": kind, "state": "failed", "error": {"message": str(exc)[:500]}})
            self._record_event(job_id, "failed", str(exc)[:200])
            if isinstance(exc, HarnessError):
                raise
            raise HarnessError("JOB_SUBMIT_FAILED", "could not snapshot or start Blender child") from exc

    def status(self, arguments):
        job_id = self._id(arguments.get("jobId"))
        directory = self._dir(job_id)
        path = directory / "status.json"
        if not path.is_file():
            raise HarnessError("JOB_NOT_FOUND", f"job not found: {job_id}")
        result = json.loads(path.read_text(encoding="utf-8"))
        process = self.processes.get(job_id)
        if process and process.poll() is not None and result.get("state") in {"queued", "running"}:
            result["state"] = "failed"
            result["error"] = {"message": f"worker exited {process.returncode} without a terminal receipt"}
            self._write(path, result)
            self._record_event(job_id, "failed", f"exit {process.returncode}")
            self.scheduler.mark_complete(job_id)
        return {"changedObjects": [], "result": result}

    def cancel(self, arguments):
        status = self.status(arguments)["result"]
        job_id = status["jobId"]
        if status["state"] in {"completed", "failed", "cancelled", "interrupted"}:
            return {"changedObjects": [], "result": status}
        process = self.processes.get(job_id)
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        status["state"] = "cancelled"
        status["cancelRequested"] = True
        self._write(self._dir(job_id) / "status.json", status)
        self._record_event(job_id, "cancelled")
        self.scheduler.mark_complete(job_id)
        self.scheduler.remove_queued(job_id)
        return {"changedObjects": [], "result": status}

    def recover(self, arguments):
        status = self.status(arguments)["result"]
        if status["state"] not in {"queued", "running"}:
            return {"changedObjects": [], "result": status}
        pid = status.get("pid")
        alive = False
        if type(pid) is int:
            try:
                os.kill(pid, 0)
                alive = True
            except OSError:
                pass
        if not alive:
            status["state"] = "interrupted"
            status["recovery"] = "not-restarted"
            self._write(self._dir(status["jobId"]) / "status.json", status)
            self._record_event(status["jobId"], "interrupted", "recovery: not-restarted")
            self.scheduler.mark_complete(status["jobId"])
        return {"changedObjects": [], "result": status}

    def resume(self, arguments):
        status = self.status(arguments)["result"]
        if status.get("kind") != "RENDER_ANIMATION_FRAMES":
            raise HarnessError("JOB_NOT_RESUMABLE", "only frame-sequence jobs can resume")
        if status.get("state") not in {"interrupted", "failed", "cancelled"}:
            raise HarnessError("JOB_NOT_RESUMABLE", "job must be interrupted, failed or cancelled")
        directory = self._dir(status["jobId"])
        try:
            spec = json.loads((directory / "spec.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HarnessError("JOB_NOT_RESUMABLE", "job specification is missing or invalid") from exc
        snapshot = Path(spec["snapshot"]["path"])
        if not snapshot.is_file() or hashlib.sha256(snapshot.read_bytes()).hexdigest() != spec["snapshot"]["sha256"]:
            raise HarnessError("JOB_NOT_RESUMABLE", "job snapshot is missing or changed")
        resumed = {"receiptVersion": "3.0.0", "jobId": status["jobId"], "kind": status["kind"],
                   "state": "queued", "attempt": int(status.get("attempt", 1)) + 1,
                   "snapshot": spec["snapshot"], "resume": "missing-or-corrupt-frames-only"}
        self._write(directory / "status.json", resumed)
        return {"changedObjects": [], "result": self._launch(directory, spec, resumed)}
