#!/usr/bin/env python3
"""Redacted, bounded MCP Streamable HTTP smoke client for ProcessOn."""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from processon_harness.mcp_proxy import (
    business_authentication_failed,
    parse_streamable_messages,
    tool_names,
)
from processon_harness.secrets import CredentialError, normalize_token


PROTOCOL_VERSION = "2025-06-18"
DEFAULT_ENDPOINT = "https://smart-hd.processon.com/mcp"
SESSION_HEADER = "Mcp-Session-Id"
AUTHORIZATION_ENV = "PROCESSON_MCP_TOKEN"
SUPPORTED_TOOLS = frozenset(
    {"generate_chart", "generate_diagram", "generate_diagram_dsl"}
)
BEARER_PATTERN = re.compile(r"(?i)^Bearer\s+.+$")


class McpSmokeError(RuntimeError):
    """A safe MCP diagnostic error that contains no credentials."""


def authorization_value(raw_token: str) -> str:
    """Normalize a raw ProcessOn token and build the HTTP header value."""
    return f"Bearer {normalize_token(raw_token)}"


def redact(value: str) -> str:
    """Redact a complete bearer value while leaving ordinary strings unchanged."""
    if BEARER_PATTERN.match(value.strip()):
        return "Bearer ***"
    return value


def _redact_payload(value: Any) -> Any:
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, list):
        return [_redact_payload(item) for item in value]
    if isinstance(value, dict):
        return {
            key: "***" if key.lower() == "authorization" else _redact_payload(item)
            for key, item in value.items()
        }
    return value


def encode_rpc(method: str, params: dict, request_id: int | None) -> bytes:
    """Encode one compact JSON-RPC 2.0 request or notification."""
    payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "params": params}
    if request_id is not None:
        payload["id"] = request_id
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def parse_streamable_response(content_type: str, body: bytes) -> dict:
    """Parse either application/json or SSE-framed Streamable HTTP JSON."""
    try:
        return parse_streamable_messages(content_type, body)[-1]
    except RuntimeError as exc:
        raise McpSmokeError("ProcessOn returned an invalid MCP response") from exc


def ensure_tool_success(payload: dict) -> None:
    """Reject protocol and business-level tool failures with safe messages."""
    if "error" in payload:
        raise McpSmokeError("ProcessOn tool returned a JSON-RPC error")
    result = payload.get("result", {})
    if business_authentication_failed([payload]):
        raise McpSmokeError("ProcessOn authentication failed (business response)")
    if result.get("isError") is True:
        raise McpSmokeError("ProcessOn tool reported a business error")


def _request(
    endpoint: str,
    authorization: str,
    body: bytes,
    timeout: float,
    session_id: str | None = None,
    expect_payload: bool = True,
) -> tuple[str, dict]:
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": PROTOCOL_VERSION,
    }
    if session_id:
        headers[SESSION_HEADER] = session_id

    for attempt in range(1, 4):
        request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response_session = response.headers.get(SESSION_HEADER, session_id or "")
                response_body = response.read()
                if not expect_payload or not response_body:
                    return response_session, {}
                return response_session, parse_streamable_response(
                    response.headers.get("Content-Type", "application/json"),
                    response_body,
                )
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                raise McpSmokeError("ProcessOn authentication failed (401)") from None
            if exc.code not in {407, 429, 500, 502, 503, 504} or attempt == 3:
                raise McpSmokeError(f"ProcessOn MCP HTTP failure ({exc.code})") from None
        except (TimeoutError, urllib.error.URLError) as exc:
            if attempt == 3:
                reason = type(getattr(exc, "reason", exc)).__name__
                raise McpSmokeError(f"ProcessOn MCP connection failed ({reason})") from None
        time.sleep((0.25 * (2 ** (attempt - 1))) + random.uniform(0.0, 0.1))
    raise McpSmokeError("ProcessOn MCP request exhausted its retry budget")


def initialize(
    endpoint: str,
    authorization: str,
    timeout: float = 30.0,
) -> tuple[str, dict]:
    """Initialize one MCP session and send the initialized notification."""
    params = {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {},
        "clientInfo": {"name": "codex-processon-smoke", "version": "0.1.0"},
    }
    session_id, payload = _request(
        endpoint,
        authorization,
        encode_rpc("initialize", params, 1),
        timeout,
    )
    if "error" in payload:
        raise McpSmokeError("ProcessOn MCP initialize returned a JSON-RPC error")
    negotiated = payload.get("result", {}).get("protocolVersion")
    if not negotiated:
        raise McpSmokeError("ProcessOn MCP initialize omitted protocolVersion")
    _request(
        endpoint,
        authorization,
        encode_rpc("notifications/initialized", {}, None),
        timeout,
        session_id=session_id,
        expect_payload=False,
    )
    return session_id, payload


def list_tools(
    endpoint: str,
    authorization: str,
    session_id: str,
    timeout: float = 30.0,
) -> dict:
    """List tools for an initialized session."""
    _, payload = _request(
        endpoint,
        authorization,
        encode_rpc("tools/list", {}, 2),
        timeout,
        session_id=session_id,
    )
    if "error" in payload:
        raise McpSmokeError("ProcessOn tools/list returned a JSON-RPC error")
    return payload


def call_tool(
    endpoint: str,
    authorization: str,
    session_id: str,
    name: str,
    prompt: str,
    timeout: float = 180.0,
) -> dict:
    """Call one documented ProcessOn prompt-only tool."""
    if name not in SUPPORTED_TOOLS:
        raise ValueError(f"unsupported ProcessOn tool: {name}")
    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    _, payload = _request(
        endpoint,
        authorization,
        encode_rpc(
            "tools/call",
            {"name": name, "arguments": {"prompt": prompt}},
            3,
        ),
        timeout,
        session_id=session_id,
    )
    ensure_tool_success(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--list-tools", action="store_true")
    parser.add_argument("--call", choices=tuple(sorted(SUPPORTED_TOOLS)))
    parser.add_argument("--prompt")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    raw_token = os.environ.get(AUTHORIZATION_ENV, "")
    try:
        authorization = authorization_value(raw_token)
    except CredentialError:
        print(
            f"{AUTHORIZATION_ENV} must contain a raw ProcessOn token",
            file=sys.stderr,
        )
        return 2

    try:
        session_id, initialized = initialize(args.endpoint, authorization, args.timeout)
        tools = list_tools(args.endpoint, authorization, session_id, args.timeout)
        summary: dict[str, Any] = {
            "protocolVersion": initialized["result"]["protocolVersion"],
            "tools": tool_names(tools),
        }
        if args.call:
            if not args.prompt:
                parser.error("--prompt is required with --call")
            summary["call"] = _redact_payload(
                call_tool(args.endpoint, authorization, session_id, args.call, args.prompt, 180.0)
            )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except (McpSmokeError, ValueError, json.JSONDecodeError) as exc:
        print(redact(str(exc)), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
