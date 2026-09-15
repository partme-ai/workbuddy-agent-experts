"""Read-only Dreamina account readiness service."""

from __future__ import annotations

from collections.abc import Mapping
from scripts.output_redactor import redact_value


class AccountService:
    def __init__(self, adapter): self.adapter = adapter

    def user_credit(self) -> dict[str, object]:
        result = self.adapter.run(["user_credit"])
        if result.exit_code != 0: raise RuntimeError("dreamina user_credit failed")
        if not isinstance(result.payload, Mapping): raise ValueError("dreamina user_credit returned no object")
        return dict(redact_value(result.payload))
