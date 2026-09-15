"""Job scheduler with capacity limits, FIFO queuing, disk reserve, and log rotation.

Policy items enforced here (per the 1.0 production plan, Task 12):
  1. maximum active jobs = 2
  2. a third job is FIFO queued
  3. priority only reorders the queued order
  4. no preemption of running jobs
  5. disk reserve max(20% of volume capacity, 20 GB)
  6. when over the limit: do not save snapshots, do not start processes
  7. job log 50 MiB x 5 rotations
"""

from __future__ import annotations

import json
import os
import shutil
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Deque, Dict, List, Optional, Tuple

from .errors import HarnessError


# ---------------------------------------------------------------------------
# Constants -- production values.  Tests inject overrides through the
# constructor so these can be mutated to prove the checks fire.
# ---------------------------------------------------------------------------
MAX_ACTIVE_JOBS = 2
DISK_RESERVE_FRACTION = 0.20
DISK_RESERVE_MINIMUM_BYTES = 20 * 1024 * 1024 * 1024  # 20 GB
LOG_MAX_BYTES = 50 * 1024 * 1024  # 50 MiB
LOG_ROTATION_COUNT = 5


@dataclass(order=True)
class _QueueEntry:
    """One entry in the pending-queue.  Lower sort key = earlier service."""
    sort_key: Tuple[int, float]          # (negated_priority, arrival_time)
    job_id: str = field(compare=False)
    kind: str = field(compare=False)
    parameters: dict = field(compare=False, default_factory=dict)
    priority: int = field(compare=False, default=0)
    enqueue_time: float = field(compare=False, default=0.0)
    spec: dict = field(compare=False, default_factory=dict)
    status: dict = field(compare=False, default_factory=dict)
    directory: Path = field(compare=False, default=Path())


def compute_disk_reserve(volume_capacity_bytes: int) -> int:
    """max(20% of volume capacity, 20 GB).  Both branches exercised."""
    return int(max(volume_capacity_bytes * DISK_RESERVE_FRACTION, DISK_RESERVE_MINIMUM_BYTES))


def check_disk_space(output_root: Path, *,
                     reserve_fraction: float = DISK_RESERVE_FRACTION,
                     reserve_minimum: int = DISK_RESERVE_MINIMUM_BYTES) -> Tuple[bool, int, int]:
    """Return (ok, free_bytes, reserve_bytes) for the volume containing *output_root*."""
    usage = shutil.disk_usage(str(output_root))
    reserve = int(max(usage.total * reserve_fraction, reserve_minimum))
    return usage.free >= reserve, usage.free, reserve


def rotate_log(log_path: Path, *,
               max_bytes: int = LOG_MAX_BYTES,
               rotation_count: int = LOG_ROTATION_COUNT) -> None:
    """Rotate *log_path* when it exceeds *max_bytes*.

    Produces up to *rotation_count* numbered backups (log.1 .. log.N).
    """
    if not log_path.exists():
        return
    if log_path.stat().st_size < max_bytes:
        return
    # Shift existing backups
    for i in range(rotation_count - 1, 0, -1):
        src = log_path.with_suffix(f".log.{i}")
        dst = log_path.with_suffix(f".log.{i + 1}")
        if src.exists():
            os.replace(str(src), str(dst))
    # Current becomes .1
    os.replace(str(log_path), str(log_path.with_suffix(".log.1")))
    # Truncate (create empty) the current log
    log_path.write_bytes(b"")


def rotate_log_path(directory: Path, *,
                    max_bytes: int = LOG_MAX_BYTES,
                    rotation_count: int = LOG_ROTATION_COUNT) -> None:
    """Convenience wrapper that rotates ``worker.log`` inside *directory*."""
    rotate_log(directory / "worker.log", max_bytes=max_bytes, rotation_count=rotation_count)


