#!/usr/bin/env python3
"""Create or inspect the isolated Stitch Harness image runtime."""

from __future__ import annotations

import os
import subprocess
import sys
import venv
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PINNED_PILLOW = "12.3.0"


def runtime_root() -> Path:
    override = os.environ.get("STITCH_HARNESS_RUNTIME")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "stitch-design" / "harness-runtime"


def runtime_python(root: Path) -> Path:
    return root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def is_ready(root: Path) -> bool:
    executable = runtime_python(root)
    if not executable.is_file():
        return False
    result = subprocess.run(
        [str(executable), "-c", "import PIL; print(PIL.__version__)"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == PINNED_PILLOW


def check(root: Path) -> int:
    if not runtime_python(root).is_file():
        print(f"Harness runtime is not installed at {root}")
        return 1
    if not is_ready(root):
        print(f"Harness runtime does not contain Pillow {PINNED_PILLOW}")
        return 1
    print(f"Harness runtime ready with Pillow {PINNED_PILLOW}")
    return 0


def run(root: Path, arguments: list[str]) -> int:
    """Run the Harness through its isolated Pillow interpreter."""

    if not is_ready(root):
        print(f"Harness runtime is not ready with Pillow {PINNED_PILLOW}", file=sys.stderr)
        return 1
    environment = dict(os.environ)
    environment["STITCH_HARNESS_ISOLATED"] = "1"
    return subprocess.run(
        [str(runtime_python(root)), str(PLUGIN_ROOT / "scripts" / "stitch_harness.py"), *arguments],
        env=environment,
        check=False,
    ).returncode


def install(root: Path) -> int:
    root.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    venv.EnvBuilder(with_pip=True, clear=False).create(root)
    executable = runtime_python(root)
    result = subprocess.run(
        [str(executable), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(PLUGIN_ROOT / "requirements-harness.txt")],
        check=False,
    )
    return result.returncode or check(root)


def main(arguments: list[str]) -> int:
    root = runtime_root()
    if arguments == ["check"]:
        return check(root)
    if arguments == ["install"]:
        return install(root)
    if arguments[:1] == ["run"] and len(arguments) > 1:
        return run(root, arguments[1:])
    print("Usage: setup_harness_runtime.py check | install | run <harness arguments>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
