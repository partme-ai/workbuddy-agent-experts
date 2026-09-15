#!/usr/bin/env python3
"""Launch the Stitch Delivery Harness CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from stitch_harness.cli import main  # noqa: E402


if __name__ == "__main__":
    if sys.argv[1:2] == ["compare"] and os.environ.get("STITCH_HARNESS_ISOLATED") != "1":
        from setup_harness_runtime import is_ready, runtime_python, runtime_root

        root = runtime_root()
        executable = runtime_python(root)
        if not is_ready(root):
            print("Harness Pillow runtime is missing or stale; run setup_harness_runtime.py install", file=sys.stderr)
            raise SystemExit(2)
        environment = dict(os.environ)
        environment["STITCH_HARNESS_ISOLATED"] = "1"
        raise SystemExit(subprocess.run([str(executable), str(Path(__file__).resolve()), *sys.argv[1:]], env=environment, check=False).returncode)
    raise SystemExit(main())
