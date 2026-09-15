"""Dependency-free stdio MCP server for approved Dreamina workflows."""

from __future__ import annotations

import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Mapping

from scripts.approval_guard import ApprovalGuard
from scripts.account_service import AccountService
from scripts.auth_service import AuthFlowStore, AuthService
from scripts.diagnostic_service import DiagnosticService
from scripts.dreamina_adapter import DreaminaAdapter, DreaminaAdapterError
from scripts.video_project_mcp import project_tool_definitions
from scripts.environment_service import EnvironmentService
from scripts.image_service import ImageService, build_request_fingerprint
from scripts.native_approval import NativeApprovalProvider
from scripts.reference_policy import ReferencePolicy
from scripts.session_service import SessionService
from scripts.task_service import TaskService
from scripts.trusted_cli import TrustedCliError, TrustedCliStore
from scripts.video_service import VideoService, build_video_request_fingerprint


PROTOCOL_VERSION = "2025-06-18"


def _tool_definitions() -> list[dict[str, Any]]:
    tools = [
        {
            "name": "dreamina_capability_snapshot",
            "description": "Read the verified Dreamina CLI capability snapshot without generation.",
            "inputSchema": {"type": "object", "properties": {"detail": {"type": "string", "enum": ["summary", "full"], "default": "summary"}}, "additionalProperties": False},
            "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
        },
        _tool("dreamina_cli_status", "Inspect Dreamina CLI installation, version, and command help.", {"command": {"type":"string","enum":["login","relogin","logout","user_credit","text2image","image2image","image_upscale","text2video","image2video","frames2video","multiframe2video","multimodal2video","query_result","list_task","session","version"]}, "detail":{"type":"string","enum":["summary","full"],"default":"summary"}}, read_only=True),
        _tool("dreamina_cli_install_or_upgrade", "Install or upgrade Dreamina CLI from the fixed official HTTPS installer.", {"action":{"type":"string","enum":["install","upgrade"]}}, required=["action"], destructive=True),
        _tool("dreamina_auth", "Run a typed Dreamina login, login check, relogin, or logout workflow.", {"action":{"type":"string","enum":["login","login_headless","check_login","relogin","logout"]},"flow_id":{"type":"string","minLength":16,"maxLength":128},"poll_seconds":{"type":"integer","minimum":0,"maximum":300,"default":0}}, required=["action"], destructive=True),
        _tool("dreamina_account", "Read redacted Dreamina account and credit readiness.", {}, read_only=True),
        {
            "name": "dreamina_submit_image",
            "description": "Submit one explicitly approved paid Dreamina image request and persist recovery state.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["text2image", "image2image", "image_upscale"]},
                    "prompt": {"type": "string", "minLength": 1, "maxLength": 4000},
                    "model": {"type": "string"},
                    "resolution_type": {"type": "string"},
                    "count": {"type": "integer", "minimum": 1, "maximum": 10},
                    "ratio": {"type": "string"},
                    "references": {"type": "array", "items": {"type": "object"}, "maxItems": 10},
                    "approved_roots": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["mode", "resolution_type"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True},
        },
        {
            "name": "dreamina_submit_video",
            "description": "Submit one explicitly approved paid Dreamina video request and persist recovery state.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["text2video", "image2video", "frames2video", "multiframe2video", "multimodal2video"]},
                    "prompt": {"type": "string", "maxLength": 4000},
                    "model": {"type": "string"},
                    "video_resolution": {"type": "string"},
                    "ratio": {"type": "string"},
                    "duration_seconds": {"type": "integer", "minimum": 1, "maximum": 30},
                    "references": {"type": "array", "items": {"type": "object"}, "maxItems": 50},
                    "transitions": {"type":"array","items":{"type":"object","properties":{"prompt":{"type":"string","minLength":1,"maxLength":1000},"duration_seconds":{"type":"integer","minimum":1,"maximum":8}},"required":["prompt","duration_seconds"],"additionalProperties":False},"maxItems":19},
                    "approved_roots": {"type": "array", "items": {"type": "string"}},
                    "web_prerequisite_acknowledged": {"type": "boolean"},
                },
                "required": ["mode", "prompt", "video_resolution"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True},
        },
        _tool("dreamina_query_task", "Query a Dreamina submit ID and optionally download into an approved root without resubmitting.", {"submit_id":{"type":"string","pattern":"^[A-Za-z0-9_-]{1,128}$"},"poll_seconds":{"type":"integer","minimum":0,"maximum":300,"default":0},"download_dir":{"type":"string"},"approved_roots":{"type":"array","items":{"type":"string"},"maxItems":10}}, required=["submit_id"], read_only=False),
        _tool("dreamina_list_tasks", "List Dreamina tasks with bounded documented filters.", {"filters":{"type":"object","properties":{"gen_status":{"type":"string"},"aigc_type":{"type":"string"},"session":{"type":"string"}},"additionalProperties":False},"limit":{"type":"integer","minimum":1,"maximum":100,"default":20}}, read_only=True),
        _tool("dreamina_session", "Create, list, search, rename, or delete a Dreamina Session.", {"action":{"type":"string","enum":["create","list","search","rename","delete"]},"name":{"type":"string","minLength":1,"maxLength":200},"session_id":{"type":"string","pattern":"^[A-Za-z0-9_-]{1,128}$"},"query":{"type":"string","minLength":1,"maxLength":200}}, required=["action"], destructive=True),
        _tool("dreamina_diagnose", "Read bounded redacted Dreamina CLI logs from the fixed log directory.", {"command":{"type":"string","maxLength":4096},"error":{"type":"string","maxLength":16384},"submit_id":{"type":"string","pattern":"^[A-Za-z0-9_-]{1,128}$"},"since_minutes":{"type":"integer","minimum":1,"maximum":1440,"default":60},"max_files":{"type":"integer","minimum":1,"maximum":10,"default":3}}, required=["command","error"], read_only=True),
    ]
    # The ten additive video-project tools extend the eleven legacy tools.
    return [*tools, *project_tool_definitions()]


