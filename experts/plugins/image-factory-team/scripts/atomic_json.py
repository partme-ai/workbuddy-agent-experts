#!/usr/bin/env python3
"""Crash-safe JSON persistence shared by durable image-factory records."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def _fsync_directory(directory: Path) -> None:
    """Best-effort directory sync for platforms that expose directory handles."""
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(directory, flags)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def write_json_atomic(path: Path, payload: object) -> None:
    """Serialize one JSON document and atomically replace its destination."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=str(target.parent), prefix=".atomic-", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        _fsync_directory(target.parent)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
