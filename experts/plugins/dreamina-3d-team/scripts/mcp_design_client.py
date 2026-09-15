"""Typed semantic client for the production Dreamina Design MCP boundary."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol


class ToolInvoker(Protocol):
    """Invoke one named MCP tool and return its full tool result envelope."""

    def call(self, name: str, arguments: dict[str, object]) -> dict[str, object]: ...


class McpToolError(RuntimeError):
    """Dreamina Design returned a structured MCP tool failure."""


class UserActionRequired(McpToolError):
    """The MCP operation stopped at an authentication or native approval gate."""


def _structured(envelope: object) -> dict[str, Any]:
    if not isinstance(envelope, Mapping):
        raise McpToolError("Dreamina Design MCP returned a non-object envelope")
    payload = envelope.get("structuredContent")
    if not isinstance(payload, Mapping):
        raise McpToolError("Dreamina Design MCP returned no structuredContent")
    result = dict(payload)
    if envelope.get("isError") is True:
        message = str(result.get("message") or "Dreamina Design MCP tool failed")
        if result.get("requires_user_action") is True:
            raise UserActionRequired(message)
        raise McpToolError(message)
    return result


def _remote_status(payload: Mapping[str, Any]) -> str:
    nested = payload.get("result")
    source = nested if isinstance(nested, Mapping) else payload
    raw = source.get("status", source.get("gen_status", "unknown"))
    status = str(raw).strip().lower()
    if status in {"success", "succeeded", "completed", "done"}:
        return "succeeded"
    if status in {"failed", "fail", "error"}:
        return "failed"
    if status in {"submitted", "querying", "running", "processing", "pending"}:
        return status
    return "unknown"


def _artifact(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    artifacts = payload.get("artifacts")
    if artifacts is None:
        return None
    if not isinstance(artifacts, list):
        raise McpToolError("Dreamina Design returned a non-list `artifacts` field")
    if not artifacts:
        return None
    if len(artifacts) != 1:
        # Surface the server-side surprise instead of silently dropping every
        # artifact and reporting a generic "no artifact" error downstream.
        raise McpToolError(
            f"Dreamina Design returned {len(artifacts)} artifacts; exactly one is expected"
        )
    item = artifacts[0]
    if not isinstance(item, Mapping):
        raise McpToolError("Dreamina Design returned a non-object artifact entry")
    path = item.get("path", item.get("local_path"))
    checksum = item.get("sha256")
    if checksum is None and isinstance(item.get("checksum"), Mapping):
        checksum = item["checksum"].get("digest")
    if not isinstance(path, str) or not path:
        raise McpToolError("Dreamina Design artifact is missing a path")
    if not isinstance(checksum, str) or not checksum:
        raise McpToolError("Dreamina Design artifact is missing a sha256 digest")
    result: dict[str, Any] = {"path": path, "sha256": checksum}
    size = item.get("size_bytes", item.get("bytes"))
    if size is not None:
        result["bytes"] = int(size)
    return result


def _require_within_roots(path: str, roots: object, label: str) -> None:
    """Reject a path that resolves outside every approved root.

    Containment is checked on resolved paths so a symlinked intermediate
    directory cannot be used to escape an approved root, and a root that is
    itself reached through a link (``/tmp`` on macOS) still matches.
    """
    if not roots:
        return
    if not isinstance(roots, (list, tuple)) or not all(isinstance(r, str) for r in roots):
        raise ValueError(f"{label} approved_roots must be a list of strings")
    allowed = [Path(root).expanduser().resolve() for root in roots]
    candidate = Path(path).expanduser().resolve()
    if not any(candidate == root or root in candidate.parents for root in allowed):
        raise ValueError(f"{label} path {candidate} is outside the approved roots {allowed}")


class McpDesignClient:
    """Map durable orchestration actions to the four approved MCP tools."""

    def __init__(self, invoker: ToolInvoker) -> None:
        self._invoker = invoker

    def _call(self, name: str, arguments: dict[str, object]) -> dict[str, Any]:
        return _structured(self._invoker.call(name, arguments))

    def status(self) -> dict[str, Any]:
        payload = self._call("dreamina_cli_status", {})
        ready = payload.get("installed") is True and payload.get("trusted") is True and not payload.get("requires_user_action")
        return {"ready": ready, **payload}

    def account(self) -> dict[str, Any]:
        payload = self._call("dreamina_account", {})
        ready = not payload.get("requires_user_action") and payload.get("exit_code", 0) == 0
        return {"ready": ready, **payload}

    def submit_video(self, request: dict[str, object]) -> dict[str, Any]:
        allowed = {"prompt", "model", "resolution", "ratio", "duration_seconds", "preview", "approved_roots", "web_prerequisite_acknowledged"}
        unknown = set(request) - allowed
        if unknown:
            raise ValueError(f"unsupported submit fields: {sorted(unknown)}")
        preview = request.get("preview")
        if not isinstance(preview, Mapping):
            raise ValueError("submit requires a validated preview object")
        preview_path = str(preview.get("path", ""))
        if preview_path.lower().endswith(".blend"):
            raise ValueError("Blender scene files must never be uploaded to Dreamina")
        approved_roots = request.get("approved_roots", [])
        if approved_roots:
            _require_within_roots(preview_path, approved_roots, "preview")
        arguments: dict[str, object] = {
            "mode": "multimodal2video",
            "prompt": request["prompt"],
            "model": request["model"],
            "video_resolution": request["resolution"],
            "ratio": request["ratio"],
            "duration_seconds": int(request["duration_seconds"]),
            "references": [{"path": preview_path, "role": "reference", "sha256": preview["sha256"]}],
            "approved_roots": list(approved_roots),
        }
        if "web_prerequisite_acknowledged" in request:
            arguments["web_prerequisite_acknowledged"] = bool(request["web_prerequisite_acknowledged"])
        payload = self._call("dreamina_submit_video", arguments)
        submit_id = payload.get("submit_id")
        return {"submit_id": submit_id} if isinstance(submit_id, str) else {}

    def query_task(self, submit_id: str, **options: object) -> dict[str, Any]:
        allowed = {"poll_seconds", "download_dir", "approved_roots"}
        unknown = set(options) - allowed
        if unknown:
            raise ValueError(f"unsupported query fields: {sorted(unknown)}")
        request: dict[str, object] = {"submit_id": submit_id, **options}
        payload = self._call("dreamina_query_task", request)
        result: dict[str, Any] = {"status": _remote_status(payload)}
        artifact = _artifact(payload)
        if artifact is not None:
            result["artifact"] = artifact
        return result

    def invoke(self, action: str, arguments: dict) -> dict:
        if action == "status":
            if arguments:
                raise ValueError("status accepts no arguments")
            return self.status()
        if action == "account":
            if arguments:
                raise ValueError("account accepts no arguments")
            return self.account()
        if action == "quote":
            # Dreamina Design exposes no authoritative quote tool. Never synthesize cost.
            return {"quote_available": False}
        if action == "submit":
            return self.submit_video(arguments)
        if action == "query":
            options = {key: value for key, value in arguments.items() if key != "submit_id"}
            return self.query_task(str(arguments["submit_id"]), **options)
        raise ValueError(f"unsupported Dreamina semantic action: {action}")


__all__ = ["McpDesignClient", "McpToolError", "ToolInvoker", "UserActionRequired"]
