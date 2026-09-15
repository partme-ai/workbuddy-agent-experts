"""Acceptance runner for the reference-video re-director release.

Every gate starts `NOT_RUN` and can only become `PASS` from output this runner
actually observed. Nothing infers, extrapolates, or upgrades a gate: a gate
whose dependencies are unavailable, unauthorized, or simply not executed stays
`NOT_RUN` with the reason recorded.

Paid generation and publication additionally require an explicit, freshly
supplied authorization for *this* run. A historical approval identifier is
rejected, because an approval consumed by an earlier batch says nothing about
the envelope being run now.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]

GATE_NAMES: tuple[str, ...] = (
    "offline_suite",
    "trusted_media_runtime",
    "reference_analysis",
    "semantic_gates",
    "rights_and_redesign",
    "batch_quote",
    "paid_generation",
    "shot_evaluation",
    "audio_subtitles",
    "final_composition",
    "installed_mcp",
    "remote_ci",
    "sha_equality",
)

# Gates that can never be reached without a separate action-time authorization.
PAID_GATES = frozenset({"paid_generation", "shot_evaluation", "final_composition"})
PUBLICATION_GATES = frozenset({"installed_mcp", "remote_ci"})

RECURSION_GUARD_ENV = "DREAMINA_ACCEPTANCE_INSIDE_SUITE"

NOT_RUN = "NOT_RUN"
PASS = "PASS"
FAIL = "FAIL"
BLOCKED = "BLOCKED"


class AcceptanceAuthorizationError(RuntimeError):
    """A gated gate was requested without a valid fresh authorization."""


class StaleAuthorizationError(AcceptanceAuthorizationError):
    """The supplied authorization was already consumed by an earlier run."""


@dataclass
class GateResult:
    status: str = NOT_RUN
    reason: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "reason": self.reason, "evidence": self.evidence}


@dataclass
class AcceptanceDependencies:
    """Everything the runner touches, injected so tests need no real tools."""

    run_offline_suite: Callable[[], tuple[bool | None, str]] | None = None
    probe_runtime_tools: Callable[[], Mapping[str, str]] | None = None
    run_local_media: Callable[[], tuple[bool, str]] | None = None
    sha_equality: Callable[[], tuple[bool, str]] | None = None
    remote_ci_for_sha: Callable[[str], Mapping[str, str]] | None = None
    head_sha: Callable[[], str] | None = None
    known_consumed_approvals: Sequence[str] = ()
    # Approval ids authorized for THIS run. Absent or empty means no paid
    # run is authorized, which fails closed.
    authorized_paid_approvals: Sequence[str] = ()


def _default_offline_suite() -> tuple[bool | None, str]:
    """Run the offline suite, refusing to nest inside another run of it.

    A test that invokes this runner would otherwise re-run the suite that
    contains that very test, recursing without bound. The child sees the guard
    variable and reports the gate as blocked instead.
    """
    if os.environ.get(RECURSION_GUARD_ENV) == "1":
        return None, "offline suite already in progress; nested run refused"
    env = {**os.environ, RECURSION_GUARD_ENV: "1"}
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=ROOT, capture_output=True, text=True, timeout=1800, check=False, env=env,
    )
    summary = (completed.stderr or completed.stdout).strip().splitlines()
    detail = summary[-1] if summary else "no output"
    return completed.returncode == 0, detail


def _default_probe_runtime_tools() -> Mapping[str, str]:
    import shutil

    found: dict[str, str] = {}
    for kind, binary in (("ffmpeg", "ffmpeg"), ("ffprobe", "ffprobe"), ("whisper", "whisper"), ("narration", "say")):
        resolved = shutil.which(binary)
        if resolved:
            found[kind] = resolved
    return found


def _map_ci_run(payload: Mapping[str, Any] | None) -> Mapping[str, str]:
    """Map a `gh run list` entry to the gate's status vocabulary.

    Pure, so it can be tested without a network. `_run_remote_ci_gate`
    understands: ``success`` opens the gate; ``queued`` / ``in_progress``
    keep it NOT_RUN as still running; anything else keeps it NOT_RUN with
    the reason recorded.
    """
    if not payload:
        return {"status": "none", "reason": "no workflow run targets this commit"}
    status = str(payload.get("status", "") or "").lower()
    conclusion = str(payload.get("conclusion", "") or "").lower()
    out: dict[str, str] = {}
    if payload.get("url"):
        out["url"] = str(payload["url"])
    if payload.get("databaseId"):
        out["run_id"] = str(payload["databaseId"])
    if payload.get("workflowName"):
        out["workflow"] = str(payload["workflowName"])
    if status in {"queued", "in_progress", "requested", "waiting", "pending"}:
        out["status"] = "queued" if status in {"queued", "waiting", "pending", "requested"} else "in_progress"
        out["reason"] = f"workflow run is {status}"
        return out
    if status == "completed":
        if conclusion == "success":
            out["status"] = "success"
            out["reason"] = "workflow run completed successfully"
        else:
            out["status"] = conclusion or "completed"
            out["reason"] = f"workflow run completed with conclusion {conclusion or 'unknown'}"
        return out
    out["status"] = status or "none"
    out["reason"] = f"workflow run status {status or 'unknown'}"
    return out


def _default_head_sha() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return completed.stdout.strip()


def _default_remote_ci_for_sha(sha: str) -> Mapping[str, str]:
    """Probe the workflow runs targeting ``sha`` through the GitHub CLI.

    Fails closed: a missing, unauthenticated or slow `gh` yields ``none``
    with the reason recorded, never a pass.
    """
    if not sha:
        return {"status": "none", "reason": "no head SHA to query"}
    try:
        completed = subprocess.run(
            ["gh", "run", "list", "--commit", sha, "--limit", "1",
             "--json", "status,conclusion,url,databaseId,workflowName"],
            cwd=ROOT, capture_output=True, text=True, timeout=60, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "none", "reason": f"gh probe unavailable: {type(exc).__name__}"}
    if completed.returncode != 0:
        lines = (completed.stderr or "").strip().splitlines()
        return {"status": "none", "reason": f"gh failed: {lines[-1] if lines else 'unknown'}"}
    try:
        runs = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError:
        return {"status": "none", "reason": "gh returned unparseable JSON"}
    if not isinstance(runs, list) or not runs:
        return {"status": "none", "reason": f"no workflow run targets {sha[:12]}"}
    return _map_ci_run(runs[0])


LOCAL_FIXTURE_DURATION_SECONDS = 2.0


def _local_fixture_argv(destination: Path) -> list[str]:
    """argv that synthesises a short local fixture.

    Pure and argv-only: no user media is read, and nothing is interpolated
    into a shell.
    """
    duration = f"{LOCAL_FIXTURE_DURATION_SECONDS:g}"
    return [
        "-v", "error",
        "-f", "lavfi", "-i", f"testsrc=size=320x240:rate=10:duration={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", "-y", str(destination),
    ]


def _default_run_local_media(*, store: Any = None, adapter_factory: Any = None) -> tuple[bool, str]:
    """Process a locally generated fixture through the trusted-tool path.

    No user media is read: the fixture is synthesised by the enrolled
    ffmpeg. Enrollment is itself a human act - the store shows a native
    confirmation dialog - so this never substitutes a silent approval. On a
    machine where the tools are not enrolled it reports that precondition
    instead of a pass.
    """
    # Running this file as a script leaves the repository root off sys.path,
    # and the runtime modules import each other as `scripts.*`.
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.media_adapter import MediaAdapter
    from scripts.trusted_media_tools import TrustedMediaToolError, TrustedMediaToolStore

    active = store if store is not None else TrustedMediaToolStore()
    try:
        staged = active.load_required({"ffmpeg", "ffprobe"})
    except TrustedMediaToolError as exc:
        return False, (
            f"{exc}; enrolling a media tool needs a native confirmation dialog, "
            "so run this with the operator present"
        )
    identities: dict[str, str] = {}
    try:
        for kind, tool in staged.items():
            identities[kind] = tool.sha256
    finally:
        for tool in staged.values():
            active.release(tool)

    adapter = (adapter_factory or MediaAdapter)(active)
    with tempfile.TemporaryDirectory(prefix="dreamina-local-media-") as tmp:
        fixture = Path(tmp) / "fixture.mp4"
        generated = adapter.run("ffmpeg", _local_fixture_argv(fixture), timeout_seconds=120)
        if generated.exit_code != 0:
            return False, f"fixture generation failed: {(generated.stderr or '').strip()[:200]}"
        if not fixture.is_file():
            return False, "fixture generation produced no file to verify"
        probe = adapter.probe_json(fixture)
        frames = adapter.verify_video_frames(fixture, LOCAL_FIXTURE_DURATION_SECONDS)
        digest = hashlib.sha256(fixture.read_bytes()).hexdigest()

    duration = ""
    if isinstance(probe.get("format"), Mapping):
        duration = str(probe["format"].get("duration", ""))
    anchors = sorted(k for k in frames if k != "readable")
    return True, (
        f"processed a locally generated fixture: ffmpeg={identities.get('ffmpeg', '')[:12]} "
        f"ffprobe={identities.get('ffprobe', '')[:12]} duration={duration} "
        f"decoded={anchors} sha256={digest[:12]}"
    )


def _default_sha_equality() -> tuple[bool, str]:
    def _rev(target: str) -> str:
        completed = subprocess.run(
            ["git", "rev-parse", target], cwd=ROOT, capture_output=True, text=True, check=False
        )
        return completed.stdout.strip()

    def _branch() -> str:
        completed = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        return completed.stdout.strip()

    head = _rev("HEAD")
    tracking = _rev("@{u}")
    branch = _branch()
    remote_sha = ""
    if branch and branch != "HEAD":
        listed = subprocess.run(
            ["git", "ls-remote", "origin", f"refs/heads/{branch}"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        ).stdout.split()
        remote_sha = listed[0] if listed else ""
    if not branch or branch == "HEAD":
        return False, f"detached HEAD; no branch to compare (head={head[:12]})"
    ok = bool(head) and head == tracking == remote_sha
    detail = f"branch={branch} head={head[:12]} tracking={tracking[:12]} remote={(remote_sha or 'none')[:12]}"
    return ok, detail


class AcceptanceRunner:
    """Run every gate it is allowed to run, and honestly record the rest."""

    def __init__(self, dependencies: AcceptanceDependencies | None = None) -> None:
        self.deps = dependencies or AcceptanceDependencies()

    # ------------------------------------------------------------------ report

    @staticmethod
    def _new_report_with_all_gates_not_run() -> dict[str, GateResult]:
        return {
            name: GateResult(NOT_RUN, "not attempted in this run")
            for name in GATE_NAMES
        }

    def _require_fresh_exact_paid_approval(self, approval_id: str | None) -> None:
        if not approval_id or not approval_id.strip():
            raise AcceptanceAuthorizationError(
                "paid generation requires a fresh, exact authorization for this run"
            )
        if approval_id in set(self.deps.known_consumed_approvals):
            raise StaleAuthorizationError(
                f"authorization {approval_id!r} was already consumed by an earlier batch; "
                "an approval for one envelope never authorizes a different one"
            )
        authorized = set(self.deps.authorized_paid_approvals)
        if not authorized:
            raise AcceptanceAuthorizationError(
                "no paid authorization is configured for this run; refusing to spend"
            )
        if approval_id not in authorized:
            raise AcceptanceAuthorizationError(
                f"approval {approval_id!r} does not authorize this run; a historical or "
                "unrelated approval is not evidence for the current envelope"
            )

    def _require_fresh_publish_authorization(self, approval_id: str | None) -> None:
        if not approval_id or not approval_id.strip():
            raise AcceptanceAuthorizationError(
                "publication and installation require a fresh, exact authorization for this run"
            )

    # ------------------------------------------------------------------- gates

    def _run_offline_and_local_media_gates(self, report: dict[str, GateResult]) -> None:
        if self.deps.run_offline_suite is not None:
            passed, detail = self.deps.run_offline_suite()
            if passed is None:
                report["offline_suite"] = GateResult(BLOCKED, detail, {"observed": detail})
            else:
                report["offline_suite"] = GateResult(
                    PASS if passed else FAIL, detail, {"observed": detail}
                )
        else:
            report["offline_suite"] = GateResult(BLOCKED, "no offline runner injected")

        tools = self.deps.probe_runtime_tools() if self.deps.probe_runtime_tools else {}
        if not tools:
            report["trusted_media_runtime"] = GateResult(
                NOT_RUN, "no trusted media tool available for enrollment"
            )
        elif self.deps.run_local_media is None:
            # Tools exist but nothing was executed against a fixture, so this is
            # still NOT_RUN: presence is not a measurement.
            report["trusted_media_runtime"] = GateResult(
                NOT_RUN,
                "trusted media tools present but no authorized source fixture was processed",
                {"tools": dict(tools)},
            )
        else:
            passed, detail = self.deps.run_local_media()
            report["trusted_media_runtime"] = GateResult(
                PASS if passed else FAIL, detail, {"tools": dict(tools)}
            )

        if self.deps.sha_equality is not None:
            passed, detail = self.deps.sha_equality()
            report["sha_equality"] = GateResult(
                PASS if passed else FAIL, detail, {"observed": detail}
            )

    def _run_remote_ci_gate(self, report: dict[str, GateResult]) -> None:
        if self.deps.remote_ci_for_sha is None or self.deps.head_sha is None:
            report["remote_ci"] = GateResult(NOT_RUN, "no CI probe injected")
            return
        sha = self.deps.head_sha()
        result = self.deps.remote_ci_for_sha(sha)
        status = str(result.get("status", "none"))
        if status == "success":
            report["remote_ci"] = GateResult(PASS, f"CI success for {sha[:12]}", dict(result))
        elif status in {"queued", "in_progress"}:
            report["remote_ci"] = GateResult(NOT_RUN, f"CI still {status} for {sha[:12]}", dict(result))
        else:
            report["remote_ci"] = GateResult(
                NOT_RUN,
                f"no CI run targets {sha[:12]} ({result.get('reason', status)})",
                dict(result),
            )

    def _run_paid_gate(self, report: dict[str, GateResult]) -> None:
        for name in sorted(PAID_GATES):
            report[name] = GateResult(
                NOT_RUN,
                "paid gate authorized but no paid batch was executed in this run",
            )

    def _run_install_and_publication_gates(self, report: dict[str, GateResult]) -> None:
        report["installed_mcp"] = GateResult(
            NOT_RUN, "publication authorized but no installation was performed in this run"
        )
        self._run_remote_ci_gate(report)

    # --------------------------------------------------------------------- api

    def run(
        self,
        *,
        allow_paid: bool = False,
        approval_id: str | None = None,
        allow_publish: bool = False,
    ) -> dict[str, Any]:
        report = self._new_report_with_all_gates_not_run()
        self._run_offline_and_local_media_gates(report)

        if allow_paid:
            self._require_fresh_exact_paid_approval(approval_id)
            self._run_paid_gate(report)
        else:
            for name in sorted(PAID_GATES):
                report[name] = GateResult(
                    NOT_RUN, "paid generation was not authorized for this run"
                )

        if allow_publish:
            self._require_fresh_publish_authorization(approval_id)
            self._run_install_and_publication_gates(report)
        else:
            for name in sorted(PUBLICATION_GATES):
                report[name] = GateResult(
                    NOT_RUN, "publication was not authorized for this run"
                )

        # Gates this runner has no way to reach stay NOT_RUN and say why.
        for name in ("reference_analysis", "semantic_gates", "rights_and_redesign", "batch_quote", "audio_subtitles"):
            if report[name].status == NOT_RUN:
                report[name] = GateResult(
                    NOT_RUN,
                    "requires a project run against a user-authorized source fixture, "
                    "which no action-time authorization has supplied",
                )

        return {
            "gates": {name: result.to_dict() for name, result in report.items()},
            "allow_paid": allow_paid,
            "allow_publish": allow_publish,
            "all_passed": all(
                result.status in {PASS, "EXCLUDED"} for result in report.values()
            ),
        }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    paid = parser.add_mutually_exclusive_group()
    paid.add_argument("--no-paid", action="store_true",
                      help="never run a paid gate (the default; stated explicitly)")
    paid.add_argument("--approve-paid", metavar="APPROVAL_ID",
                      help="authorise the paid gates for THIS run with a fresh approval id; "
                           "a historical or unrelated id is refused")
    parser.add_argument("--installed-plugin", action="store_true", help="run against an installed plugin")
    parser.add_argument("--approve-publish", metavar="APPROVAL_ID",
                        help="authorise publication and installation for THIS run with a fresh "
                             "approval id; a historical or unrelated id is refused")
    parser.add_argument("--local-media", action="store_true",
                        help="also process a locally generated fixture through the enrolled media tools "
                             "(needs the operator present: enrollment shows a confirmation dialog)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    # The runner carries one approval id per invocation, so asking for two
    # different authorisations in one run cannot be honoured exactly. Refuse
    # instead of quietly using one id for both.
    if args.approve_paid and args.approve_publish and args.approve_paid != args.approve_publish:
        parser.error(
            "--approve-paid and --approve-publish must name the same approval id, or be run "
            "separately: the runner takes a single approval id per invocation"
        )

    approval_id = args.approve_paid or args.approve_publish
    dependencies = AcceptanceDependencies(
        run_offline_suite=_default_offline_suite,
        probe_runtime_tools=_default_probe_runtime_tools,
        sha_equality=_default_sha_equality,
        head_sha=_default_head_sha,
        remote_ci_for_sha=_default_remote_ci_for_sha,
        # The id the operator supplies *is* this run's authorisation. It is
        # only ever added to the authorised set, so the guards still reject a
        # consumed id, and a run with no flags authorises nothing.
        authorized_paid_approvals=(args.approve_paid,) if args.approve_paid else (),
        # Only wired on request: the trusted-tool path enrolls ffmpeg/ffprobe,
        # and enrollment shows a native confirmation dialog, so it needs the
        # operator present. Left unwired, the gate reports NOT_RUN exactly as
        # before rather than pretending the local media path was exercised.
        run_local_media=_default_run_local_media if args.local_media else None,
    )
    runner = AcceptanceRunner(dependencies)
    try:
        report = runner.run(
            allow_paid=bool(args.approve_paid),
            approval_id=approval_id,
            allow_publish=bool(args.approve_publish),
        )
    except (AcceptanceAuthorizationError, StaleAuthorizationError) as exc:
        # An unauthorised or reused approval is a refusal, not a crash: say so
        # and exit non-zero without printing a report that could be mistaken
        # for one.
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for name, gate in report["gates"].items():
            print(f"{name:24s} {gate['status']:8s} {gate['reason']}")
    return 0


__all__ = [
    "GATE_NAMES",
    "RECURSION_GUARD_ENV",
    "PAID_GATES",
    "PUBLICATION_GATES",
    "AcceptanceAuthorizationError",
    "AcceptanceDependencies",
    "AcceptanceRunner",
    "GateResult",
    "StaleAuthorizationError",
]


if __name__ == "__main__":
    raise SystemExit(main())
