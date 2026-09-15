"""Validate model exports in an isolated Blender subprocess."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .errors import HarnessError


VALIDATION_SCRIPT = Path(__file__).resolve().parents[1] / "validate_model_in_blender.py"


def build_validation_argv(blender: Path, artifact: Path) -> list[str]:
    return [
        str(blender), "--background", "--factory-startup", "--disable-autoexec",
        "--python", str(VALIDATION_SCRIPT), "--", str(artifact),
    ]


def parse_validation_output(stdout: str) -> dict:
    for line in stdout.splitlines():
        if line.startswith("CODEX_REIMPORT="):
            return json.loads(line.split("=", 1)[1])
    raise HarnessError("REIMPORT_FAILED", "isolated Blender emitted no validation summary")


def validate_reimport(blender: Path, artifact: Path, *, runner=subprocess.run, timeout: float = 120.0) -> dict:
    argv = build_validation_argv(blender, artifact)
    process = runner(argv, capture_output=True, text=True, timeout=timeout, check=False, shell=False)
    if process.returncode != 0:
        raise HarnessError("REIMPORT_FAILED", process.stderr.strip() or f"Blender exited {process.returncode}")
    summary = parse_validation_output(process.stdout)
    if int(summary.get("meshes", 0)) <= 0:
        raise HarnessError("REIMPORT_FAILED", "re-imported artifact contains no meshes")
    return {"status": "passed", "checks": ["isolated_reimport", "mesh_present"], "summary": summary}

