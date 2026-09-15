"""Plugin-owned MCP adapter for the guarded Codex Blender Harness."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import uuid
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

from .runtime import build_registry
from .transport import Endpoint, send_request


MCP_PROTOCOL_VERSION = "2025-06-18"
HARNESS_PROTOCOL_VERSION = "codex-blender/v1"
BLENDER_DOWNLOAD_URL = "https://www.blender.org/download/"
ENVELOPE_PROPERTIES = {
    "_requestId": {"type": "string", "minLength": 1, "description": "Stable request id for replay safety"},
    "_transactionId": {"type": "string", "minLength": 1, "description": "Harness milestone transaction id"},
    "_expectedSceneRevision": {"type": "integer", "minimum": 0},
    "_authorization": {"type": "string", "minLength": 1, "description": "Action-bound Harness authorization claim"},
}
CONTROL_TOOLS = {
    "blender_transaction_begin": "transaction.begin",
    "blender_transaction_commit": "transaction.commit",
    "blender_transaction_rollback": "transaction.rollback",
    "blender_authorize": "session.authorize",
}


class McpAdapterError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def command_tool_name(command: str) -> str:
    """Return a stable MCP-safe name which remains reversible by inspection."""
    return "blender_" + command.replace(".", "_")


def _static_registry():
    bpy_metadata = SimpleNamespace(
        app=SimpleNamespace(version=(5, 2, 1), background=False, version_string="catalog"),
    )
    # Connector is the registered superset (it adds official_uploader.*).
    # Runtime availability and the Harness still decide whether a given tool can execute.
    return build_registry(
        bpy_metadata,
        runtime_mode="connector",
        approved_output_root=Path(tempfile.gettempdir()) / "codex-blender-mcp-catalog",
    )


def _command_tool(registry, capability: dict) -> dict:
    command = capability["command"]
    detail = registry.describe_capability({"id": command})
    schema = deepcopy(detail["input"] or {"type": "object", "properties": {}, "additionalProperties": False})
    schema.setdefault("properties", {}).update(deepcopy(ENVELOPE_PROPERTIES))
    if capability["risk"] != "read":
        required = list(schema.get("required", []))
        if "_transactionId" not in required:
            required.append("_transactionId")
        schema["required"] = required
    schema["additionalProperties"] = False
    requirements = detail.get("context", {}).get("requirements", [])
    description = f"Codex Blender Harness command `{command}`. Risk: {capability['risk']}; maturity: {detail['maturity']}."
    if requirements:
        description += " Requirements: " + "; ".join(requirements)
    return {
        "name": command_tool_name(command),
        "title": command,
        "description": description,
        "inputSchema": schema,
        "outputSchema": {"type": "object"},
        "annotations": {
            "readOnlyHint": capability["risk"] == "read",
            "destructiveHint": capability["risk"] == "gated",
            "idempotentHint": capability["risk"] == "read",
            "openWorldHint": command.startswith("official_uploader."),
        },
        "_meta": {"codexBlenderCommand": command, "risk": capability["risk"], "maturity": detail["maturity"]},
    }


def build_tool_catalog(*, registry=None, plugin_root: Path | None = None) -> list[dict]:
    registry = registry or _static_registry()
    plugin_root = Path(plugin_root or Path(__file__).resolve().parents[2])
    tools = [
        {
            "name": "blender_getting_started",
            "title": "Install and connect Blender",
            "description": "Show the official Blender download and illustrated Codex Blender MCP setup guide.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            "outputSchema": {"type": "object"},
            "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
        },
        {
            "name": "blender_connection_status",
            "title": "Blender MCP connection status",
            "description": "Check whether the plugin-owned MCP adapter can reach one live guarded Harness session.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            "outputSchema": {"type": "object"},
            "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
        },
    ]
    control_schema = {
        "type": "object",
        "properties": {
            "_requestId": deepcopy(ENVELOPE_PROPERTIES["_requestId"]),
            "_transactionId": deepcopy(ENVELOPE_PROPERTIES["_transactionId"]),
        },
        "required": ["_transactionId"],
        "additionalProperties": False,
    }
    for name, command in CONTROL_TOOLS.items():
        schema = deepcopy(control_schema)
        if command == "session.authorize":
            schema = {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "minLength": 1},
                    "requestId": {"type": "string", "minLength": 1},
                    "userConfirmed": {"type": "boolean"},
                    "ttlSeconds": {"type": "integer", "minimum": 1, "maximum": 300},
                    "_requestId": deepcopy(ENVELOPE_PROPERTIES["_requestId"]),
                    "_transactionId": deepcopy(ENVELOPE_PROPERTIES["_transactionId"]),
                },
                "required": ["action", "requestId", "userConfirmed", "_transactionId"],
                "additionalProperties": False,
            }
        tools.append({
            "name": name, "title": command,
            "description": f"Guarded Harness lifecycle operation `{command}`.",
            "inputSchema": schema, "outputSchema": {"type": "object"},
            "annotations": {"readOnlyHint": False, "destructiveHint": command == "transaction.rollback",
                            "idempotentHint": False, "openWorldHint": False},
            "_meta": {"codexBlenderControl": command},
        })
    command_tools = [_command_tool(registry, capability) for capability in registry.capabilities()]
    all_names = [tool["name"] for tool in tools] + [tool["name"] for tool in command_tools]
    duplicates = sorted({name for name in all_names if all_names.count(name) > 1})
    if duplicates:
        raise McpAdapterError(
            "MCP_TOOL_NAME_COLLISION",
            "Harness command names do not map uniquely to MCP tools: " + ", ".join(duplicates),
        )
    tools.extend(command_tools)
    return tools


def _process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _endpoint(descriptor: dict) -> Endpoint:
    address = descriptor["address"]
    if descriptor["transport"] == "tcp":
        address = (str(address[0]), int(address[1]))
    return Endpoint(str(descriptor["transport"]), address)


class DescriptorBridge:
    """Load one private Harness descriptor and forward closed requests."""

    def __init__(self, *, descriptor_path: Path, sender=send_request, process_alive=_process_alive):
        self.descriptor_path = Path(descriptor_path)
        self.sender = sender
        self.process_alive = process_alive

    def _load(self) -> dict:
        path = self.descriptor_path
        if path.is_symlink():
            raise McpAdapterError("UNSAFE_DESCRIPTOR", "Harness descriptor must not be a symlink")
        try:
            stat = path.stat()
        except FileNotFoundError as error:
            raise McpAdapterError("BLENDER_NOT_CONNECTED", "No active Codex Blender Harness session") from error
        if os.name != "nt" and stat.st_mode & 0o077:
            raise McpAdapterError("UNSAFE_DESCRIPTOR", "Harness descriptor permissions are not private")
        try:
            descriptor = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise McpAdapterError("INVALID_DESCRIPTOR", "Harness descriptor is unreadable") from error
        required = {"protocolVersion", "sessionId", "transport", "address", "token", "pid"}
        if required.difference(descriptor) or descriptor.get("protocolVersion") != HARNESS_PROTOCOL_VERSION:
            raise McpAdapterError("INVALID_DESCRIPTOR", "Harness descriptor has an incompatible contract")
        if not self.process_alive(int(descriptor["pid"])):
            raise McpAdapterError("BLENDER_NOT_CONNECTED", "Harness process is no longer running")
        return descriptor

    def status(self) -> dict:
        descriptor = self._load()
        response = self.call("session.status", {}, request_id=str(uuid.uuid4()), transaction_id="mcp-status")
        if response.get("status") != "succeeded":
            raise McpAdapterError("BLENDER_NOT_CONNECTED", "Harness session did not answer its status probe")
        status = {
            "connected": True,
            "sessionId": descriptor["sessionId"],
            "transport": descriptor["transport"],
            "processId": descriptor["pid"],
            "sceneRevision": response.get("sceneRevision"),
        }
        if isinstance(response.get("result"), dict):
            status.update({key: value for key, value in response["result"].items()
                           if key not in {"token", "authorization"}})
        return status

    def call(self, command: str, arguments: dict, *, request_id: str | None = None,
             transaction_id: str | None = None, expected_scene_revision: int | None = None,
             authorization: str | None = None) -> dict:
        descriptor = self._load()
        payload = {
            "protocolVersion": HARNESS_PROTOCOL_VERSION,
            "sessionId": descriptor["sessionId"],
            "requestId": request_id or str(uuid.uuid4()),
            "transactionId": transaction_id or "mcp-read",
            "command": command,
            "arguments": arguments,
        }
        if expected_scene_revision is not None:
            payload["expectedSceneRevision"] = expected_scene_revision
        if authorization is not None:
            payload["authorization"] = authorization
        return self.sender(_endpoint(descriptor), descriptor["token"], payload)


def discover_bridge(runtime_dir: Path | None = None) -> DescriptorBridge:
    explicit = os.environ.get("CODEX_BLENDER_DESCRIPTOR")
    if explicit:
        return DescriptorBridge(descriptor_path=Path(explicit))
    root = Path(runtime_dir or os.environ.get("CODEX_BLENDER_RUNTIME_DIR") or
                (Path(tempfile.gettempdir()) / "codex-blender"))
    live = []
    for path in sorted(root.glob("*.json")) if root.is_dir() else []:
        bridge = DescriptorBridge(descriptor_path=path)
        try:
            bridge.status()
            live.append(bridge)
        except McpAdapterError:
            continue
    if not live:
        raise McpAdapterError("BLENDER_NOT_CONNECTED", "No active Codex Blender Harness session")
    if len(live) != 1:
        raise McpAdapterError("AMBIGUOUS_SESSION", "Multiple Blender sessions are active; set CODEX_BLENDER_DESCRIPTOR")
    return live[0]


class McpAdapter:
    def __init__(self, *, bridge=None, plugin_root: Path | None = None, registry=None):
        self.plugin_root = Path(plugin_root or Path(__file__).resolve().parents[2]).resolve()
        self._bridge = bridge
        self.registry = registry or _static_registry()
        self.tools = build_tool_catalog(registry=self.registry, plugin_root=self.plugin_root)
        self.tools_by_name = {tool["name"]: tool for tool in self.tools}

    def list_tools(self, *, cursor: str | None = None, limit: int = 50) -> dict:
        if cursor is None:
            offset = 0
        elif isinstance(cursor, str) and cursor.startswith("offset:") and cursor[7:].isdigit():
            offset = int(cursor[7:])
        else:
            raise McpAdapterError("INVALID_CURSOR", "tools/list cursor is invalid")
        if offset < 0 or offset > len(self.tools):
            raise McpAdapterError("INVALID_CURSOR", "tools/list cursor is out of range")
        page = self.tools[offset:offset + limit]
        result = {"tools": page}
        if offset + limit < len(self.tools):
            result["nextCursor"] = f"offset:{offset + limit}"
        return result

    def _active_bridge(self):
        return self._bridge or discover_bridge()

    def getting_started(self) -> dict:
        executable = shutil.which("blender")
        if executable is None and sys.platform == "darwin":
            candidate = Path("/Applications/Blender.app/Contents/MacOS/Blender")
            executable = str(candidate) if candidate.is_file() else None
        images = [
            ("Open Edit > Preferences", "assets/getting-started/blender-preferences-menu.png"),
            ("Enable PartMe Blender MCP", "assets/getting-started/blender-enable-mcp-addon.png"),
        ]
        return {
            "blenderInstalled": executable is not None,
            "blenderExecutable": executable,
            "downloadUrl": BLENDER_DOWNLOAD_URL,
            "copy": {
                "zhCN": "还没有 Blender？下载安装包\n\n打开 Blender，在 偏好设置 > 插件 中启用 MCP 插件，然后在 N 面板中点击 Start MCP Server。",
                "en": "No Blender yet? Download the installer. Open Blender, enable the MCP Add-on in Preferences > Add-ons, then press N and click Start MCP Server.",
            },
            "addonName": "PartMe Blender MCP",
            "steps": [
                "Download Blender from the official Blender website and launch it once.",
                "Install partme-blender-mcp-addon-0.1.1.zip from Edit > Preferences > Add-ons > Install from Disk.",
                "Enable PartMe Blender MCP.",
                "In the 3D View press N, open Codex, choose approved output/assets, and click Start MCP Server.",
            ],
            "screenshots": [{"title": title, "path": str((self.plugin_root / relative).resolve())}
                            for title, relative in images],
        }

    @staticmethod
    def _result(payload: dict, *, is_error: bool = False) -> dict:
        return {
            "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, separators=(",", ":"))}],
            "structuredContent": payload,
            "isError": is_error,
        }

    def _error(self, error: McpAdapterError) -> dict:
        payload = {"status": "failed", "error": {"code": error.code, "message": str(error)}}
        if error.code == "BLENDER_NOT_CONNECTED":
            payload["gettingStarted"] = self.getting_started()
        return self._result(payload, is_error=True)

    def call_tool(self, name: str, arguments: dict | None) -> dict:
        arguments = dict(arguments or {}) if isinstance(arguments or {}, dict) else None
        if arguments is None:
            return self._error(McpAdapterError("INVALID_ARGUMENT", "tool arguments must be an object"))
        if name == "blender_getting_started":
            if arguments:
                return self._error(McpAdapterError("INVALID_ARGUMENT", "getting started accepts no arguments"))
            return self._result(self.getting_started())
        if name == "blender_connection_status":
            if arguments:
                return self._error(McpAdapterError("INVALID_ARGUMENT", "connection status accepts no arguments"))
            try:
                return self._result(self._active_bridge().status())
            except McpAdapterError as error:
                return self._error(error)
        tool = self.tools_by_name.get(name)
        if tool is None:
            return self._error(McpAdapterError("UNKNOWN_TOOL", f"unknown MCP tool: {name}"))
        schema = tool["inputSchema"]
        unknown = sorted(set(arguments).difference(schema.get("properties", {})))
        missing = sorted(set(schema.get("required", [])).difference(arguments))
        if unknown or missing:
            detail = f"unknown fields: {unknown}" if unknown else f"missing fields: {missing}"
            return self._error(McpAdapterError("INVALID_ARGUMENT", detail))
        request_id = arguments.pop("_requestId", None)
        transaction_id = arguments.pop("_transactionId", None)
        expected_revision = arguments.pop("_expectedSceneRevision", None)
        authorization = arguments.pop("_authorization", None)
        command = tool.get("_meta", {}).get("codexBlenderCommand") or tool.get("_meta", {}).get("codexBlenderControl")
        try:
            bridge = self._active_bridge()
            risk = tool.get("_meta", {}).get("risk")
            if expected_revision is None and risk in {"standard", "gated"}:
                expected_revision = bridge.status().get("sceneRevision")
            response = bridge.call(
                command, arguments,
                request_id=request_id,
                transaction_id=transaction_id,
                expected_scene_revision=expected_revision,
                authorization=authorization,
            )
        except McpAdapterError as error:
            return self._error(error)
        failed = response.get("status") == "failed" or "error" in response
        return self._result(response, is_error=failed)


def _jsonrpc_error(request_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def serve_stdio(input_stream=None, output_stream=None, adapter: McpAdapter | None = None) -> int:
    input_stream = input_stream or sys.stdin
    output_stream = output_stream or sys.stdout
    adapter = adapter or McpAdapter()
    for raw in input_stream:
        try:
            request = json.loads(raw)
            if not isinstance(request, dict):
                raise ValueError("request must be an object")
            request_id = request.get("id")
            method = request.get("method")
            if method == "notifications/initialized":
                continue
            if method == "initialize":
                result = {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "codex-blender", "title": "Codex Blender", "version": "0.3.0"},
                }
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                params = request.get("params") or {}
                if not isinstance(params, dict) or set(params).difference({"cursor"}):
                    raise McpAdapterError("INVALID_CURSOR", "invalid tools/list parameters")
                try:
                    result = adapter.list_tools(cursor=params.get("cursor"))
                except McpAdapterError:
                    response = _jsonrpc_error(request_id, -32602, "invalid tools/list cursor")
                    output_stream.write(json.dumps(response, separators=(",", ":")) + "\n")
                    output_stream.flush()
                    continue
            elif method == "tools/call":
                params = request.get("params")
                if not isinstance(params, dict) or not isinstance(params.get("name"), str):
                    response = _jsonrpc_error(request_id, -32602, "invalid tools/call parameters")
                    output_stream.write(json.dumps(response, separators=(",", ":")) + "\n")
                    output_stream.flush()
                    continue
                result = adapter.call_tool(params["name"], params.get("arguments", {}))
            else:
                response = _jsonrpc_error(request_id, -32601, "method not found")
                output_stream.write(json.dumps(response, separators=(",", ":")) + "\n")
                output_stream.flush()
                continue
            if request_id is not None:
                output_stream.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result},
                                               separators=(",", ":"), ensure_ascii=False) + "\n")
                output_stream.flush()
        except McpAdapterError:
            output_stream.write(json.dumps(_jsonrpc_error(None, -32602, "invalid parameters"), separators=(",", ":")) + "\n")
            output_stream.flush()
        except (json.JSONDecodeError, ValueError):
            output_stream.write(json.dumps(_jsonrpc_error(None, -32700, "parse error"), separators=(",", ":")) + "\n")
            output_stream.flush()
        except Exception:
            output_stream.write(json.dumps(_jsonrpc_error(None, -32603, "internal error"), separators=(",", ":")) + "\n")
            output_stream.flush()
    return 0
