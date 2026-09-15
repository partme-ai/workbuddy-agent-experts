"""Queue command work for execution on Blender's owning thread."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from collections.abc import Callable

from .errors import HarnessError


@dataclass
class _WorkItem:
    callback: Callable[[], object]
    completed: threading.Event = field(default_factory=threading.Event)
    result: object = None
    error: BaseException | None = None
    cancelled: bool = False


class MainThreadExecutor:
    def __init__(self, owner_thread_id: int | None = None):
        self.owner_thread_id = owner_thread_id or threading.get_ident()
        self._queue: queue.Queue[_WorkItem] = queue.Queue()

    def submit(self, callback: Callable[[], object], *, timeout: float = 30.0):
        if threading.get_ident() == self.owner_thread_id:
            return callback()
        item = _WorkItem(callback=callback)
        self._queue.put(item)
        if not item.completed.wait(timeout):
            item.cancelled = True
            raise HarnessError("COMMAND_TIMEOUT", f"main-thread command timed out after {timeout}s", retryable=True)
        if item.error is not None:
            raise item.error
        return item.result

    def pump(self, *, limit: int = 64) -> int:
        if threading.get_ident() != self.owner_thread_id:
            raise HarnessError("MAIN_THREAD_REQUIRED", "command queue must be pumped by Blender's main thread")
        processed = 0
        while processed < limit:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break
            if not item.cancelled:
                try:
                    item.result = item.callback()
                except BaseException as exc:
                    item.error = exc
            item.completed.set()
            processed += 1
        return processed

    def blender_timer_callback(self):
        self.pump(limit=1)
        return 0.02

    @property
    def pending_count(self):
        return self._queue.qsize()

    def cancel_pending(self, code="SESSION_REVOKED"):
        while True:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                return
            item.cancelled = True
            item.error = HarnessError(code, "pending command cancelled at a user-control boundary")
            item.completed.set()
