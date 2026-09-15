"""User-interaction policy for a bounded Blender design run.

The policy decides which lifecycle events require a conversational review. It
does not grant command authorization: path checks, transactions, and
action-bound claims remain enforced by the Harness session.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path


class ExecutionPolicyError(ValueError):
    """Raised when an automatic-run envelope is incomplete or unsafe."""


class ExecutionMode(str, Enum):
    """Supported user-interaction cadences."""

    INTERACTIVE = "interactive"
    AUTO_WITH_BUDGET = "auto_with_budget"
    REVIEW_ONLY = "review_only"


_IRREVERSIBLE_EVENTS = frozenset(
    {"delete", "overwrite", "expert_python", "path_escape", "budget_exceeded", "recovery_resubmit"}
)


@dataclass(frozen=True)
class ExecutionPolicy:
    """Immutable execution envelope recorded with each design session."""

    mode: ExecutionMode
    approved_output_root: str | None = None
    allow_designed_proxies: bool = False
    downstream_budget_limit: Decimal | None = None
    export_formats: tuple[str, ...] = ("blend", "glb", "gltf", "fbx", "obj", "stl", "png", "jpg", "mp4")

    def __post_init__(self):
        try:
            object.__setattr__(self, "mode", ExecutionMode(self.mode))
        except (ValueError, TypeError) as exc:
            raise ExecutionPolicyError("unknown execution mode") from exc
        if type(self.allow_designed_proxies) is not bool:
            raise ExecutionPolicyError("allow_designed_proxies must be boolean")
        object.__setattr__(self, "downstream_budget_limit", self._parse_budget(self.downstream_budget_limit))
        if not isinstance(self.export_formats, (list, tuple)) or not all(
            isinstance(value, str) and value in {"blend", "glb", "gltf", "fbx", "obj", "stl", "png", "jpg", "mp4"}
            for value in self.export_formats
        ):
            raise ExecutionPolicyError("invalid export formats")
        object.__setattr__(self, "export_formats", tuple(self.export_formats))
        if self.mode is ExecutionMode.AUTO_WITH_BUDGET:
            if not isinstance(self.approved_output_root, str) or not Path(self.approved_output_root).is_absolute():
                raise ExecutionPolicyError("automatic execution requires an absolute output root")
            root = Path(self.approved_output_root).resolve()
            if root == Path(root.anchor):
                raise ExecutionPolicyError("filesystem root is not a scoped output directory")
            object.__setattr__(self, "approved_output_root", str(root))

    @classmethod
    def from_dict(cls, payload: dict) -> "ExecutionPolicy":
        if not isinstance(payload, dict) or set(payload) - {
            "mode", "approvedOutputRoot", "allowDesignedProxies", "downstreamBudgetLimit", "exportFormats"
        }:
            raise ExecutionPolicyError("invalid execution policy fields")
        return cls(payload.get("mode", "interactive"), payload.get("approvedOutputRoot"),
                   payload.get("allowDesignedProxies", False), payload.get("downstreamBudgetLimit"),
                   tuple(payload.get("exportFormats", cls.__dataclass_fields__["export_formats"].default)))

    @classmethod
    def interactive(cls) -> "ExecutionPolicy":
        """Create a policy that requests normal milestone review."""
        return cls(ExecutionMode.INTERACTIVE)

    @classmethod
    def review_only(cls) -> "ExecutionPolicy":
        """Create a policy that permits no mutation or export."""
        return cls(ExecutionMode.REVIEW_ONLY)

    @classmethod
    def auto_with_budget(
        cls,
        approved_output_root: str | None,
        allow_designed_proxies: bool,
        downstream_budget_limit: str | Decimal | None,
    ) -> "ExecutionPolicy":
        """Create an automatic policy constrained to one output root and budget."""
        if not isinstance(approved_output_root, str) or not approved_output_root.strip():
            raise ExecutionPolicyError("auto_with_budget requires approved_output_root")
        budget = cls._parse_budget(downstream_budget_limit)
        return cls(
            ExecutionMode.AUTO_WITH_BUDGET,
            approved_output_root=approved_output_root,
            allow_designed_proxies=allow_designed_proxies,
            downstream_budget_limit=budget,
        )

    @staticmethod
    def _parse_budget(value: str | Decimal | None) -> Decimal | None:
        if value is None:
            return None
        try:
            budget = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise ExecutionPolicyError("downstream_budget_limit must be decimal") from exc
        if not budget.is_finite() or budget < 0:
            raise ExecutionPolicyError("downstream_budget_limit must be non-negative")
        return budget

    def requires_user_review(self, event: str) -> bool:
        """Return whether the named lifecycle event interrupts this policy."""
        if event in _IRREVERSIBLE_EVENTS:
            return True
        if self.mode is ExecutionMode.INTERACTIVE:
            return True
        if self.mode is ExecutionMode.REVIEW_ONLY:
            return True
        if event == "missing_asset":
            return not self.allow_designed_proxies
        return event not in {"milestone_complete", "final_artifact_report", "mutation", "export"}

    def permits_fresh_export(self, arguments: dict) -> bool:
        """An automatic grant covers only a new output under the fixed root and format scope."""
        if self.mode is not ExecutionMode.AUTO_WITH_BUDGET or arguments.get("overwrite", False) is not False:
            return False
        raw = arguments.get("path")
        if not isinstance(raw, str) or not Path(raw).is_absolute():
            return False
        target = Path(raw)
        if target.suffix.lower().lstrip(".") not in self.export_formats:
            return False
        root = Path(self.approved_output_root)
        if not target.resolve().is_relative_to(root) or target.exists():
            return False
        for candidate in (target, *target.parents):
            if candidate.resolve() == root:
                break
            if candidate.is_symlink():
                return False
        return True

    def to_audit_dict(self) -> dict[str, object]:
        """Return a non-secret, JSON-safe policy record for the session audit."""
        return {
            "mode": self.mode.value,
            "approvedOutputRoot": self.approved_output_root,
            "allowDesignedProxies": self.allow_designed_proxies,
            "exportFormats": list(self.export_formats),
            "downstreamBudgetLimit": (
                str(self.downstream_budget_limit) if self.downstream_budget_limit is not None else None
            ),
        }
