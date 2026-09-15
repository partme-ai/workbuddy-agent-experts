#!/usr/bin/env python3
"""Drive one generation step by invoking Codex, and decide honestly whether it worked.

The plugin does not generate images. It asks Codex to, once, and then checks the
filesystem for evidence. That ordering produces the single most important rule
here: an exit code of zero is a claim, not a result. A step is successful only
when a new image file appeared in the generation directory, so a run that reports
success without producing anything is recorded as a failure rather than as a
completed item.

Three further rules are enforced by construction rather than by policy:

* Every attempt is a fresh argv-array subprocess. There is no retry loop inside
  this module, because a silent retry is how one bad prompt becomes a large bill.
* The approval-bypass flags are never passed. Whatever approval posture the user
  configured for Codex stays in force.
* An exhausted usage limit is classified, its reset time is recorded, and the
  attempt stops there.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from artifact_collector import new_entries, snapshot

DEFAULT_TIMEOUT_SECONDS = 600.0
IMAGE_LIMIT_ID = "image_gen"

# Stable wrapper telling Codex what this invocation is for. Kept minimal and
# constant so the author's prompt stays the only variable part of a request.
GENERATION_INSTRUCTION = (
    "Generate exactly one image with the built-in image generation tool. "
    "Treat any attached images as visual references for the result. "
    "Do not modify or create any other file. "
    "When you are done, reply with the absolute path of the generated image.\n\n"
    "Image description:\n"
)

# Never passed, and asserted against in tests: these would silently widen what a
# batch run is allowed to do to the machine.
FORBIDDEN_FLAGS = (
    "--dangerously-bypass-approvals-and-sandbox",
    "--yolo",
    "--dangerously-bypass-hook-trust",
)


@dataclass(frozen=True)
class GenerationFailure:
    code: str
    message: str
    limit_id: str | None = None
    resets_at: int | None = None


@dataclass(frozen=True)
class GenerationOutcome:
    ok: bool
    failure: GenerationFailure | None = None
    session_id: str | None = None
    last_message: str = ""
    events: tuple[dict, ...] = ()
    exit_code: int | None = None
    attempts_made: int = 0
    new_files: tuple[str, ...] = ()
    before_snapshot: dict = field(default_factory=dict)


def build_prompt(prompt: str) -> str:
    return GENERATION_INSTRUCTION + prompt


def build_argv(
    *,
    binary: str,
    prompt: str,
    reference_images: tuple[str, ...] | list[str],
    workdir: Path,
    last_message_path: Path,
) -> list[str]:
    """Build the Codex invocation as an argv array; a shell string is never used."""
    argv = [
        binary,
        "exec",
        "--json",
        "--skip-git-repo-check",
        "--color",
        "never",
        "-C",
        str(workdir),
        "-o",
        str(last_message_path),
    ]
    for reference in reference_images:
        argv.extend(["-i", str(reference)])
    if reference_images:
        argv.append("--")
    argv.append(build_prompt(prompt))
    return argv


def _parse_events(stdout: str) -> tuple[dict, ...]:
    events: list[dict] = []
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            payload = json.loads(stripped)
        except ValueError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return tuple(events)


def _usage_limit_failure(stdout: str, stderr: str, events: tuple[dict, ...]) -> GenerationFailure | None:
    """Detect an exhausted image allowance without matching on the limit id alone.

    Matching the substring "image_gen" would fire on the ordinary
    `image_generation` item, so detection keys on the failure marker instead and
    the limit id is only read out of an event already known to be a limit event.
    """
    markers = ("usage_limit_exceeded", "usagelimitexceeded", "usage limit", "rate limit", "quota")
    source: dict | None = None
    for event in events:
        lowered = json.dumps(event).lower()
        if any(marker in lowered for marker in markers):
            source = event
            break
    if source is None:
        lowered_error = (stderr or "").lower()
        if any(marker in lowered_error for marker in ("usage limit", "rate limit", "quota")):
            source = {}

    if source is None:
        return None

    limit_id = _find_key(source, "limit_id")
    if not isinstance(limit_id, str):
        limit_id = IMAGE_LIMIT_ID
    resets_at = _find_key(source, "resets_at")
    if not isinstance(resets_at, int):
        resets_at = None
    return GenerationFailure(
        code="quota_exceeded",
        message="the image generation usage limit for this account was reached",
        limit_id=limit_id,
        resets_at=resets_at,
    )


def _error_message(events: tuple[dict, ...], stderr: str) -> str:
    """Prefer the event stream's own error text; fall back to stderr, then to the exit code."""
    for event in events:
        if event.get("type") == "error" and isinstance(event.get("message"), str):
            return event["message"]
    for event in events:
        candidate = _find_key(event, "message")
        if isinstance(candidate, str) and candidate.strip():
            return candidate
    lines = [line for line in (stderr or "").strip().splitlines() if line.strip()]
    if lines:
        return lines[-1]
    return "codex exited without reporting a reason"


