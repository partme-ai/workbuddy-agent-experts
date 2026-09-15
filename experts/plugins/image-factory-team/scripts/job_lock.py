"""Cross-platform advisory process locking for one Image Factory job."""

from __future__ import annotations

import errno
import os
import time
from pathlib import Path
from typing import BinaryIO


class JobAlreadyRunningError(RuntimeError):
    """Raised when another process currently owns the job lock."""


def lock_path_for(job_path: Path) -> Path:
    """Return the stable sidecar path used to serialize a job."""
    return Path(f"{Path(job_path)}.lock")


class JobLock:
    """Own an exclusive advisory lock for the lifetime of a context manager."""

    def __init__(self, job_path: Path, timeout_seconds: float = 0.0) -> None:
        if timeout_seconds < 0:
            raise ValueError("timeout_seconds must be non-negative")
        self.lock_path = lock_path_for(job_path)
        self.timeout_seconds = timeout_seconds
        self._handle: BinaryIO | None = None

    def __enter__(self) -> JobLock:
        handle = self.lock_path.open("a+b")
        self._handle = handle
        try:
            self._ensure_lock_byte(handle)
            self._acquire(handle)
        except BaseException:
            handle.close()
            self._handle = None
            raise
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback) -> None:
        handle = self._handle
        self._handle = None
        if handle is None:
            return
        try:
            self._unlock(handle)
        finally:
            handle.close()

    @staticmethod
    def _ensure_lock_byte(handle: BinaryIO) -> None:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)

    def _acquire(self, handle: BinaryIO) -> None:
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            try:
                self._try_lock(handle)
                return
            except OSError as error:
                if not self._is_contention(error):
                    raise
                if self.timeout_seconds == 0.0 or time.monotonic() >= deadline:
                    raise JobAlreadyRunningError(
                        f"job already running (lock: {self.lock_path})"
                    ) from error
                time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))

    @staticmethod
    def _try_lock(handle: BinaryIO) -> None:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            return

        import fcntl

        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)

    @staticmethod
    def _unlock(handle: BinaryIO) -> None:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            return

        import fcntl

        fcntl.flock(handle, fcntl.LOCK_UN)

    @staticmethod
    def _is_contention(error: OSError) -> bool:
        return error.errno in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}
