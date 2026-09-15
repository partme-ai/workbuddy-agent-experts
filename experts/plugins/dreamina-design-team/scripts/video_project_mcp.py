"""Ten additive video-project MCP tools.

The existing eleven Dreamina tools remain the stable atomic layer. These ten
tools add a resumable reference-video-to-final-MP4 workflow on top of it
without changing any of them.

Every definition here is a closed ``type: object`` schema with
``additionalProperties: false`` and bounded collections. Callers can never
supply a shell fragment, raw argv, a codec flag, or an ffmpeg filter
expression, so the local media layer always receives a fixed argv it built
itself.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

IDENTIFIER_PROJECT = r"^vp_[a-f0-9]{24}$"
IDENTIFIER_VERSION = r"^v[0-9]{3}$"
IDENTIFIER_SHA256 = r"^[a-f0-9]{64}$"

PROJECT_TOOL_NAMES = (
    "dreamina_video_project",
    "dreamina_analyze_reference_video",
    "dreamina_validate_shot_analysis",
    "dreamina_create_redesign",
    "dreamina_quote_video_batch",
    "dreamina_approve_video_batch",
    "dreamina_execute_video_batch",
    "dreamina_evaluate_video_batch",
    "dreamina_compose_video",
    "dreamina_export_video_project",
)

CREATIVE_MODES = ("original_redesign", "authorized_replication")
AUDIO_POLICIES = ("full_redesign", "preserve_authorized_audio", "subtitles_only", "silent")
SUBTITLE_MODES = ("none", "sidecar", "muxed", "burned_in")
MEDIA_TOOL_KINDS = ("ffmpeg", "ffprobe", "whisper", "narration")


class ProjectToolError(ValueError):
    """A project tool received an action-invalid or forbidden argument set."""


def _project_id() -> dict[str, Any]:
    return {"type": "string", "pattern": IDENTIFIER_PROJECT}


def _version_id() -> dict[str, Any]:
    return {"type": "string", "pattern": IDENTIFIER_VERSION}


def _sha256() -> dict[str, Any]:
    return {"type": "string", "pattern": IDENTIFIER_SHA256}


def _roots(max_items: int = 10) -> dict[str, Any]:
    return {
        "type": "array",
        "items": {"type": "string", "minLength": 1},
        "maxItems": max_items,
        "uniqueItems": True,
    }


def _media_tool_paths() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {kind: {"type": "string", "minLength": 1} for kind in MEDIA_TOOL_KINDS},
    }


def _approval(action: str) -> str:
    """Read-only actions are pre-approved; every mutating action prompts."""
    return "approve" if action == "approve" else "prompt"


def project_tool_definitions() -> list[dict[str, Any]]:
    """The ten closed additive tool definitions, in plan order."""
    return [
        {
            "name": "dreamina_video_project",
            "description": (
                "Create, inspect, list, or resume a private video project, and enroll the "
                "trusted local media tools the project will use."
            ),
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["action"],
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["runtime_status", "enroll_media_tools", "create", "get", "list", "resume"],
                    },
                    "project_id": _project_id(),
                    "title": {"type": "string", "minLength": 1, "maxLength": 200},
                    "creative_mode": {"type": "string", "enum": list(CREATIVE_MODES)},
                    "audio_policy": {"type": "string", "enum": list(AUDIO_POLICIES)},
                    "media_tool_paths": _media_tool_paths(),
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
            },
            "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
        },
        {
            "name": "dreamina_analyze_reference_video",
            "description": (
                "Seed the source video into a project, then derive frames, contact sheets, "
                "or a typed recut from the deterministic analysis."
            ),
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["action", "project_id"],
                "properties": {
                    "action": {"type": "string", "enum": ["seed", "frames", "sheets", "recut"]},
                    "project_id": _project_id(),
                    "source_path": {"type": "string", "minLength": 1},
                    "approved_roots": _roots(),
                    "threshold": {"type": "number", "minimum": 0.05, "maximum": 0.80},
                    "min_shot_seconds": {"type": "number", "minimum": 0.10, "maximum": 5.00},
                    "track_hz": {"type": "number", "minimum": 1, "maximum": 10},
                    "analysis_version": _version_id(),
                    "columns": {"type": "integer", "minimum": 1, "maximum": 10},
                    "rows": {"type": "integer", "minimum": 1, "maximum": 10},
                    "splits": {"type": "array", "maxItems": 200, "items": {"type": "object"}},
                    "merges": {"type": "array", "maxItems": 200, "items": {"type": "object"}},
                },
            },
            "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
        },
        {
            "name": "dreamina_validate_shot_analysis",
            "description": (
                "Persist semantic shot annotations against a machine analysis version, but "
                "only when the caller's machine fingerprint still matches."
            ),
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["project_id", "analysis_version", "machine_fingerprint", "annotations"],
                "properties": {
                    "project_id": _project_id(),
                    "analysis_version": _version_id(),
                    "machine_fingerprint": _sha256(),
                    "annotations": {"type": "array", "minItems": 1, "maxItems": 500, "items": {"type": "object"}},
                },
            },
            "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
        },
        {
            "name": "dreamina_create_redesign",
            "description": (
                "Create a creative-design version. Original redesign replaces expressive "
                "content; authorized replication requires a complete, scope-matching rights receipt."
            ),
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["project_id", "analysis_version", "creative_mode", "design"],
                "properties": {
                    "project_id": _project_id(),
                    "analysis_version": _version_id(),
                    "creative_mode": {"type": "string", "enum": list(CREATIVE_MODES)},
                    "design": {"type": "object"},
                    "rights_assertion": {"type": "object"},
                },
            },
            "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
        },
        {
            "name": "dreamina_quote_video_batch",
            "description": (
                "Enumerate the exact base and retry requests for an approved design and "
                "return their immutable quote. Spends nothing."
            ),
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["project_id", "design_version", "cost_basis"],
                "properties": {
                    "project_id": _project_id(),
                    "design_version": _version_id(),
                    "cost_basis": {"type": "object"},
                    "max_attempts_per_shot": {"type": "integer", "minimum": 1, "maximum": 3},
                },
            },
            "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
        },
        {
            "name": "dreamina_approve_video_batch",
            "description": (
                "Activate one non-expandable whole-batch allowance for an exact quote "
                "fingerprint after native confirmation."
            ),
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["project_id", "batch_version", "quote_fingerprint"],
                "properties": {
                    "project_id": _project_id(),
                    "batch_version": _version_id(),
                    "quote_fingerprint": _sha256(),
                },
            },
            "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
        },
        {
            "name": "dreamina_execute_video_batch",
            "description": (
                "Run, reconcile, or resume an activated batch. An activated batch can reduce "
                "work but can never add shots, models, references, retries, or credits."
            ),
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["action", "project_id", "batch_version", "allowance_id"],
                "properties": {
                    "action": {"type": "string", "enum": ["run_next", "reconcile", "resume"]},
                    "project_id": _project_id(),
                    "batch_version": _version_id(),
                    "allowance_id": {"type": "string", "minLength": 1, "maxLength": 128},
                    "max_new_submissions": {"type": "integer", "minimum": 1, "maximum": 4},
                    "download_root": {"type": "string", "minLength": 1},
                    "approved_roots": _roots(),
                },
            },
            "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True},
        },
        {
            "name": "dreamina_evaluate_video_batch",
            "description": (
                "Record measured and semantic gates for one shot attempt and return the "
                "decision: accepted, a prequoted retry, rejected, or manual review."
            ),
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "project_id",
                    "batch_version",
                    "shot_id",
                    "attempt",
                    "artifact_sha256",
                    "semantic_evaluation",
                ],
                "properties": {
                    "project_id": _project_id(),
                    "batch_version": _version_id(),
                    "shot_id": {"type": "string", "pattern": "^s[0-9]{3,4}$"},
                    "attempt": {"type": "integer", "minimum": 1, "maximum": 3},
                    "artifact_sha256": _sha256(),
                    "semantic_evaluation": {"type": "object"},
                },
            },
            "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
        },
        {
            "name": "dreamina_compose_video",
            "description": (
                "Build the closed timeline and render one temporary final MP4 from the "
                "accepted shots using an internally constructed ffmpeg graph."
            ),
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["project_id", "batch_version", "composition"],
                "properties": {
                    "project_id": _project_id(),
                    "batch_version": _version_id(),
                    "composition": {"type": "object"},
                    "audio_policy": {"type": "string", "enum": list(AUDIO_POLICIES)},
                    "subtitle_mode": {"type": "string", "enum": list(SUBTITLE_MODES)},
                },
            },
            "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
        },
        {
            "name": "dreamina_export_video_project",
            "description": (
                "Verify the rendered MP4, then export it to the approved destination with "
                "the comparison report."
            ),
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["project_id", "composition_version", "destination", "approved_roots"],
                "properties": {
                    "project_id": _project_id(),
                    "composition_version": _version_id(),
                    "destination": {"type": "string", "minLength": 1},
                    "approved_roots": _roots(),
                    "include_report": {"type": "boolean"},
                    "subtitle_mode": {"type": "string", "enum": list(SUBTITLE_MODES)},
                },
            },
            "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
        },
    ]


# Action-specific requirements. A field listed as forbidden for an action must
# be absent, so a caller cannot smuggle a seed-only path or a batch-only
# allowance into an unrelated action.
_ACTION_RULES: dict[str, dict[str, tuple[frozenset[str], frozenset[str]]]] = {
    "dreamina_video_project": {
        "runtime_status": (frozenset(), frozenset({"project_id", "title", "media_tool_paths"})),
        "enroll_media_tools": (frozenset({"media_tool_paths"}), frozenset({"title", "creative_mode", "audio_policy"})),
        "create": (frozenset({"title"}), frozenset({"project_id", "media_tool_paths"})),
        "get": (frozenset({"project_id"}), frozenset({"title", "media_tool_paths"})),
        "list": (frozenset(), frozenset({"project_id", "media_tool_paths"})),
        "resume": (frozenset({"project_id"}), frozenset({"title", "media_tool_paths"})),
    },
    "dreamina_analyze_reference_video": {
        "seed": (frozenset({"source_path"}), frozenset({"analysis_version", "columns", "rows", "splits", "merges"})),
        "frames": (frozenset({"analysis_version"}), frozenset({"source_path", "approved_roots", "threshold"})),
        "sheets": (frozenset({"analysis_version", "columns", "rows"}), frozenset({"source_path"})),
        "recut": (frozenset({"analysis_version"}), frozenset({"source_path", "columns", "rows"})),
    },
    "dreamina_execute_video_batch": {
        "run_next": (frozenset(), frozenset()),
        "reconcile": (frozenset(), frozenset({"max_new_submissions", "download_root", "approved_roots"})),
        "resume": (frozenset(), frozenset()),
    },
}


def validate_action(name: str, args: Mapping[str, Any]) -> None:
    """Enforce action-specific required and forbidden fields."""
    rules = _ACTION_RULES.get(name)
    if rules is None:
        return
    action = args.get("action")
    if not isinstance(action, str) or action not in rules:
        raise ProjectToolError(f"{name} requires a known action")
    required, forbidden = rules[action]
    missing = sorted(field for field in required if args.get(field) in (None, "", [], {}))
    if missing:
        raise ProjectToolError(f"{name} action {action} requires: {', '.join(missing)}")
    present = sorted(field for field in forbidden if field in args)
    if present:
        raise ProjectToolError(f"{name} action {action} forbids: {', '.join(present)}")


def _validate_schema(value: Any, schema: Mapping[str, Any], path: str = "arguments") -> None:
    """Validate the closed subset of JSON Schema these definitions use."""
    expected = schema.get("type")
    if expected == "object":
        if not isinstance(value, Mapping):
            raise ProjectToolError(f"{path} must be an object")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(value) - set(properties))
            if unknown:
                raise ProjectToolError(f"{path} has unsupported fields: {', '.join(unknown)}")
        for field in schema.get("required", ()):
            if value.get(field) in (None, "", [], {}):
                raise ProjectToolError(f"{path}.{field} is required")
        for field, item in value.items():
            if field in properties:
                _validate_schema(item, properties[field], f"{path}.{field}")
        return
    if expected == "array":
        if not isinstance(value, (list, tuple)):
            raise ProjectToolError(f"{path} must be an array")
        maximum = schema.get("maxItems")
        if isinstance(maximum, int) and len(value) > maximum:
            raise ProjectToolError(f"{path} accepts at most {maximum} items")
        if schema.get("uniqueItems") and len({repr(item) for item in value}) != len(value):
            raise ProjectToolError(f"{path} items must be unique")
        for index, item in enumerate(value):
            _validate_schema(item, schema.get("items", {}), f"{path}[{index}]")
        return
    if expected == "string":
        if not isinstance(value, str):
            raise ProjectToolError(f"{path} must be a string")
        minimum = schema.get("minLength")
        maximum = schema.get("maxLength")
        if isinstance(minimum, int) and len(value) < minimum:
            raise ProjectToolError(f"{path} is shorter than {minimum}")
        if isinstance(maximum, int) and len(value) > maximum:
            raise ProjectToolError(f"{path} is longer than {maximum}")
        enum = schema.get("enum")
        if enum is not None and value not in enum:
            raise ProjectToolError(f"{path} must be one of {list(enum)}")
        pattern = schema.get("pattern")
        if pattern is not None:
            import re

            if re.fullmatch(pattern, value) is None:
                raise ProjectToolError(f"{path} does not match {pattern}")
        return
    if expected == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ProjectToolError(f"{path} must be an integer")
        if "minimum" in schema and value < schema["minimum"]:
            raise ProjectToolError(f"{path} must be >= {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise ProjectToolError(f"{path} must be <= {schema['maximum']}")
        return
    if expected == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ProjectToolError(f"{path} must be a number")
        if "minimum" in schema and value < schema["minimum"]:
            raise ProjectToolError(f"{path} must be >= {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise ProjectToolError(f"{path} must be <= {schema['maximum']}")
        return
    if expected == "boolean":
        if not isinstance(value, bool):
            raise ProjectToolError(f"{path} must be a boolean")


class VideoProjectMcpTools:
    """Thin registry: validate, enforce action rules, then delegate.

    Every dependency is injected, so tests never need real ffmpeg, Dreamina,
    ASR, narration, or a native dialog.
    """

    def __init__(
        self,
        handlers: Mapping[str, Callable[[Mapping[str, Any]], dict[str, Any]]] | None = None,
    ) -> None:
        self._schemas = {tool["name"]: tool["inputSchema"] for tool in project_tool_definitions()}
        self._handlers = dict(handlers or {})

    def register(self, name: str, handler: Callable[[Mapping[str, Any]], dict[str, Any]]) -> None:
        if name not in self._schemas:
            raise ProjectToolError(f"unknown video project tool: {name}")
        self._handlers[name] = handler

    def handles(self, name: str) -> bool:
        return name in self._schemas

    def call(self, name: str, args: Mapping[str, Any]) -> dict[str, Any]:
        schema = self._schemas.get(name)
        if schema is None:
            raise ProjectToolError(f"unknown video project tool: {name}")
        _validate_schema(args, schema)
        validate_action(name, args)
        handler = self._handlers.get(name)
        if handler is None:
            raise ProjectToolError(f"{name} has no registered handler")
        return handler(args)


__all__ = [
    "AUDIO_POLICIES",
    "CREATIVE_MODES",
    "MEDIA_TOOL_KINDS",
    "PROJECT_TOOL_NAMES",
    "ProjectToolError",
    "SUBTITLE_MODES",
    "VideoProjectMcpTools",
    "project_tool_definitions",
    "validate_action",
]
