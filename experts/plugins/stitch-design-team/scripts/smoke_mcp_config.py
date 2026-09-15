#!/usr/bin/env python3
"""Execute the configured MCP command and verify its Python runtime."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def configured_server() -> tuple[str, list[str], Path]:
    payload = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    server = payload["mcpServers"]["stitch"]
    command = server.get("command")
    arguments = server.get("args")
    relative_cwd = server.get("cwd")
    if not isinstance(command, str) or not command:
        raise ValueError("configured MCP command is invalid")
    if not isinstance(arguments, list) or not all(isinstance(item, str) for item in arguments):
        raise ValueError("configured MCP arguments are invalid")
    if not isinstance(relative_cwd, str) or not relative_cwd:
        raise ValueError("configured MCP cwd is invalid")
    cwd = (ROOT / relative_cwd).resolve()
    try:
        cwd.relative_to(ROOT)
    except ValueError as error:
        raise ValueError("configured MCP cwd escapes the plugin root") from error
    return command, arguments, cwd


def run(expected_python: str) -> None:
    command, arguments, cwd = configured_server()
    version = subprocess.run(
        [command, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if version.returncode != 0:
        raise RuntimeError("configured MCP Python command could not report its version")
    actual_python = version.stdout.strip()
    if actual_python != expected_python:
        raise RuntimeError(
            f"configured MCP command resolved Python {actual_python}, expected {expected_python}"
        )

    smoke = subprocess.run(
        [command, *arguments],
        cwd=cwd,
        input="{invalid-json\n",
        capture_output=True,
        text=True,
        check=False,
    )
    if smoke.returncode != 0 or '"code":-32700' not in smoke.stdout:
        raise RuntimeError("configured MCP proxy smoke failed")
    print(f"configured Python {actual_python}; proxy smoke passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-python", required=True)
    arguments = parser.parse_args()
    try:
        run(arguments.expected_python)
    except (OSError, KeyError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
