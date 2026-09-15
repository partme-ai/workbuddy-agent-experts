"""Non-invasive Blender launcher and session descriptor reader."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path


BOOTSTRAP = Path(__file__).with_name("managed_bootstrap.py")


def build_managed_argv(*, blender: Path, project: Path | None, session_id: str, runtime_dir: Path, output_root: Path | None = None, asset_roots=(), execution_policy=None) -> list[str]:
    argv = [str(blender), "--disable-autoexec"]
    if project is not None:
        argv.append(str(project))
    argv.extend(
        [
            "--python",
            str(BOOTSTRAP),
            "--",
            "--session-id",
            session_id,
            "--runtime-dir",
            str(runtime_dir),
        ]
    )
    if output_root is not None:
        argv.extend(["--output-root", str(output_root)])
    for asset_root in asset_roots:
        argv.extend(["--asset-root", str(asset_root)])
    if execution_policy is not None:
        argv.extend(["--execution-policy-json", json.dumps(execution_policy.to_audit_dict())])
    return argv


def load_descriptor(path: Path) -> dict:
    path = Path(path)
    if os.name != "nt" and path.stat().st_mode & 0o077:
        raise PermissionError(f"session descriptor permissions are not private: {path}")
    return json.loads(path.read_text())


def remove_stale_descriptor(path: Path) -> bool:
    path = Path(path)
    if not path.exists():
        return False
    descriptor = load_descriptor(path)
    pid = int(descriptor.get("pid", 0))
    alive = False
    if pid > 0:
        try:
            os.kill(pid, 0)
            alive = True
        except OSError:
            pass
    if alive:
        return False
    if descriptor.get("transport") == "unix" and descriptor.get("address"):
        try:
            Path(descriptor["address"]).unlink()
        except FileNotFoundError:
            pass
    path.unlink()
    return True


def launch_managed(*, blender: Path, project: Path | None, session_id: str, runtime_dir: Path, output_root: Path | None = None, asset_roots=(), timeout: float = 30.0, execution_policy=None):
    runtime_dir = Path(runtime_dir)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    descriptor = runtime_dir / f"{session_id}.json"
    if descriptor.exists():
        if not remove_stale_descriptor(descriptor):
            raise FileExistsError(f"session already exists: {session_id}")
    process = subprocess.Popen(
        build_managed_argv(blender=blender, project=project, session_id=session_id, runtime_dir=runtime_dir, output_root=output_root, asset_roots=asset_roots, execution_policy=execution_policy),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if descriptor.exists():
            return process, load_descriptor(descriptor)
        if process.poll() is not None:
            raise RuntimeError(f"Blender exited before Harness startup: {process.returncode}")
        time.sleep(0.05)
    process.terminate()
    raise TimeoutError(f"Harness did not start within {timeout}s")
