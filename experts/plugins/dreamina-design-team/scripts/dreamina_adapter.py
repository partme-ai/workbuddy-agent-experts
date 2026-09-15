"""Argv-only adapter for the `dreamina` CLI.

This module provides a thin, deterministic wrapper around the `dreamina`
binary. It enforces:

* argv-only execution (``shell=False``; no string interpolation);
* typed error surfaces for missing CLI, auth/permission failures, invalid
  JSON, upgrade notices, and timeouts;
* separate stdout / stderr capture;
* a hard output-size cap to avoid buffering huge responses;
* a ``capability_snapshot`` helper that combines ``--version`` and
  ``--help`` / ``schema`` outputs into the canonical capability snapshot.

The adapter never installs, authenticates, or runs paid operations. It is
the only sanctioned seam between Codex Skill code and the installed binary.
"""

from __future__ import annotations

import json
import hashlib
import hmac
import atexit
import os
import re
import selectors
import signal
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_OUTPUT_BYTES = 1 * 1024 * 1024  # 1 MiB
CAPABILITY_MODES = (
    "text2image",
    "image2image",
    "image_upscale",
    "text2video",
    "image2video",
    "frames2video",
    "multiframe2video",
    "multimodal2video",
)


class DreaminaAdapterError(RuntimeError):
    """Base class for all adapter-level errors."""

    def __init__(self, message: str, *, invocation_started: bool = False,
                 outcome_ambiguous: bool = False, submit_id: str | None = None) -> None:
        self.invocation_started = invocation_started
        self.outcome_ambiguous = outcome_ambiguous
        self.submit_id = submit_id
        super().__init__(message)


class CLINotFoundError(DreaminaAdapterError):
    """The configured `dreamina` binary could not be located or executed."""


class UntrustedCLIError(DreaminaAdapterError):
    """The CLI path, permissions, ownership, or digest failed trust checks."""


class PermissionDeniedError(DreaminaAdapterError):
    """The CLI reported missing authentication or insufficient permission."""


class UpgradeRequiredError(DreaminaAdapterError):
    """The CLI signalled that a newer version is required."""


class InvalidJSONError(DreaminaAdapterError):
    """The CLI did not emit a parseable JSON payload on stdout."""


class TimeoutError(DreaminaAdapterError):  # noqa: A001 (mirrors builtin on purpose)
    """The CLI exceeded the configured timeout. No resubmission is performed."""


@dataclass(frozen=True)
class DreaminaResult:
    """Structured result of a single CLI invocation."""

    exit_code: int
    payload: Mapping[str, object] | list | None
    error_code: str | None
    submit_id: str | None
    stderr: str


@dataclass(frozen=True)
class DreaminaTextResult:
    """Bounded raw-text result for non-JSON CLI commands."""

    exit_code: int
    stdout: str
    stderr: str


