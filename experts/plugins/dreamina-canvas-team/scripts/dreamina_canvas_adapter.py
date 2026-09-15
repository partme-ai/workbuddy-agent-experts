"""Strict argv-only dreamina-canvas CLI adapter.

Always:
- Passes argv as a list (no shell).
- Forces --format json.
- Caps stdout / stderr to a configurable byte limit.
- Parses a single error JSON object from stderr on non-zero exit.
- Preserves the original numeric exit code.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandResult:
    exit_code: int
    payload: dict | None
    error: dict | None
    required_action: str
    partial_data: dict | None


# Stable requiredAction values used by both the CLI and the routed error map.
REQUIRED_ACTIONS = {
    "none",
    "login",
    "confirm",
    "retry",
    "resume",
    "upgrade",
    "human_intervention",
    "contact_support",
}


def build_argv(argv: list[str], *, profile: str | None = None) -> list[str]:
    """Prepend the binary and the global --format json flag if missing.

    The binary name is always inserted; the adapter does not resolve the
    installed path on the caller's behalf — pass it explicitly.

    Global flag order: --format json, --profile.
    """
    final = list(argv)
    if "--format" not in final and not any(a.startswith("--format=") for a in final):
        final = ["--format", "json", *final]
    if profile and "--profile" not in final:
        # Place profile after the format flag, before the subcommand.
        idx = 2 if final[:2] == ["--format", "json"] else 0
        final = [*final[:idx], "--profile", profile, *final[idx:]]
    return final


def run_dreamina_canvas(
    argv: list[str],
    *,
    binary: str | Path = "dreamina-canvas",
    timeout_seconds: int = 30,
    profile: str | None = None,
    output_limit_bytes: int = 16 * 1024 * 1024,
) -> CommandResult:
    """Invoke the CLI in --format json mode and parse its envelopes."""
    full_argv = [str(binary), *build_argv(argv, profile=profile)]
    try:
        proc = subprocess.run(
            full_argv,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError:
        # The CLI binary is not installed. Map to exit code 2 and a
        # stable error envelope so the router can take over.
        return CommandResult(
            exit_code=2,
            payload=None,
            error={"code": "cli.binary_not_found", "message": f"{binary} not in PATH"},
            required_action="human_intervention",
            partial_data=None,
        )
    exit_code = proc.returncode
    stdout = proc.stdout
    stderr = proc.stderr
    # Cap on read so a runaway process cannot exhaust memory.
    if len(stdout) > output_limit_bytes:
        stdout = stdout[:output_limit_bytes]
    if len(stderr) > output_limit_bytes:
        stderr = stderr[:output_limit_bytes]
    return _parse(exit_code, stdout, stderr)


def _parse(exit_code: int, stdout: str, stderr: str) -> CommandResult:
    if exit_code == 0:
        return _parse_success(stdout)
    return _parse_failure(exit_code, stdout, stderr)


def _parse_success(stdout: str) -> CommandResult:
    payload: dict | None = None
    text = stdout.strip()
    if text:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {"raw": text}
    return CommandResult(
        exit_code=0,
        payload=payload,
        error=None,
        required_action="none",
        partial_data=None,
    )


def _parse_failure(exit_code: int, stdout: str, stderr: str) -> CommandResult:
    error: dict | None = None
    required_action = "none"
    partial_data: dict | None = None
    # Prefer a structured error envelope on stderr.
    for source in (stderr, stdout):
        text = source.strip()
        if not text:
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("ok") is False:
            error = data.get("error") or {}
            action = error.get("requiredAction") or "none"
            if action not in REQUIRED_ACTIONS:
                action = "none"
            required_action = action
            partial_data = error.get("partialData")
            if partial_data is not None and not isinstance(partial_data, dict):
                partial_data = None
            break
    if error is None:
        error = {"code": "cli.unknown", "message": stderr.strip() or stdout.strip()}
    return CommandResult(
        exit_code=exit_code,
        payload=None,
        error=error,
        required_action=required_action,
        partial_data=partial_data,
    )
