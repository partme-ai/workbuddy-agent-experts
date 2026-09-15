"""Bounded secret redaction for Dreamina CLI and MCP output."""

from __future__ import annotations

import re
from collections.abc import Mapping


REDACTED = "[REDACTED]"
SENSITIVE_KEY = re.compile(r"(?:token|cookie|authorization|device_code|user_code|secret|password|api[_-]?key|private[_-]?key|signed[_-]?url)", re.I)
TEXT_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)((?:access_token|refresh_token|device_code|user_code|cookie|secret|password)\s*[:=]\s*)[^\s,;]+"),
)
SIGNED_URL_PATTERN = re.compile(r"(?i)https?://[^\s]+[?&](?:token|key|signature|sig|expires)=[^\s,;]+")


def redact_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): REDACTED if SENSITIVE_KEY.search(str(key)) else redact_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return redact_text(value, max_bytes=1024 * 1024)
    return value


def redact_text(text: str, *, max_bytes: int) -> str:
    result = str(text)
    result = SIGNED_URL_PATTERN.sub(REDACTED, result)
    for pattern in TEXT_PATTERNS:
        result = pattern.sub(lambda match: match.group(1) + REDACTED, result)
    encoded = result.encode("utf-8")
    if len(encoded) <= max_bytes:
        return result
    suffix = "…[TRUNCATED]"
    budget = max(0, max_bytes - len(suffix.encode("utf-8")))
    prefix = encoded[:budget].decode("utf-8", errors="ignore")
    return prefix + suffix
