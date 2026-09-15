"""Short-lived, action-bound local authorization claims."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from collections.abc import Callable


class AuthorizationManager:
    def __init__(self, secret: bytes | None = None, now: Callable[[], float] | None = None):
        self._secret = secret or secrets.token_bytes(32)
        self._now = now or time.time

    def issue(self, request_id: str, action: str, *, ttl_seconds: int = 60) -> str:
        payload = {
            "requestId": request_id,
            "action": action,
            "expiresAt": int(self._now()) + int(ttl_seconds),
            "nonce": secrets.token_hex(12),
        }
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        signature = hmac.new(self._secret, body, hashlib.sha256).digest()
        return self._encode(body) + "." + self._encode(signature)

    def verify(self, claim: str | None, request_id: str, action: str) -> bool:
        if not claim or "." not in claim:
            return False
        try:
            body_token, signature_token = claim.split(".", 1)
            body = self._decode(body_token)
            signature = self._decode(signature_token)
            expected = hmac.new(self._secret, body, hashlib.sha256).digest()
            payload = json.loads(body)
        except Exception:
            return False
        return (
            hmac.compare_digest(signature, expected)
            and payload.get("requestId") == request_id
            and payload.get("action") == action
            and int(payload.get("expiresAt", 0)) >= int(self._now())
        )

    @staticmethod
    def _encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode().rstrip("=")

    @staticmethod
    def _decode(value: str) -> bytes:
        return base64.urlsafe_b64decode(value + "=" * ((4 - len(value) % 4) % 4))

