"""Temporary bootstrap loaded by Blender in managed mode."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


_RUNTIME = None


def _arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--runtime-dir", required=True)
    parser.add_argument("--output-root")
    parser.add_argument("--asset-root", action="append", default=[])
    parser.add_argument("--execution-policy-json")
    return parser.parse_args(argv)


def start(argv=None):
    global _RUNTIME
    import bpy

    values = list(argv) if argv is not None else sys.argv[sys.argv.index("--") + 1 :]
    args = _arguments(values)
    plugin_root = Path(__file__).resolve().parents[1]
    if str(plugin_root) not in sys.path:
        sys.path.insert(0, str(plugin_root))
    from scripts.harness.server import start_harness
    from scripts.harness.execution_policy import ExecutionPolicy

    _RUNTIME = start_harness(
        bpy,
        session_id=args.session_id,
        runtime_dir=Path(args.runtime_dir),
        approved_output_root=Path(args.output_root) if args.output_root else None,
        approved_asset_roots=[Path(value) for value in args.asset_root],
        execution_policy=ExecutionPolicy.from_dict(json.loads(args.execution_policy_json)) if args.execution_policy_json else None,
    )

    def close_runtime(_unused=None):
        global _RUNTIME
        if _RUNTIME is not None:
            _RUNTIME.close()
            _RUNTIME = None

    bpy.app.handlers.quit_pre.append(close_runtime)
    return _RUNTIME


if __name__ == "__main__":
    start()