class Scheduler:
    """Controls job dispatch with a configurable concurrency cap.

    The scheduler is the single point of enforcement for policies 1-6.
    Policy 7 (log rotation) is a standalone helper called by ``JobManager``
    after each job completes.
    """

    def __init__(self, *,
                 max_active: int = MAX_ACTIVE_JOBS,
                 disk_reserve_fraction: float = DISK_RESERVE_FRACTION,
                 disk_reserve_minimum: int = DISK_RESERVE_MINIMUM_BYTES,
                 log_max_bytes: int = LOG_MAX_BYTES,
                 log_rotation_count: int = LOG_ROTATION_COUNT,
                 process_factory: Callable = None,
                 time_source: Callable[[], float] = None):
        self.max_active = max_active
        self.disk_reserve_fraction = disk_reserve_fraction
        self.disk_reserve_minimum = disk_reserve_minimum
        self.log_max_bytes = log_max_bytes
        self.log_rotation_count = log_rotation_count
        self._process_factory = process_factory
        self._time = time_source or time.time

        # State
        self._active: Dict[str, dict] = {}          # job_id -> launch_info
        self._queue: Deque[_QueueEntry] = deque()    # ordered by sort_key

    # -- public queries -------------------------------------------------------

    @property
    def active_count(self) -> int:
        return len(self._active)

    @property
    def queued_ids(self) -> List[str]:
        """Job IDs in queue order (head = next to launch)."""
        return [e.job_id for e in self._queue]

    @property
    def active_ids(self) -> List[str]:
        return list(self._active)

    def is_active(self, job_id: str) -> bool:
        return job_id in self._active

    def is_queued(self, job_id: str) -> bool:
        return any(e.job_id == job_id for e in self._queue)

    # -- enqueue / dequeue ----------------------------------------------------

    def enqueue(self, entry: _QueueEntry) -> None:
        """Add a job to the pending queue, preserving priority order."""
        entry.enqueue_time = self._time()
        entry.sort_key = (-entry.priority, entry.enqueue_time)
        # Insert in sorted position (bisect-like on deque -- simple linear for
        # the tiny queue sizes expected).
        inserted = False
        for i, existing in enumerate(self._queue):
            if entry < existing:
                self._queue.insert(i, entry)
                inserted = True
                break
        if not inserted:
            self._queue.append(entry)

    def promote_queued(self, job_id: str, new_priority: int) -> bool:
        """Re-insert a queued job with a higher priority.  Returns True if found.

        A running job is NOT affected (policy 4).
        """
        for i, entry in enumerate(self._queue):
            if entry.job_id == job_id:
                removed = entry
                del self._queue[i]
                removed.priority = new_priority
                self.enqueue(removed)
                return True
        return False

    def remove_queued(self, job_id: str) -> bool:
        for i, entry in enumerate(self._queue):
            if entry.job_id == job_id:
                del self._queue[i]
                return True
        return False

    # -- dispatch -------------------------------------------------------------

    def try_dispatch(self, output_root: Path, *,
                     launch_fn: Callable[[_QueueEntry], dict]) -> List[dict]:
        """Attempt to launch queued jobs as capacity allows.

        Returns list of launched status dicts.  Policy 5/6 checked here.
        """
        launched = []
        while self._queue and self.active_count < self.max_active:
            # Policy 5/6: disk reserve check before launching
            ok, free, reserve = check_disk_space(
                output_root,
                reserve_fraction=self.disk_reserve_fraction,
                reserve_minimum=self.disk_reserve_minimum,
            )
            if not ok:
                # Policy 6: do not start processes when over disk limit
                break
            entry = self._queue[0]
            # Policy 7: rotate log before launching
            if entry.directory:
                rotate_log_path(entry.directory,
                                max_bytes=self.log_max_bytes,
                                rotation_count=self.log_rotation_count)
            result = launch_fn(entry)
            self._active[entry.job_id] = {
                "entry": entry,
                "launched_at": self._time(),
            }
            self._queue.popleft()
            launched.append(result)
        return launched

    def mark_complete(self, job_id: str) -> None:
        """Remove a job from the active set (it finished or was cancelled)."""
        self._active.pop(job_id, None)

    # -- snapshot guard (policy 6) --------------------------------------------

    def can_save_snapshot(self, output_root: Path) -> bool:
        """Return True only if disk reserve allows snapshot writes."""
        ok, _, _ = check_disk_space(
            output_root,
            reserve_fraction=self.disk_reserve_fraction,
            reserve_minimum=self.disk_reserve_minimum,
        )
        return ok

    # -- re-prioritize a running job (should be a no-op) ----------------------

    def set_running_priority(self, job_id: str, new_priority: int) -> bool:
        """Attempt to change priority of a running job.

        Returns True if the job was found in the active set.  The priority
        change has NO effect on execution (policy 4 -- no preemption).
        """
        if job_id in self._active:
            # Policy 4: no preemption -- priority of a running job is ignored.
            # We record it for audit only.
            self._active[job_id]["priority_override"] = new_priority
            return True
        return False

    # -- queue manipulation for testing ----------------------------------------

    def drain_queue(self) -> List[_QueueEntry]:
        """Return and clear all queued entries (for test inspection)."""
        entries = list(self._queue)
        self._queue.clear()
        return entries

    def clear_active(self) -> None:
        self._active.clear()

    def _raw_queue_list(self) -> List[_QueueEntry]:
        """Snapshot of the queue for mutation testing."""
        return list(self._queue)

    def _set_queue(self, entries: List[_QueueEntry]) -> None:
        """Replace the internal queue (for LIFO mutation tests)."""
        self._queue = deque(entries)
