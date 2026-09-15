"""Closed request validation for protocol version 1."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import HarnessError


PROTOCOL_VERSION = "codex-blender/v1"
REQUEST_FIELDS = {
    "protocolVersion",
    "sessionId",
    "requestId",
    "transactionId",
    "command",
    "arguments",
    "expectedSceneRevision",
    "authorization",
}


@dataclass(frozen=True)
class CommandRequest:
    protocol_version: str
    session_id: str
    request_id: str
    transaction_id: str
    command: str
    arguments: dict
    expected_scene_revision: int | None = None
    authorization: str | None = None

    @classmethod
    def parse(cls, payload: dict) -> "CommandRequest":
        if not isinstance(payload, dict):
            raise HarnessError("INVALID_REQUEST", "request must be an object")
        unknown = sorted(set(payload) - REQUEST_FIELDS)
        if unknown:
            raise HarnessError("INVALID_REQUEST", f"unknown fields: {unknown}")
        required = ("protocolVersion", "sessionId", "requestId", "transactionId", "command", "arguments")
        missing = [field for field in required if field not in payload]
        if missing:
            raise HarnessError("INVALID_REQUEST", f"missing fields: {missing}")
        if payload["protocolVersion"] != PROTOCOL_VERSION:
            raise HarnessError("UNSUPPORTED_PROTOCOL", f"expected {PROTOCOL_VERSION}")
        for field in ("sessionId", "requestId", "transactionId", "command"):
            if not isinstance(payload[field], str) or not payload[field]:
                raise HarnessError("INVALID_REQUEST", f"{field} must be a non-empty string")
        if not isinstance(payload["arguments"], dict):
            raise HarnessError("INVALID_REQUEST", "arguments must be an object")
        revision = payload.get("expectedSceneRevision")
        if revision is not None and (isinstance(revision, bool) or not isinstance(revision, int) or revision < 0):
            raise HarnessError("INVALID_REQUEST", "expectedSceneRevision must be a non-negative integer")
        return cls(
            protocol_version=payload["protocolVersion"],
            session_id=payload["sessionId"],
            request_id=payload["requestId"],
            transaction_id=payload["transactionId"],
            command=payload["command"],
            arguments=dict(payload["arguments"]),
            expected_scene_revision=revision,
            authorization=payload.get("authorization"),
        )