def _find_key(node: object, key: str) -> object | None:
    if isinstance(node, dict):
        if key in node:
            return node[key]
        for value in node.values():
            found = _find_key(value, key)
            if found is not None:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _find_key(value, key)
            if found is not None:
                return found
    return None


def _session_id(events: tuple[dict, ...], new_files: tuple[str, ...]) -> str | None:
    for event in events:
        if event.get("type") == "session.started" and isinstance(event.get("session_id"), str):
            return event["session_id"]
    for event in events:
        candidate = _find_key(event, "session_id")
        if isinstance(candidate, str):
            return candidate
    if new_files:
        parts = Path(new_files[0]).parts
        if len(parts) >= 2:
            return parts[-2]
    return None


def run_item(
    *,
    binary: str,
    item: object,
    round_number: int,
    workdir: Path,
    output_dir: Path,
    generation_dir: Path,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> GenerationOutcome:
    """Invoke Codex once for one batch item. Never retries."""
    workdir = Path(workdir)
    output_dir = Path(output_dir)
    generation_dir = Path(generation_dir)
    workdir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    last_message_path = output_dir / f"{getattr(item, 'id')}-round-{round_number}.last-message.txt"
    before = snapshot(generation_dir)
    argv = build_argv(
        binary=binary,
        prompt=getattr(item, "prompt"),
        reference_images=getattr(item, "reference_images"),
        workdir=workdir,
        last_message_path=last_message_path,
    )

    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            cwd=str(workdir),
        )
    except subprocess.TimeoutExpired:
        return GenerationOutcome(
            ok=False,
            failure=GenerationFailure(
                "timeout",
                f"codex did not finish within {timeout_seconds:.0f}s; it is not retried automatically",
            ),
            attempts_made=1,
            before_snapshot=before,
        )
    except (FileNotFoundError, NotADirectoryError, PermissionError, OSError) as error:
        return GenerationOutcome(
            ok=False,
            failure=GenerationFailure("codex_missing", f"codex could not be executed: {error}"),
            attempts_made=1,
            before_snapshot=before,
        )

    events = _parse_events(completed.stdout or "")
    last_message = ""
    try:
        last_message = last_message_path.read_text(encoding="utf-8")
    except OSError:
        last_message = ""

    common = {
        "session_id": None,
        "last_message": last_message,
        "events": events,
        "exit_code": completed.returncode,
        "attempts_made": 1,
    }

    if completed.returncode < 0:
        return GenerationOutcome(
            ok=False,
            failure=GenerationFailure(
                "interrupted",
                f"codex was terminated by signal {-completed.returncode}; its external outcome is unknown",
            ),
            before_snapshot=before,
            **common,
        )

    limit = _usage_limit_failure(completed.stdout or "", completed.stderr or "", events)
    if limit is not None:
        return GenerationOutcome(ok=False, failure=limit, before_snapshot=before, **common)

    after = snapshot(generation_dir)
    fresh = new_entries(before, after)

    if completed.returncode != 0:
        return GenerationOutcome(
            ok=False,
            failure=GenerationFailure("generation_failed", _error_message(events, completed.stderr)),
            before_snapshot=before,
            new_files=fresh,
            **{**common, "session_id": _session_id(events, fresh)},
        )

    if not fresh:
        return GenerationOutcome(
            ok=False,
            failure=GenerationFailure(
                "artifact_missing",
                "codex reported success but no new image appeared in the generation directory",
            ),
            before_snapshot=before,
            new_files=(),
            **{**common, "session_id": _session_id(events, ())},
        )

    return GenerationOutcome(
        ok=True,
        new_files=fresh,
        before_snapshot=before,
        **{**common, "session_id": _session_id(events, fresh)},
    )


def as_report(outcome: GenerationOutcome) -> dict:
    return {
        "ok": outcome.ok,
        "failure": (
            {
                "code": outcome.failure.code,
                "message": outcome.failure.message,
                "limit_id": outcome.failure.limit_id,
                "resets_at": outcome.failure.resets_at,
            }
            if outcome.failure
            else None
        ),
        "session_id": outcome.session_id,
        "last_message": outcome.last_message,
        "exit_code": outcome.exit_code,
        "attempts_made": outcome.attempts_made,
        "new_files": list(outcome.new_files),
    }


def resolved_binary(explicit: str | None = None) -> str:
    """Pick the Codex binary to invoke, preferring an explicit path."""
    if explicit:
        return explicit
    import shutil

    found = shutil.which("codex")
    if found:
        return found
    home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    bundled = home / "plugins" / ".plugin-appserver" / "codex"
    if bundled.is_file():
        return str(bundled)
    return "codex"