class DreaminaAdapter:
    """Argv-only wrapper around an installed `dreamina` binary.

    The binary path is injected explicitly. Tests inject a shell-script
    stub; production code resolves `dreamina` from ``PATH`` or a configured
    absolute path. Authentication, model catalogs, and any paid operation
    are out of scope for this module.
    """

    def __init__(
        self,
        cli_command: str = "dreamina",
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
        trusted_binary_sha256: str | None = None,
    ) -> None:
        self.cli_command = cli_command
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes
        self.env = self._minimal_environment()
        self.trusted_binary_sha256 = trusted_binary_sha256
        self._trusted_binary_dir: Path | None = None
        self._trusted_binary_path: str | None = None

    def _resolve_cli(self) -> str:
        if self._trusted_binary_path is not None:
            return self._trusted_binary_path
        target = Path(self.cli_command)
        if not target.is_absolute():
            raise UntrustedCLIError("dreamina CLI path must be absolute; PATH lookup is disabled")
        if target.is_symlink() or not target.is_file() or not os.access(target, os.X_OK):
            raise CLINotFoundError(f"dreamina CLI must be an executable regular non-symlink file: {target}")
        stat = target.stat()
        if stat.st_uid not in {0, os.getuid()} or stat.st_mode & 0o022:
            raise UntrustedCLIError("dreamina CLI owner or write permissions are not trusted")
        for parent in target.parents:
            parent_stat = parent.stat()
            if parent_stat.st_mode & 0o022:
                raise UntrustedCLIError(f"group/world-writable CLI parent directory: {parent}")
        expected = (self.trusted_binary_sha256 or "").lower()
        if re.fullmatch(r"[0-9a-f]{64}", expected) is None:
            raise UntrustedCLIError("trusted_binary_sha256 is required")
        self._trusted_binary_path = self._stage_trusted_binary(target, expected)
        return self._trusted_binary_path

    def _stage_trusted_binary(self, source: Path, expected_sha256: str) -> str:
        """Copy the opened verified inode into a private immutable execution dir."""
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        source_fd = os.open(source, flags)
        private_root = Path(tempfile.mkdtemp(prefix="dreamina-trusted-"))
        self._trusted_binary_dir = private_root
        atexit.register(shutil.rmtree, private_root, True)
        os.chmod(private_root, 0o700)
        staged = private_root / "dreamina"
        digest = hashlib.sha256()
        try:
            with os.fdopen(source_fd, "rb") as reader, staged.open("xb") as writer:
                while True:
                    chunk = reader.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
                    writer.write(chunk)
                writer.flush()
                os.fsync(writer.fileno())
            if not hmac.compare_digest(digest.hexdigest(), expected_sha256):
                raise UntrustedCLIError(
                    f"dreamina CLI SHA-256 mismatch: expected {expected_sha256}, got {digest.hexdigest()}"
                )
            os.chmod(staged, 0o500)
            return str(staged)
        except Exception:
            shutil.rmtree(private_root, ignore_errors=True)
            self._trusted_binary_dir = None
            raise

    def close(self) -> None:
        """Remove the private staged executable when the adapter is no longer used."""
        if self._trusted_binary_dir is not None:
            shutil.rmtree(self._trusted_binary_dir, ignore_errors=True)
            self._trusted_binary_dir = None
            self._trusted_binary_path = None

    @staticmethod
    def _minimal_environment() -> dict[str, str]:
        allowed = ("HOME", "TMPDIR", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR")
        result = {key: os.environ[key] for key in allowed if key in os.environ}
        result["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"
        return result

    def run(self, args: list[str]) -> DreaminaResult:
        """Invoke the CLI with argv-only arguments and parse its JSON output.

        Raises one of the typed adapter errors when the CLI cannot be run
        cleanly. Returns a :class:`DreaminaResult` on success.
        """
        if not isinstance(args, list):
            raise TypeError("argv must be a list of strings (argv-only)")
        binary = self._resolve_cli()
        cmd = [binary, *args]
        try:
            returncode, stdout_text, stderr_text = self._run_bounded_text(cmd)
        except TimeoutError:
            raise
        except OSError as exc:
            raise CLINotFoundError(f"dreamina CLI not found: {binary}") from exc

        stdout_bytes_size = len(stdout_text.encode("utf-8"))
        if stdout_bytes_size > self.max_output_bytes:
            raise InvalidJSONError(f"dreamina CLI output exceeded {self.max_output_bytes} bytes",
                                   invocation_started=True, outcome_ambiguous=True)

        stderr_lower = stderr_text.lower()
        if "upgrade required" in stderr_lower:
            raise UpgradeRequiredError(stderr_text.strip() or "upgrade required",
                                       invocation_started=True, outcome_ambiguous=False)
        if returncode != 0:
            if (
                "not authenticated" in stderr_lower
                or "permission denied" in stderr_lower
                or "unauthorized" in stderr_lower
            ):
                raise PermissionDeniedError(stderr_text.strip() or "permission denied",
                                            invocation_started=True, outcome_ambiguous=False)
            payload = _safe_parse_json(stdout_text)
            if payload is None:
                raise DreaminaAdapterError(f"dreamina CLI failed (exit {returncode}): {stderr_text.strip()}",
                                           invocation_started=True, outcome_ambiguous=False)
            return DreaminaResult(
                exit_code=returncode,
                payload=payload,
                error_code=str(payload.get("error_code")) if isinstance(payload, Mapping) else None,
                submit_id=str(payload.get("submit_id")) if isinstance(payload, Mapping) and payload.get("submit_id") is not None else None,
                stderr=stderr_text,
            )

        payload = _safe_parse_json(stdout_text)
        if payload is None:
            raise InvalidJSONError("dreamina CLI did not emit JSON on stdout",
                                   invocation_started=True, outcome_ambiguous=True)
        submit_id = None
        if isinstance(payload, Mapping):
            raw = payload.get("submit_id")
            if raw is not None:
                submit_id = str(raw)
        return DreaminaResult(
            exit_code=returncode,
            payload=payload,
            error_code=None,
            submit_id=submit_id,
            stderr=stderr_text,
        )

    def run_text(self, args: list[str]) -> DreaminaTextResult:
        """Run a fixed-domain argv list without requiring JSON stdout."""
        if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
            raise TypeError("argv must be a list of strings (argv-only)")
        binary = self._resolve_cli()
        try:
            exit_code, stdout, stderr = self._run_bounded_text([binary, *args])
        except OSError as exc:
            raise CLINotFoundError(f"dreamina CLI not found: {binary}") from exc
        return DreaminaTextResult(exit_code=exit_code, stdout=stdout, stderr=stderr)

    def _run_bounded_text(self, cmd: list[str]) -> tuple[int, str, str]:
        """Run argv-only with streaming byte limits on stdout and stderr."""
        process = subprocess.Popen(  # noqa: S603
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            env=self.env,
            start_new_session=True,
        )
        try:
            return self._communicate_bounded(process)
        except DreaminaAdapterError:
            raise
        except (OSError, subprocess.SubprocessError) as exc:
            if process.poll() is None:
                try: self._terminate_process_group(process)
                except (OSError, subprocess.SubprocessError): pass
            for stream in (process.stdout, process.stderr):
                if stream is not None and not stream.closed:
                    stream.close()
            raise DreaminaAdapterError(
                "dreamina CLI failed after process start",
                invocation_started=True, outcome_ambiguous=True) from exc

    def _communicate_bounded(self, process: subprocess.Popen) -> tuple[int, str, str]:
        """Read one already-started process; every failure is post-spawn."""
        selector = selectors.DefaultSelector()
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        try:
            assert process.stdout is not None and process.stderr is not None
            selector.register(process.stdout, selectors.EVENT_READ, "stdout")
            selector.register(process.stderr, selectors.EVENT_READ, "stderr")
            deadline = time.monotonic() + self.timeout_seconds
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self._terminate_process_group(process)
                    raise TimeoutError(
                        f"dreamina CLI timed out after {self.timeout_seconds}s; operation NOT resubmitted",
                        invocation_started=True, outcome_ambiguous=True)
                for key, _ in selector.select(timeout=min(remaining, 0.1)):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    buffer = buffers[key.data]
                    buffer.extend(chunk)
                    if len(buffer) > self.max_output_bytes:
                        self._terminate_process_group(process)
                        raise InvalidJSONError(
                            f"dreamina CLI {key.data} exceeded {self.max_output_bytes} bytes",
                            invocation_started=True, outcome_ambiguous=True)
            returncode = process.wait(timeout=max(0.1, deadline - time.monotonic()))
        finally:
            selector.close()
            if process.poll() is None:
                self._terminate_process_group(process)
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
        return (
            returncode,
            buffers["stdout"].decode("utf-8", errors="replace"),
            buffers["stderr"].decode("utf-8", errors="replace"),
        )

    @staticmethod
    def _terminate_process_group(process: subprocess.Popen) -> None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()

    def capability_snapshot(self) -> dict:
        """Return a parsed capability snapshot from the live CLI.

        Combines ``--version`` and ``schema`` (or ``--help``) into the
        shape described by ``schemas/capability_snapshot.schema.json``.
        """
        version_text = self._run_text(["--version"]).strip()
        version_payload = _safe_parse_json(version_text)
        cli_version = ""
        cli_commit = None
        if isinstance(version_payload, Mapping):
            cli_version = str(version_payload.get("version", "")).strip()
            cli_commit = version_payload.get("commit")
        if not cli_version:
            match = re.search(r"\b(\d+\.\d+\.\d+(?:[+-][A-Za-z0-9.-]+)?)\b", version_text)
            if match:
                cli_version = match.group(1)
        if not cli_version:
            raise InvalidJSONError("dreamina --version emitted no usable build identity")

        schema_payload: Mapping[str, object] = {}
        try:
            schema_result = self.run(["schema"])
            if isinstance(schema_result.payload, Mapping):
                schema_payload = schema_result.payload
        except DreaminaAdapterError as exc:
            if 'unknown command "schema"' not in str(exc):
                raise
            help_text = self._run_text(["--help"])
            modes = [
                mode
                for mode in CAPABILITY_MODES
                if re.search(rf"(?m)^\s{{2}}{re.escape(mode)}\s+", help_text)
            ]
            schema_payload = _parse_command_help(
                {mode: self._run_text([mode, "--help"]) for mode in modes}
            )
        snapshot = {
            "cli_version": cli_version or "0.0.0",
            "captured_at": _now_iso(),
            "modes": [],
        }
        if cli_commit:
            snapshot["cli_commit"] = cli_commit
        if schema_payload:
            if schema_payload.get("cli_commit"):
                snapshot["cli_commit"] = schema_payload["cli_commit"]
            modes = schema_payload.get("modes")
            if isinstance(modes, list):
                snapshot["modes"] = modes
            for key in ("models", "resolutions", "ratios", "durations", "mode_limits", "pricing"):
                if key in schema_payload:
                    snapshot[key] = schema_payload[key]
        return snapshot

    def _run_text(self, args: list[str]) -> str:
        """Run a read-only help command whose stdout is plain text."""
        binary = self._resolve_cli()
        returncode, stdout_text, stderr_text = self._run_bounded_text([binary, *args])
        if returncode != 0:
            raise DreaminaAdapterError(
                f"dreamina CLI failed (exit {returncode}): {stderr_text.strip()}"
            )
        return stdout_text


def _safe_parse_json(text: str):
    if not text or not text.strip():
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _parse_command_help(command_help: Mapping[str, str]) -> dict:
    """Derive capability unions from the installed CLI's generator help."""
    models: dict[str, dict] = {}
    resolutions = {"image": set(), "video": set()}
    ratios: set[str] = set()
    duration_bounds: list[int] = []
    mode_limits: dict[str, dict[str, int]] = {}
    for mode, help_text in command_help.items():
        model_match = re.search(
            r"(?m)(?:^- model_version(?: values)?:|--model_version\s+\w+\s+supported values:|flag values:)\s*([^\n)]+)",
            help_text,
        )
        if model_match:
            for token in model_match.group(1).split(","):
                name = token.strip()
                if name:
                    entry = models.setdefault(name, {"name": name, "modes": []})
                    entry["modes"].append(mode)
        mode_ratios = set(re.findall(r"\b(?:21:9|16:9|9:16|4:3|3:4|3:2|2:3|1:1)\b", help_text))
        ratios.update(mode_ratios)
        values = {
            value.lower()
            for value in re.findall(
                r"\b(?:1(?:\.5)?k|2k|4k|480p|720p|1080p)\b",
                help_text,
                re.IGNORECASE,
            )
        }
        resolutions["image" if mode.endswith("image") else "video"].update(values)
        mode_bounds = [
            (int(lower), int(upper))
            for lower, upper in re.findall(r"duration[^\n]*?(\d+)-(\d+)", help_text)
        ]
        for lower, upper in mode_bounds:
            duration_bounds.extend((int(lower), int(upper)))
        count_match = re.search(r"generate_num:\s*(\d+)-(\d+)", help_text)
        reference_count_match = re.search(r"Upload\s+(\d+)\s+to\s+(\d+)\s+local images", help_text)
        if mode == "multiframe2video" and reference_count_match:
            transition_bounds = re.search(r"transition duration\s+(\d+)-(\d+)s", help_text)
            request_bounds = re.search(r"request duration\s+(\d+)-(\d+)s", help_text)
            if transition_bounds and request_bounds:
                mode_limits[mode] = {
                    "min_references": int(reference_count_match.group(1)),
                    "max_references": int(reference_count_match.group(2)),
                    "request_duration_min_seconds": int(request_bounds.group(1)),
                    "request_duration_max_seconds": int(request_bounds.group(2)),
                    "transition_duration_min_seconds": int(transition_bounds.group(1)),
                    "transition_duration_max_seconds": int(transition_bounds.group(2)),
                }
        for entry in models.values():
            if mode not in entry["modes"]:
                continue
            entry.setdefault("ratios", set()).update(mode_ratios)
            if count_match and mode.endswith("image"):
                entry["max_count"] = int(count_match.group(2))
            if reference_count_match and mode == "image2image":
                entry["max_references"] = int(reference_count_match.group(2))
            if mode == "multimodal2video":
                entry.setdefault("max_references", 12)
            entry.setdefault("resolutions", set())
            for line in help_text.splitlines():
                if not line.startswith("- ") or "->" not in line or re.search(
                    rf"(?<![A-Za-z0-9._]){re.escape(entry['name'])}(?![A-Za-z0-9._])",
                    line.split("->", 1)[0],
                ) is None:
                    continue
                entry["resolutions"].update(
                    value.lower()
                    for value in re.findall(
                        r"\b(?:1(?:\.5)?k|2k|4k|480p|720p|1080p)\b", line, re.IGNORECASE
                    )
                )
                bounds = re.search(r"output duration\s+(\d+)-(\d+)s", line)
                if bounds is None and "video/audio duration" not in line:
                    bounds = re.search(r"duration\s+(\d+)-(\d+)s", line)
                if bounds:
                    entry["duration_min_seconds"] = int(bounds.group(1))
                    entry["duration_max_seconds"] = int(bounds.group(2))
                reference_bounds = re.search(r"video/audio duration\s+(\d+)-(\d+)s", line)
                if reference_bounds:
                    entry["audio_reference_max_seconds"] = int(reference_bounds.group(2))
                total_inputs = re.search(r"total inputs<=([0-9]+)", line)
                if total_inputs:
                    entry["max_references"] = int(total_inputs.group(1))
            if mode in {"image2video", "frames2video"} and re.search(
                rf"not accepted with model_version\s+{re.escape(entry['name'])}", help_text
            ):
                entry.setdefault("ratio_forbidden_modes", []).append(mode)
        # Apply explicit "all other models" constraints to entries that did not
        # receive a model-specific line for this mode.
        other_line = next((line for line in help_text.splitlines() if "all other" in line and "->" in line), "")
        if other_line:
            other_resolutions = {
                value.lower() for value in re.findall(r"\b(?:480p|720p|1080p|4k)\b", other_line, re.IGNORECASE)
            }
            bounds = re.search(r"duration\s+(\d+)-(\d+)s", other_line)
            for entry in models.values():
                if mode in entry["modes"] and not entry.get("resolutions"):
                    entry["resolutions"] = set(other_resolutions)
                    if bounds:
                        entry["duration_min_seconds"] = int(bounds.group(1))
                        entry["duration_max_seconds"] = int(bounds.group(2))
    result = {
        "modes": list(command_help),
        "models": [
            {
                key: sorted(value) if isinstance(value, set) else value
                for key, value in entry.items()
            }
            for _, entry in sorted(models.items())
        ],
        "resolutions": {
            key: sorted(values) for key, values in resolutions.items() if values
        },
        "ratios": sorted(ratios),
    }
    if duration_bounds:
        result["durations"] = {
            "min_seconds": min(duration_bounds),
            "max_seconds": max(duration_bounds),
        }
    if mode_limits:
        result["mode_limits"] = mode_limits
    return result


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="dreamina argv adapter probe")
    parser.add_argument("--cli-command", required=True)
    parser.add_argument("--trusted-sha256", required=True)
    parser.add_argument("args", nargs="*")
    args = parser.parse_args()
    adapter = DreaminaAdapter(
        cli_command=args.cli_command,
        trusted_binary_sha256=args.trusted_sha256,
    )
    try:
        result = adapter.run(args.args)
    except DreaminaAdapterError as exc:
        print(f"adapter error: {exc}")
        raise SystemExit(2) from exc
    print(json.dumps(result.payload, indent=2))