def _tool(name: str, description: str, properties: Mapping[str, Any], *, required: list[str] | None = None, read_only: bool = False, destructive: bool = False) -> dict[str, Any]:
    schema={"type":"object","properties":dict(properties),"additionalProperties":False}
    if required: schema["required"]=required
    return {"name":name,"description":description,"inputSchema":schema,"annotations":{"readOnlyHint":read_only,"destructiveHint":destructive,"idempotentHint":read_only,"openWorldHint":False}}


class DreaminaMcpTools:
    """Tool handlers; paid handlers are protected by Codex approval_mode=prompt."""

    def __init__(self, *, state_root: Path | None = None, approval_provider: Any | None = None) -> None:
        self.state_root = state_root or (Path.home() / ".local" / "share" / "codex-dreamina-design")
        self.approval_provider = approval_provider or NativeApprovalProvider()
        self.auth_flow_store = AuthFlowStore()

    def call(self, name: str, args: Mapping[str, Any]) -> dict[str, Any]:
        definitions={tool["name"]:tool for tool in _tool_definitions()}
        if name not in definitions: raise ValueError(f"unknown tool: {name}")
        _validate_schema(args,definitions[name]["inputSchema"],path="arguments")
        if name == "dreamina_capability_snapshot":
            with _adapter(args) as adapter:
                snapshot = adapter.capability_snapshot()
                if args.get("detail", "summary") == "full":
                    return snapshot
                return {
                    "cli_version": snapshot["cli_version"],
                    "cli_commit": snapshot.get("cli_commit"),
                    "modes": snapshot.get("modes", []),
                    "model_count": len(snapshot.get("models", [])),
                    "captured_at": snapshot["captured_at"],
                }
        if name == "dreamina_cli_install_or_upgrade":
            service=EnvironmentService(None,trust_store=TrustedCliStore())
            return service.install_or_upgrade(str(args["action"]),approval_provider=self.approval_provider)
        if name == "dreamina_diagnose":
            return DiagnosticService().diagnose(command=str(args["command"]),error=str(args["error"]),submit_id=args.get("submit_id"),since_minutes=int(args.get("since_minutes",60)),max_files=int(args.get("max_files",3)))
        if name == "dreamina_cli_status":
            try:
                with _adapter(args) as adapter:
                    return EnvironmentService(adapter).status(command=args.get("command"),detail=str(args.get("detail","summary")))
            except TrustedCliError as exc:
                return {"installed":False,"trusted":False,"requires_user_action":"install_or_enroll","message":str(exc)}
        if name in {"dreamina_cli_status","dreamina_account","dreamina_auth","dreamina_query_task","dreamina_list_tasks","dreamina_session"}:
            with _adapter(args) as adapter:
                account=AccountService(adapter)
                if name == "dreamina_account": return account.user_credit()
                if name == "dreamina_auth": return AuthService(adapter,account,self.approval_provider,self.auth_flow_store).execute(str(args["action"]),flow_id=args.get("flow_id"),poll_seconds=int(args.get("poll_seconds",0)))
                if name == "dreamina_query_task":
                    download_dir=_approved_download_dir(args)
                    if download_dir: self.approval_provider.confirm({"operation":"dreamina-download","submit_id":str(args["submit_id"]),"download_dir":download_dir})
                    return TaskService(adapter).query(str(args["submit_id"]),poll_seconds=int(args.get("poll_seconds",0)),download_dir=download_dir)
                if name == "dreamina_list_tasks": return TaskService(adapter).list_tasks(args.get("filters",{}),limit=int(args.get("limit",20)))
                return SessionService(adapter,self.approval_provider).execute(str(args["action"]),name=args.get("name"),session_id=args.get("session_id"),query=args.get("query"))
        if name == "dreamina_submit_image":
            return self._submit_image(args)
        if name == "dreamina_submit_video":
            return self._submit_video(args)
        raise ValueError(f"unknown tool: {name}")

    def _submit_image(self, args: Mapping[str, Any]) -> dict[str, Any]:
        with _adapter(args) as adapter:
            snapshot = adapter.capability_snapshot()
            policy = _reference_policy(args)
            session_id, guard = self._approval_context("image")
            service = ImageService(snapshot=snapshot, ledger_dir=self.state_root / "operations", reference_policy=policy)
            request = service.build_request(
                mode=str(args["mode"]), prompt=str(args.get("prompt") or "") or None, model=str(args.get("model") or "") or None,
                resolution_type=str(args["resolution_type"]), count=int(args.get("count", 1)),
                ratio=args.get("ratio"), references=list(args.get("references", [])),
            )
            scope = _scope(request)
            approver = self.approval_provider.confirm(request)
            approval_id = guard.record_approval(session_id, request=request, receipt=_approved_receipt(build_request_fingerprint(request), scope, approver))
            return service.submit(request, adapter=adapter, approval_guard=guard, session_id=session_id, approval_id=approval_id)

    def _submit_video(self, args: Mapping[str, Any]) -> dict[str, Any]:
        with _adapter(args) as adapter:
            snapshot = adapter.capability_snapshot()
            policy = _reference_policy(args)
            session_id, guard = self._approval_context("video")
            service = VideoService(snapshot=snapshot, ledger_dir=self.state_root / "operations", reference_policy=policy)
            if args.get("web_prerequisite_acknowledged") is True:
                service.record_web_prerequisite_acknowledgement()
            request = service.build_request(
                mode=str(args["mode"]), prompt=str(args.get("prompt", "")), model=str(args.get("model")) if args.get("model") is not None else None,
                video_resolution=str(args["video_resolution"]), ratio=args.get("ratio"),
                duration_seconds=int(args["duration_seconds"]) if args.get("duration_seconds") is not None else None,
                references=list(args.get("references", [])), transitions=list(args.get("transitions", [])),
            )
            scope = _scope(request)
            approver = self.approval_provider.confirm(request)
            approval_id = guard.record_approval(session_id, request=request, receipt=_approved_receipt(build_video_request_fingerprint(request), scope, approver), fingerprint_builder=build_video_request_fingerprint)
            return service.submit(request, adapter=adapter, approval_guard=guard, session_id=session_id, approval_id=approval_id, web_prerequisite_cleared=bool(args.get("web_prerequisite_acknowledged")))

    def _approval_context(self, kind: str) -> tuple[str, ApprovalGuard]:
        guard = ApprovalGuard(root=self.state_root / "approvals")
        session_id = guard.create_session(label=f"mcp-{kind}-{uuid.uuid4().hex[:12]}")
        return session_id, guard


