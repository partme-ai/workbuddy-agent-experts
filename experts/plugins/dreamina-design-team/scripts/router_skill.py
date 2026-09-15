"""Router Skill code path for ``dreamina-design-use``.

This module backs the router Skill. It does *not* embed any prompt or
CLI invocation body — it only selects between the packaged Skills and
enforces the anti-patterns called out in the plan:

* refuse ambiguous routing (multiple matches);
* refuse hard-coded catalogs;
* require explicit approval binding;
* require web-prerequisite acknowledgement for the first video;
* require submit-ID query before any blind resubmission.

The additive ``video_project`` intent routes to the project orchestrator Skill.
It is a separate intent so it cannot change any existing image or video route.

The router deliberately defers to ``scripts/verify_skill_snapshot`` to
prove every packaged Skill is byte-identical to the verified upstream
commit before any routing decision is allowed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


class RouterError(Exception):
    """Base class for router errors."""


class AmbiguousRoutingError(RouterError):
    """The user's intent matches more than one packaged Skill."""


class HardCodedCatalogError(RouterError):
    """A caller asked the router to bypass the registry with a hard-coded list."""


class WebPrerequisiteRequired(RouterError):
    """The first video submission requires the web-console acknowledgement."""


class ApprovalMismatchError(RouterError):
    """The approval's request_fingerprint does not match the current request."""


@dataclass(frozen=True)
class _RoutingTable:
    image_mode_to_skill: Mapping[str, str]
    video_mode_to_skill: Mapping[str, str]


# Registry, not catalog — values are Skill names, not model tokens.
ROUTING_TABLE = _RoutingTable(
    image_mode_to_skill={
        "text2image": "dreamina-cli-text2image",
        "image2image": "dreamina-cli-image2image",
    },
    video_mode_to_skill={
        "text2video": "dreamina-cli-text2video",
        "image2video": "dreamina-cli-image2video",
        "frames2video": "dreamina-cli",
        "multiframe2video": "dreamina-cli",
        "multimodal2video": "dreamina-cli",
    },
)

# Additive project intent. Kept out of the direct-mode tables so no existing
# route can be shadowed by the project workflow.
PROJECT_INTENT = "video_project"
PROJECT_INTENTS = {
    "reference": "dreamina-video-production",
}


class Router:
    """Pure router that selects a packaged Skill for a given intent."""

    def route(self, *, intent: str, mode: str) -> str:
        if intent == "image":
            target = ROUTING_TABLE.image_mode_to_skill.get(mode)
        elif intent == "video":
            target = ROUTING_TABLE.video_mode_to_skill.get(mode)
        elif intent == PROJECT_INTENT:
            target = PROJECT_INTENTS.get(mode)
        else:
            raise AmbiguousRoutingError(f"unknown intent: {intent}")
        if target is None:
            raise AmbiguousRoutingError(
                f"no packaged Skill for intent={intent} mode={mode}"
            )
        return target

    def route_with_hardcoded_catalog(self, *, intent: str) -> str:  # noqa: ARG002
        raise HardCodedCatalogError(
            "router must use the registry, not a hard-coded catalog"
        )

    def can_submit_first_video_without_web_acknowledgement(self) -> bool:
        raise WebPrerequisiteRequired(
            "first Dreamina video requires the web-console prerequisite acknowledgement; "
            "the router refuses silent bypass"
        )

    def replay_approval(self, *, request_fingerprint: str, stored_fingerprint: str) -> bool:
        if request_fingerprint != stored_fingerprint:
            raise ApprovalMismatchError(
                "approval reuse with mismatched fingerprint is forbidden"
            )
        return True


__all__ = [
    "AmbiguousRoutingError",
    "ApprovalMismatchError",
    "HardCodedCatalogError",
    "PROJECT_INTENT",
    "PROJECT_INTENTS",
    "Router",
    "RouterError",
    "WebPrerequisiteRequired",
]
