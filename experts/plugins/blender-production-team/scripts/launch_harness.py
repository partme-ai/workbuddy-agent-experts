#!/usr/bin/env python3
"""Launch a non-invasive Codex Blender managed session."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from scripts.managed_launcher import launch_managed
from scripts.harness.execution_policy import ExecutionMode, ExecutionPolicy


def discover_blender(explicit: str | None) -> Path:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    found = shutil.which("blender")
    if found:
        candidates.append(Path(found))
    if sys.platform == "darwin":
        candidates.append(Path("/Applications/Blender.app/Contents/MacOS/Blender"))
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError("Blender executable not found; pass --blender")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Launch Blender with the temporary Codex Harness")
    parser.add_argument("--blender")
    parser.add_argument("--project")
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--runtime-dir")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--asset-root", action="append", default=[])
    parser.add_argument("--execution-mode", choices=[mode.value for mode in ExecutionMode], default="interactive")
    parser.add_argument("--allow-designed-proxies", action="store_true")
    parser.add_argument("--export-format", action="append", choices=["blend", "glb", "gltf", "fbx", "obj", "stl", "png", "jpg", "mp4"])
    args = parser.parse_args(argv)
    try:
        blender = discover_blender(args.blender)
        project = Path(args.project).resolve() if args.project else None
        if project is not None and (Path(args.project).is_symlink() or not project.is_file()):
            raise ValueError("--project must be an existing non-symlink file")
        output_root = Path(args.output_root).resolve()
        output_root.mkdir(parents=True, exist_ok=True)
        runtime_dir = Path(args.runtime_dir).resolve() if args.runtime_dir else Path(tempfile.gettempdir()) / "codex-blender"
        policy_data = {"mode": args.execution_mode, "approvedOutputRoot": str(output_root),
                       "allowDesignedProxies": args.allow_designed_proxies}
        if args.export_format is not None:
            policy_data["exportFormats"] = args.export_format
        policy = ExecutionPolicy.from_dict(policy_data)
        process, descriptor = launch_managed(
            blender=blender,
            project=project,
            session_id=args.session_id,
            runtime_dir=runtime_dir,
            output_root=output_root,
            asset_roots=[Path(value).resolve() for value in args.asset_root],
            execution_policy=policy,
        )
        public = {key: value for key, value in descriptor.items() if key != "token"}
        public["descriptor"] = str(runtime_dir / f"{args.session_id}.json")
        public["processId"] = process.pid
        print(json.dumps(public))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
