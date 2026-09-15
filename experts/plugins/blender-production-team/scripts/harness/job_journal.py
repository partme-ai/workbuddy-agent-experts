"""Durable append-only job journal with atomic writes and crash recovery.

The journal records job lifecycle events to a JSONL file (one JSON object per
line) using append-mode writes with flush and fsync.  The append-only invariant
is that the previous file content is always an exact byte prefix of the new
content after an append.

RecoveryPlan types (only these four are valid):
  - resume_missing_frames:        a RENDER_ANIMATION_FRAMES job was interrupted
                                  and has at least one verified frame on disk.
  - recompose_verified_sequence:  a COMPOSE_VIDEO job was interrupted but its
                                  source frame sequence is complete and verified.
  - resubmit_from_snapshot:       a job was interrupted with no recoverable
                                  progress; re-launch from the saved snapshot.
  - manual_decision_required:     the situation is ambiguous -- e.g. multiple
                                  interrupted jobs with conflicting recovery
                                  needs, or a job kind whose recovery path
                                  cannot be determined automatically.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JOURNAL_FILENAME = "journal.jsonl"
ALLOWED_RECOVERY_PLANS = frozenset({
    "resume_missing_frames",
    "recompose_verified_sequence",
    "resubmit_from_snapshot",
    "manual_decision_required",
})

# Status states that are not terminal and whose process may have died.
_INDETERMINATE_STATES = frozenset({"queued", "running"})


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class JobEvent:
    """One event in the job journal."""
    job_id: str
    type: str
    message: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "jobId": self.job_id,
            "type": self.type,
            "message": self.message,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "JobEvent":
        return cls(
            job_id=data["jobId"],
            type=data["type"],
            message=data.get("message", ""),
            timestamp=data.get("timestamp", 0.0),
        )


@dataclass
class RecoveryPlan:
    """Describes the recovery action for interrupted jobs.

    ``plan`` must be one of ALLOWED_RECOVERY_PLANS.
    ``jobs`` maps jobId -> recovery detail dict.
    """
    plan: str
    jobs: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.plan not in ALLOWED_RECOVERY_PLANS:
            raise ValueError(
                f"invalid recovery plan {self.plan!r}; "
                f"allowed: {sorted(ALLOWED_RECOVERY_PLANS)}"
            )


# ---------------------------------------------------------------------------
# Atomic write helper (for status/spec files, NOT for the journal itself)
# ---------------------------------------------------------------------------

def atomic_write_json(path: Path, payload: Any, *, _fsync=os.fsync) -> None:
    """Write *payload* as JSON to *path* atomically.

    Strategy: same-directory temp file, write, flush, fsync, os.replace.
    The ``_fsync`` parameter is injectable for call-level contract checks.
    """
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    tmp = directory / (path.name + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.flush()
            _fsync(fh.fileno())
        os.replace(str(tmp), str(path))
    except BaseException:
        # Clean up temp file on failure; the target is untouched.
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Journal
# ---------------------------------------------------------------------------

class JobJournal:
    """Append-only job event journal with atomic persistence and crash recovery.

    The journal uses JSONL format (one JSON object per line).  Append opens the
    file in append mode, writes one line, flushes, and fsyncs.  This guarantees
    that previous content is always an exact byte prefix of the new content.

    Parameters
    ----------
    journal_dir : Path
        Directory that holds ``journal.jsonl`` and the per-job status files
        (each in ``<journal_dir>/jobs/<jobId>/status.json``).
    """

    def __init__(self, journal_dir: Path):
        self._dir = Path(journal_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / JOURNAL_FILENAME
        self._jobs_root = self._dir / "jobs"
        # In-memory cache of events for query performance.
        self._events: List[dict] = []
        self._next_revision: int = 1
        # Load existing events from disk (crash recovery).
        if self._path.is_file():
            try:
                with self._path.open("r", encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        record = json.loads(line)
                        if isinstance(record, dict) and "revision" in record:
                            self._events.append(record)
                            self._next_revision = record["revision"] + 1
            except (OSError, json.JSONDecodeError, KeyError):
                # Corrupt journal -- start fresh.
                self._events = []
                self._next_revision = 1

    # -- public API ---------------------------------------------------------

    def append(self, event: JobEvent, *, _fsync=os.fsync) -> int:
        """Append *event* and return its monotonically increasing revision.

        The journal file is opened in append mode.  One JSON line is written,
        followed by a newline, then flush + fsync.  Previous content is always
        an exact byte prefix of the new content (append-only invariant).
        """
        revision = self._next_revision
        record = event.to_dict()
        record["revision"] = revision
        self._events.append(record)
        self._next_revision = revision + 1
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        self._dir.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line)
            fh.flush()
            _fsync(fh.fileno())
        return revision

    def events(self) -> List[dict]:
        """Return all journal events (read-only copy)."""
        return list(self._events)

    def recover(self) -> RecoveryPlan:
        """Scan job status files and classify interrupted jobs.

        A job whose state is ``running`` or ``queued`` and whose PID is no
        longer alive is classified as ``interrupted``.  The status file is
        updated in place (atomic write) and a journal event is appended.

        Returns a RecoveryPlan whose ``plan`` is one of the four allowed
        types.
        """
        if not self._jobs_root.is_dir():
            return RecoveryPlan(plan="resubmit_from_snapshot", jobs={})

        interrupted: List[dict] = []
        for job_dir in sorted(self._jobs_root.iterdir()):
            status_path = job_dir / "status.json"
            if not status_path.is_file():
                continue
            try:
                status = json.loads(status_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            state = status.get("state")
            if state not in _INDETERMINATE_STATES:
                continue
            pid = status.get("pid")
            alive = False
            if type(pid) is int:
                try:
                    os.kill(pid, 0)
                    alive = True
                except OSError:
                    pass
            if not alive:
                # Mark interrupted.
                status["state"] = "interrupted"
                atomic_write_json(status_path, status)
                self.append(JobEvent(
                    job_id=status.get("jobId", job_dir.name),
                    type="interrupted",
                    message="recovery: process dead",
                ))
                interrupted.append(status)

        if not interrupted:
            # Nothing to recover -- pick a safe default.
            return RecoveryPlan(plan="resubmit_from_snapshot", jobs={})

        return self._classify_interrupted(interrupted)

    # -- internal -----------------------------------------------------------

    def _classify_interrupted(self, interrupted: List[dict]) -> RecoveryPlan:
        """Determine the appropriate RecoveryPlan for the given jobs.

        Rules:
        - RENDER_ANIMATION_FRAMES with verified frames on disk -> resume_missing_frames
        - COMPOSE_VIDEO with a complete verified source sequence -> recompose_verified_sequence
        - Any other kind, or no recoverable progress -> resubmit_from_snapshot
        - Multiple interrupted jobs with conflicting needs -> manual_decision_required
        """
        plans: Dict[str, str] = {}   # jobId -> plan
        details: Dict[str, Any] = {}  # jobId -> detail

        for status in interrupted:
            job_id = status.get("jobId", "unknown")
            kind = status.get("kind", "")
            detail: Dict[str, Any] = {"kind": kind, "state": "interrupted"}

            if kind == "RENDER_ANIMATION_FRAMES":
                # Check for verified frames on disk.
                job_dir = self._jobs_root / job_id
                manifest_path = job_dir / "frame-sequence.json"
                has_frames = False
                frame_count = 0
                if manifest_path.is_file():
                    try:
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                        frames = manifest.get("frames", [])
                        frame_count = len(frames)
                        has_frames = frame_count > 0
                    except (OSError, json.JSONDecodeError):
                        has_frames = False
                if has_frames:
                    plans[job_id] = "resume_missing_frames"
                    detail["reason"] = f"{frame_count} frames verified on disk"
                else:
                    plans[job_id] = "resubmit_from_snapshot"
                    detail["reason"] = "no verified frames on disk"

            elif kind == "COMPOSE_VIDEO":
                # Check if source sequence is complete.
                job_dir = self._jobs_root / job_id
                spec_path = job_dir / "spec.json"
                source_complete = False
                if spec_path.is_file():
                    try:
                        spec = json.loads(spec_path.read_text(encoding="utf-8"))
                        source_seq = spec.get("sourceSequence", {})
                        source_job_id = source_seq.get("jobId")
                        if source_job_id:
                            source_dir = self._jobs_root / source_job_id
                            source_manifest = source_dir / "frame-sequence.json"
                            if source_manifest.is_file():
                                sm = json.loads(source_manifest.read_text(encoding="utf-8"))
                                source_complete = sm.get("validation", {}).get("status") == "passed"
                    except (OSError, json.JSONDecodeError):
                        source_complete = False
                if source_complete:
                    plans[job_id] = "recompose_verified_sequence"
                    detail["reason"] = "source sequence verified complete"
                else:
                    plans[job_id] = "resubmit_from_snapshot"
                    detail["reason"] = "source sequence not verified"

            else:
                plans[job_id] = "resubmit_from_snapshot"
                detail["reason"] = f"kind={kind} has no frame-level resume"

            details[job_id] = detail

        # If multiple jobs have different recovery strategies, require
        # manual decision -- the operator must choose which to prioritise.
        unique_plans = set(plans.values())
        if len(unique_plans) > 1:
            return RecoveryPlan(
                plan="manual_decision_required",
                jobs=details,
            )

        # All interrupted jobs agree on a single plan.
        (plan,) = unique_plans
        return RecoveryPlan(plan=plan, jobs=details)
