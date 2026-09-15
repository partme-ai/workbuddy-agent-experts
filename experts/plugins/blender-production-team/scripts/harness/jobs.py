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


class JobManager:
    SUPPORTED_KINDS = {
        "EXPORT", "RENDER_STILL", "BAKE_POINT_CACHES",
        "RENDER_ANIMATION_FRAMES", "COMPOSE_VIDEO",
    }

    def __init__(self, bpy_module, output_root=None, process_factory=subprocess.Popen):
        self.bpy = bpy_module
        self.root = Path(output_root).resolve() / "jobs" if output_root else None
        self.processes = {}
        self.process_factory = process_factory
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

    def _dir(self, job_id):
        self._available()
        job_id = self._id(job_id)
        directory = (self.root / job_id).resolve()
        if not directory.is_relative_to(self.root):
            raise HarnessError("OUTPUT_NOT_AUTHORIZED", "job path escaped output root")
        return directory

    @staticmethod
    def _write(path, payload, exclusive=False):
        with path.open("x" if exclusive else "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)

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
        current = json.loads((directory / "status.json").read_text(encoding="utf-8"))
        if current.get("state") == "queued":
            status["pid"] = process.pid
            status["state"] = "running"
            self._write(directory / "status.json", status)
            current = status
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
            return {"changedObjects": [], "result": self._launch(directory, spec, initial)}
        except Exception as exc:
            self._write(directory / "status.json", {"receiptVersion": "3.0.0", "jobId": job_id,
                        "kind": kind, "state": "failed", "error": {"message": str(exc)[:500]}})
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