class _AdapterContext:
    def __init__(self, adapter: DreaminaAdapter) -> None: self.adapter = adapter
    def __enter__(self) -> DreaminaAdapter: return self.adapter
    def __exit__(self, *_): self.adapter.close()


def _adapter(args: Mapping[str, Any]) -> _AdapterContext:
    trusted = TrustedCliStore().load()
    return _AdapterContext(DreaminaAdapter(cli_command=trusted["cli_path"], trusted_binary_sha256=trusted["cli_sha256"]))


def _reference_policy(args: Mapping[str, Any]) -> ReferencePolicy | None:
    references = list(args.get("references", []))
    if not references:
        return None
    roots = [Path(value) for value in args.get("approved_roots", [])]
    if not roots:
        raise ValueError("approved_roots is required when references are uploaded")
    return ReferencePolicy(approved_roots=roots)


def _approved_download_dir(args: Mapping[str, Any]) -> str | None:
    value=args.get("download_dir")
    if value is None: return None
    roots=[Path(root).resolve() for root in args.get("approved_roots",[])]
    if not roots: raise ValueError("approved_roots is required with download_dir")
    destination=Path(str(value)).resolve()
    if not any(destination==root or root in destination.parents for root in roots): raise ValueError("download_dir escapes approved roots")
    if destination.is_symlink(): raise ValueError("download_dir must not be a symlink")
    if destination.is_dir() and any(destination.iterdir()): raise ValueError("download_dir must be empty to verify newly downloaded artifacts")
    destination.mkdir(parents=True,exist_ok=True)
    return str(destination)


def _validate_schema(value: Any, schema: Mapping[str, Any], *, path: str) -> None:
    expected=schema.get("type")
    if expected=="object":
        if not isinstance(value,Mapping): raise ValueError(f"{path} must be an object")
        properties=schema.get("properties",{})
        unknown=set(value)-set(properties)
        if unknown and schema.get("additionalProperties") is False: raise ValueError(f"{path} has unknown properties: {sorted(unknown)}")
        for required in schema.get("required",[]):
            if required not in value: raise ValueError(f"{path}.{required} is required")
        for key,item in value.items():
            if key in properties: _validate_schema(item,properties[key],path=f"{path}.{key}")
    elif expected=="array":
        if not isinstance(value,list): raise ValueError(f"{path} must be an array")
        if len(value)>int(schema.get("maxItems",len(value))): raise ValueError(f"{path} has too many items")
        for index,item in enumerate(value): _validate_schema(item,schema.get("items",{}),path=f"{path}[{index}]")
    elif expected=="string":
        if not isinstance(value,str): raise ValueError(f"{path} must be a string")
        if len(value)<int(schema.get("minLength",0)) or len(value)>int(schema.get("maxLength",len(value))): raise ValueError(f"{path} length is invalid")
        if "pattern" in schema and re.fullmatch(str(schema["pattern"]),value) is None: raise ValueError(f"{path} format is invalid")
    elif expected=="integer":
        if isinstance(value,bool) or not isinstance(value,int): raise ValueError(f"{path} must be an integer")
        if value<int(schema.get("minimum",value)) or value>int(schema.get("maximum",value)): raise ValueError(f"{path} is outside allowed range")
    elif expected=="boolean" and not isinstance(value,bool): raise ValueError(f"{path} must be a boolean")
    if "enum" in schema and value not in schema["enum"]: raise ValueError(f"{path} is not an allowed value")


def _scope(request: Mapping[str, Any]) -> dict[str, Any]:
    values = {
        "count": int(request.get("count", 1)), "model": request.get("model"),
        "resolution": request.get("resolution_type", request.get("video_resolution")),
        "ratio": request.get("ratio"), "duration_seconds": request.get("duration_seconds"),
    }
    return {key: value for key, value in values.items() if value is not None}


def _approved_receipt(fingerprint: str, scope: Mapping[str, Any], approver: str) -> dict[str, Any]:
    return {"request_fingerprint": fingerprint, "acknowledged_cost": "credits", "acknowledged_scope": dict(scope), "approver": approver}


def _response(request_id: Any, result: Any = None, error: dict | None = None) -> dict:
    payload = {"jsonrpc": "2.0", "id": request_id}
    payload["error" if error else "result"] = error or result
    return payload


def _handle(message: Mapping[str, Any], tools: DreaminaMcpTools) -> dict | None:
    method = message.get("method")
    request_id = message.get("id")
    if method == "initialize":
        return _response(request_id, {"protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {}}, "serverInfo": {"name": "dreamina-design", "version": "0.4.0"}})
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return _response(request_id, {"tools": _tool_definitions()})
    if method == "tools/call":
        params = message.get("params") or {}
        try:
            structured = tools.call(str(params.get("name", "")), params.get("arguments") or {})
            return _response(request_id, {"content": [{"type": "text", "text": json.dumps(structured, ensure_ascii=False)}], "structuredContent": structured, "isError": False})
        except Exception as exc:
            error_type=type(exc).__name__
            requires_user_action=isinstance(exc,(PermissionError,TrustedCliError))
            query_retryable=str(params.get("name", "")) == "dreamina_query_task" and isinstance(exc, DreaminaAdapterError)
            structured={"error_type":error_type,"message":str(exc),"retryable":query_retryable,"requires_user_action":requires_user_action,"next_action":"request_user_action" if requires_user_action else "query_same_submit_id" if query_retryable else "correct_request"}
            return _response(request_id, {"content": [{"type": "text", "text": json.dumps(structured, ensure_ascii=False)}], "structuredContent": structured, "isError": True})
    if request_id is not None:
        return _response(request_id, error={"code": -32601, "message": f"method not found: {method}"})
    return None


def main() -> int:
    tools = DreaminaMcpTools()
    for line in sys.stdin:
        try:
            message = json.loads(line)
            response = _handle(message, tools)
        except Exception as exc:
            response = _response(None, error={"code": -32700, "message": str(exc)})
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
