#!/usr/bin/env python3
"""Run one bounded Stitch provider/asset smoke and clean it up separately."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

RELEASE_CANDIDATE = "0.7.8"

from stitch_harness.assets import local_tool_definitions  # noqa: E402
from stitch_harness.mcp_proxy import McpHttpSession, PROTOCOL_VERSION, ProxyError, UnknownWriteResult  # noqa: E402
from stitch_harness.secrets import platform_secret_provider  # noqa: E402
from stitch_harness.tool_catalog import REQUIRED_TOOL_NAMES, ToolCatalog  # noqa: E402


STAGES = (
    "create_project", "generate", "read", "edit", "variant",
    "design_system_create", "design_system_update", "design_system_list",
    "design_system_apply", "upload", "download",
)
PROJECT_PATTERN = re.compile(r"^projects/([0-9]+)$")
SCREEN_PATTERN = re.compile(r"^projects/([0-9]+)/screens/([A-Za-z0-9_-]{1,128})$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
ASSET_PATTERN = re.compile(r"^assets/([^/]+)$")
PROJECT_ASSET_PATTERN = re.compile(r"^projects/([0-9]+)/assets/([^/]+)$")
PROJECT_SESSION_PATTERN = re.compile(r"^projects/([0-9]+)/sessions/([^/]+)$")
LOCAL_TOOL_NAMES = frozenset(tool["name"] for tool in local_tool_definitions())
EXPECTED_TOOL_NAMES = REQUIRED_TOOL_NAMES | LOCAL_TOOL_NAMES
PUBLIC_STAGE_KEYS = frozenset(
    {
        "project_created", "screen_generated", "screen_read", "screen_edited",
        "one_variant_generated", "design_system_created", "design_system_updated",
        "design_system_listed", "design_system_applied", "asset_uploaded", "assets_downloaded",
    }
)
PUBLIC_COUNT_KEYS = frozenset(
    {"screens_read", "variant_screens", "design_systems", "uploaded_screens", "downloaded_files"}
)


def _canary_design_system() -> dict[str, Any]:
    return {
        "displayName": "Stitch Canary",
        "theme": {
            "colorMode": "LIGHT",
            "headlineFont": "INTER",
            "bodyFont": "INTER",
            "roundness": "ROUND_EIGHT",
            "customColor": "#2563EB",
        },
    }


def _asset_id(name: Any, project_id: str) -> str:
    if isinstance(name, str):
        match = ASSET_PATTERN.fullmatch(name)
        if match is not None:
            return match.group(1)
        project_match = PROJECT_ASSET_PATTERN.fullmatch(name)
        if project_match is not None and project_match.group(1) == project_id:
            return project_match.group(2)
    raise ProxyError("Stitch returned an invalid design-system identity")


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("canary clock must be timezone-aware")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _atomic_private_json(
    path: Path,
    payload: dict[str, Any],
    *,
    enforce_posix_mode: bool | None = None,
    mode_setter: Callable[[int, int], None] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    try:
        enforce_mode = os.name != "nt" if enforce_posix_mode is None else enforce_posix_mode
        if enforce_mode:
            setter = mode_setter if mode_setter is not None else os.fchmod
            setter(descriptor, 0o600)
        stream = os.fdopen(descriptor, "w", encoding="utf-8")
        descriptor = None
        with stream:
            json.dump(payload, stream, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        Path(temporary_name).unlink(missing_ok=True)


def _public_template(started_at: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "release_candidate": RELEASE_CANDIDATE,
        "smoke_scope": "provider-and-assets",
        "started_at": started_at,
        "finished_at": None,
        "stages": {key: False for key in sorted(PUBLIC_STAGE_KEYS)},
        "counts": {key: 0 for key in sorted(PUBLIC_COUNT_KEYS)},
        "hashes": {"download_manifest_sha256": None},
        "cleanup": {"delete_requested": False, "project_absent": False},
    }


def _validate_evidence_schema(payload: dict[str, Any]) -> None:
    expected = {
        "schema_version", "release_candidate", "smoke_scope", "started_at", "finished_at",
        "stages", "counts", "hashes", "cleanup",
    }
    if (
        not isinstance(payload, dict)
        or set(payload) != expected
        or payload.get("schema_version") != 1
        or payload.get("release_candidate") != RELEASE_CANDIDATE
        or payload.get("smoke_scope") != "provider-and-assets"
    ):
        raise ValueError("sanitized evidence has an invalid top-level contract")
    if set(payload.get("stages", {})) != PUBLIC_STAGE_KEYS:
        raise ValueError("sanitized evidence has invalid stage fields")
    if set(payload.get("counts", {})) != PUBLIC_COUNT_KEYS:
        raise ValueError("sanitized evidence has invalid count fields")
    if set(payload.get("cleanup", {})) != {"delete_requested", "project_absent"}:
        raise ValueError("sanitized evidence has invalid cleanup fields")
    for section in ("stages", "cleanup"):
        if not isinstance(payload.get(section), dict) or not all(isinstance(value, bool) for value in payload[section].values()):
            raise ValueError("sanitized evidence status values must be booleans")
    if not isinstance(payload.get("counts"), dict) or not all(
        isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in payload["counts"].values()
    ):
        raise ValueError("sanitized evidence counts must be non-negative integers")
    manifest_hash = payload.get("hashes", {}).get("download_manifest_sha256")
    if manifest_hash is not None and (
        not isinstance(manifest_hash, str) or SHA256_PATTERN.fullmatch(manifest_hash) is None
    ):
        raise ValueError("sanitized evidence hashes must be SHA-256 values")
    if set(payload.get("hashes", {})) != {"download_manifest_sha256"}:
        raise ValueError("sanitized evidence contains an unsupported hash field")
    for key in ("started_at", "finished_at"):
        value = payload.get(key)
        if value is not None and (not isinstance(value, str) or not value.endswith("Z")):
            raise ValueError("sanitized evidence timestamps must be UTC strings")


def _validate_public_evidence(payload: dict[str, Any]) -> None:
    """Backward-compatible alias for schema validation."""

    _validate_evidence_schema(payload)


def _validate_acceptance_evidence(payload: dict[str, Any]) -> None:
    _validate_evidence_schema(payload)
    if not all(payload["stages"].values()):
        raise ValueError("provider-and-assets acceptance requires every stage to pass")
    if not all(value > 0 for value in payload["counts"].values()):
        raise ValueError("provider-and-assets acceptance requires positive observed counts")
    if payload["hashes"]["download_manifest_sha256"] is None:
        raise ValueError("provider-and-assets acceptance requires a download manifest hash")
    if payload["finished_at"] is None:
        raise ValueError("provider-and-assets acceptance requires a completion timestamp")
    if not all(payload["cleanup"].values()):
        raise ValueError("provider-and-assets acceptance requires verified cleanup")


def _write_public_evidence(path: Path, payload: dict[str, Any]) -> None:
    _validate_evidence_schema(payload)
    _atomic_private_json(path, payload)


def _response_result(messages: list[dict[str, Any]], identifier: str, *, tool_call: bool) -> dict[str, Any]:
    if len(messages) != 1 or not isinstance(messages[0], dict):
        raise ProxyError("Stitch returned an invalid canary response")
    response = messages[0]
    if (
        response.get("jsonrpc") != "2.0"
        or type(response.get("id")) is not type(identifier)
        or response.get("id") != identifier
        or "error" in response
        or not isinstance(response.get("result"), dict)
    ):
        raise ProxyError("Stitch returned an invalid canary response")
    result = response["result"]
    if not tool_call:
        return result
    if result.get("isError") is True:
        raise ProxyError("Stitch returned a failed tool result")
    structured = result.get("structuredContent")
    if not isinstance(structured, dict):
        raise ProxyError("Stitch tool result has no valid structuredContent")
    return structured


def _project_identity(project: Any) -> tuple[str, str, str | None]:
    if not isinstance(project, dict):
        raise ProxyError("Stitch returned invalid project metadata")
    name = project.get("name")
    match = PROJECT_PATTERN.fullmatch(name) if isinstance(name, str) else None
    if match is None:
        raise ProxyError("Stitch returned invalid project metadata")
    title = project.get("title")
    if title is not None and not isinstance(title, str):
        raise ProxyError("Stitch returned invalid project metadata")
    return name, match.group(1), title


def _screen_identity(screen: Any, project_id: str) -> tuple[str, str]:
    if not isinstance(screen, dict):
        raise ProxyError("Stitch returned invalid screen metadata")
    source = screen.get("sourceScreen") or screen.get("name")
    identifier = screen.get("id")
    match = SCREEN_PATTERN.fullmatch(source) if isinstance(source, str) else None
    if match is None or match.group(1) != project_id or not isinstance(identifier, str) or not identifier:
        raise ProxyError("Stitch returned screen metadata for an invalid project identity")
    return source, identifier


def _screen_list(payload: dict[str, Any], project_id: str, *, exact_count: int | None = None) -> list[tuple[str, str]]:
    screens = payload.get("screens")
    if not isinstance(screens, list):
        components = payload.get("outputComponents")
        screens = []
        if isinstance(components, list):
            for component in components:
                design = component.get("design") if isinstance(component, dict) else None
                generated = design.get("screens") if isinstance(design, dict) else None
                if isinstance(generated, list):
                    screens.extend(generated)
    if not isinstance(screens, list) or not screens:
        raise ProxyError("Stitch returned an invalid nonempty screen list")
    identities = [_screen_identity(screen, project_id) for screen in screens]
    if exact_count is not None and len(identities) != exact_count:
        raise ProxyError(f"Stitch canary requires exactly {exact_count} screen result")
    return identities


class StitchBackend:
    """Live MCP backend. Opaque remote identifiers never leave private state."""

    def __init__(self, session: Any | None = None) -> None:
        self.session = session or McpHttpSession(provider=platform_secret_provider())
        self.catalog = ToolCatalog()
        self._ready = False
        self._request_id = 0

    def _request(self, method: str, params: dict[str, Any] | None = None, *, tool_call: bool = False) -> dict[str, Any]:
        self._request_id += 1
        identifier = f"canary-{self._request_id}"
        request: dict[str, Any] = {"jsonrpc": "2.0", "id": identifier, "method": method}
        if params is not None:
            request["params"] = params
        return _response_result(self.session.send(request), identifier, tool_call=tool_call)

    def _ensure_ready(self) -> None:
        if self._ready:
            return
        initialized = self._request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "stitch-design-live-smoke", "version": RELEASE_CANDIDATE},
            },
        )
        capabilities = initialized.get("capabilities")
        if initialized.get("protocolVersion") != PROTOCOL_VERSION or not isinstance(capabilities, dict) or not isinstance(capabilities.get("tools"), dict):
            raise ProxyError("Stitch returned an unsupported canary initialization")
        notification = self.session.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        if notification:
            raise ProxyError("Stitch returned a response to initialized notification")
        cursor: str | None = None
        seen_cursors: set[str] = set()
        while True:
            params = {"cursor": cursor} if cursor is not None else {}
            result = self._request("tools/list", params)
            tools = result.get("tools")
            if not isinstance(tools, list):
                raise ProxyError("Stitch returned an invalid tool catalog")
            try:
                self.catalog.extend(tools)
            except ValueError as error:
                raise ProxyError("Stitch returned an invalid tool catalog") from error
            next_cursor = result.get("nextCursor")
            if next_cursor is None:
                break
            if not isinstance(next_cursor, str) or not next_cursor or next_cursor in seen_cursors:
                raise ProxyError("Stitch returned an invalid tool catalog cursor")
            seen_cursors.add(next_cursor)
            cursor = next_cursor
        errors = self.catalog.validation_errors()
        names = {tool["name"] for tool in self.catalog.tools}
        if errors or names != EXPECTED_TOOL_NAMES or len(self.catalog.tools) != len(EXPECTED_TOOL_NAMES):
            raise ProxyError("Stitch provider/local tool catalog is invalid")
        self._ready = True

    def _call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self._ensure_ready()
        return self._request("tools/call", {"name": name, "arguments": arguments}, tool_call=True)

    @staticmethod
    def _selected(context: dict[str, Any]) -> dict[str, str]:
        return {"id": context["screen_id"], "sourceScreen": context["screen_name"]}

    def _list_projects(self) -> list[tuple[str, str, str | None]]:
        result = self._call("list_projects", {})
        projects = result.get("projects")
        if not isinstance(projects, list):
            raise ProxyError("Stitch did not return a project list")
        return [_project_identity(project) for project in projects]

    def execute(self, stage: str, context: dict[str, Any], workspace: Path) -> dict[str, Any]:
        if stage == "create_project":
            try:
                result = self._call("create_project", {"title": context["project_title"]})
                project_name, project_id, _ = _project_identity(result)
            except UnknownWriteResult:
                matches = [identity for identity in self._list_projects() if identity[2] == context["project_title"]]
                if len(matches) != 1:
                    raise UnknownWriteResult("project creation remains unknown after title reconciliation")
                project_name, project_id, _ = matches[0]
            return {"project_name": project_name, "project_id": project_id}
        if stage == "generate":
            result = self._call(
                "generate_screen_from_text",
                {
                    "projectId": context["project_id"],
                    "prompt": "Create one minimal 390x884 mobile canary screen with a heading, body text, and primary button.",
                },
            )
            identities = _screen_list(result, context["project_id"], exact_count=1)
            return {"screen_name": identities[0][0], "screen_id": identities[0][1]}
        if stage == "read":
            project = self._call("get_project", {"name": context["project_name"]})
            if project.get("name") != context["project_name"]:
                raise ProxyError("get_project did not bind the exact project identity")
            listed_payload = self._call("list_screens", {"projectId": context["project_id"]})
            expected = (context["screen_name"], context["screen_id"])
            if "screens" in listed_payload:
                listed = _screen_list(listed_payload, context["project_id"])
                if expected not in listed:
                    raise ProxyError("list_screens does not bind the exact generated screen identity")
            detail = self._call("get_screen", {"name": context["screen_name"]})
            if (
                detail.get("name") not in {None, context["screen_name"]}
                or not isinstance(detail.get("htmlCode"), dict)
                or not isinstance(detail.get("screenshot"), dict)
            ):
                raise ProxyError("get_screen did not return HTML and screenshot resources")
            return {"screen_count": 1}
        if stage == "edit":
            identities = _screen_list(
                self._call("edit_screens", {
                    "projectId": context["project_id"],
                    "selectedScreenIds": [context["screen_id"]],
                    "prompt": "Keep the layout and change the primary button label to Continue.",
                }),
                context["project_id"],
            )
            return {"screen_name": identities[0][0], "screen_id": identities[0][1]}
        if stage == "variant":
            identities = _screen_list(
                self._call("generate_variants", {
                    "projectId": context["project_id"],
                    "selectedScreenIds": [context["screen_id"]],
                    "prompt": "Create one layout variant while preserving the content hierarchy.",
                    "variantOptions": {"variantCount": 1, "creativeRange": "REFINE", "aspects": ["LAYOUT"]},
                }),
                context["project_id"], exact_count=1,
            )
            if identities[0][0] == context["screen_name"] or identities[0][1] == context["screen_id"]:
                raise ProxyError("variant result must be different from the exact source screen identity")
            return {"variant_count": len(identities)}
        if stage == "design_system_create":
            design_system = _canary_design_system()
            result = self._call("create_design_system", {
                "projectId": context["project_id"], "designSystem": design_system,
            })
            name = result.get("name")
            asset_id = _asset_id(name, context["project_id"])
            return {
                "design_system_name": name,
                "design_system_asset_id": asset_id,
                "design_system": design_system,
            }
        if stage == "design_system_update":
            result = self._call("update_design_system", {
                "name": context["design_system_name"],
                "projectId": context["project_id"],
                "designSystem": context["design_system"],
            })
            session_name = result.get("name")
            session_match = PROJECT_SESSION_PATTERN.fullmatch(session_name) if isinstance(session_name, str) else None
            returned_design_system = result.get("designSystem")
            returned_theme = returned_design_system.get("theme") if isinstance(returned_design_system, dict) else None
            if (
                session_match is None
                or session_match.group(1) != context["project_id"]
                or not isinstance(returned_theme, dict)
                or returned_design_system.get("displayName") != context["design_system"]["displayName"]
                or not all(returned_theme.get(key) == value for key, value in context["design_system"]["theme"].items())
            ):
                raise ProxyError("updated design-system identity does not match")
            return {"ok": True}
        if stage == "design_system_list":
            result = self._call("list_design_systems", {"projectId": context["project_id"]})
            systems = result.get("designSystems")
            if not isinstance(systems, list) or not systems or not any(
                isinstance(system, dict)
                and _asset_id(system.get("name"), context["project_id"]) == context["design_system_asset_id"]
                for system in systems
            ):
                raise ProxyError("design-system list does not contain the exact created asset")
            return {"design_system_count": len(systems)}
        if stage == "design_system_apply":
            identities = _screen_list(
                self._call("apply_design_system", {
                    "projectId": context["project_id"],
                    "selectedScreenInstances": [self._selected(context)],
                    "assetId": context["design_system_asset_id"],
                }),
                context["project_id"],
            )
            return {"screen_name": identities[0][0], "screen_id": identities[0][1]}
        if stage == "upload":
            source = workspace / "canary-upload.html"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("<!doctype html><meta charset=utf-8><title>Canary</title><main>Canary asset</main>\n", encoding="utf-8")
            result = self._call(
                "stitch_local_upload_asset",
                {"projectId": context["project_id"], "filePath": str(source.resolve()), "title": "Canary asset"},
            )
            screens = result.get("screens")
            if not isinstance(screens, list) or not screens:
                raise ProxyError("local upload did not return a nonempty screen list")
            for screen in screens:
                name = screen.get("name") if isinstance(screen, dict) else None
                match = SCREEN_PATTERN.fullmatch(name) if isinstance(name, str) else None
                if match is None or match.group(1) != context["project_id"]:
                    raise ProxyError("local upload returned a screen outside the exact project")
            return {"upload_count": len(screens), "uploaded_screen_name": screens[0]["name"]}
        if stage == "download":
            destination = (workspace / "downloaded").resolve()
            result = self._call(
                "stitch_local_download_assets",
                {
                    "projectId": context["project_id"],
                    "outputDir": str(destination),
                    "screenNames": [context["uploaded_screen_name"]],
                },
            )
            files = result.get("files")
            count = result.get("count")
            if result.get("outputDir") != str(destination) or not isinstance(files, list) or not files or count != len(files):
                raise ProxyError("local download returned an invalid output contract")
            hashes: list[str] = []
            for item in files:
                value = item.get("sha256") if isinstance(item, dict) else None
                if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
                    raise ProxyError("local download returned invalid hashes")
                hashes.append(value)
            manifest_hash = hashlib.sha256("\n".join(sorted(hashes)).encode("ascii")).hexdigest()
            return {"count": len(files), "manifest_sha256": manifest_hash}
        raise ValueError(f"unsupported canary stage: {stage}")

    def delete_project(self, context: dict[str, Any]) -> bool:
        self._call("delete_project", {"name": context["project_name"]})
        return True

    def project_absent(self, context: dict[str, Any]) -> bool:
        projects = self._list_projects()
        return context["project_name"] not in {identity[0] for identity in projects}

    def find_project_by_title(self, title: str) -> dict[str, str] | None:
        """Resolve exactly one valid project identity from a private unique title."""

        if not isinstance(title, str) or not title:
            raise ProxyError("cleanup project title is invalid")
        matches = [identity for identity in self._list_projects() if identity[2] == title]
        if len(matches) > 1:
            raise ProxyError("cleanup project title matches multiple projects")
        if not matches:
            return None
        name, project_id, _ = matches[0]
        return {"project_name": name, "project_id": project_id}


def _mark_stage(evidence: dict[str, Any], stage: str, result: dict[str, Any]) -> None:
    mapping = {
        "create_project": "project_created", "generate": "screen_generated", "read": "screen_read",
        "edit": "screen_edited", "variant": "one_variant_generated",
        "design_system_create": "design_system_created", "design_system_update": "design_system_updated",
        "design_system_list": "design_system_listed", "design_system_apply": "design_system_applied",
        "upload": "asset_uploaded", "download": "assets_downloaded",
    }
    evidence["stages"][mapping[stage]] = True
    count_mapping = {
        "read": ("screens_read", "screen_count"),
        "variant": ("variant_screens", "variant_count"),
        "design_system_list": ("design_systems", "design_system_count"),
        "upload": ("uploaded_screens", "upload_count"),
        "download": ("downloaded_files", "count"),
    }
    if stage in count_mapping:
        public_key, result_key = count_mapping[stage]
        evidence["counts"][public_key] = result[result_key]
    if stage == "download":
        evidence["hashes"]["download_manifest_sha256"] = result["manifest_sha256"]


def run_canary(backend: Any, state_path: Path, evidence_path: Path, workspace: Path, *, now: Callable[[], datetime] = _utc_now, nonce: str | None = None) -> dict[str, Any]:
    """Run every non-cleanup smoke stage, checkpointing opaque values in private state."""

    started = now()
    unique = (nonce or uuid.uuid4().hex[:12]).lower()
    if re.fullmatch(r"[0-9a-f]{12}", unique) is None:
        raise ValueError("canary nonce must contain exactly 12 lowercase hexadecimal characters")
    compact_time = started.astimezone(UTC).strftime("%Y%m%dt%H%M%Sz").lower()
    context: dict[str, Any] = {
        "schema_version": 1,
        "project_title": f"codex-stitch-canary-{compact_time}-{unique}",
        "workspace": str(Path(workspace).resolve()),
        "delete_attempted": False,
    }
    evidence = _public_template(_timestamp(started))
    _atomic_private_json(Path(state_path), context)
    _write_public_evidence(Path(evidence_path), evidence)
    for stage in STAGES:
        result = backend.execute(stage, context, Path(workspace).resolve())
        if not isinstance(result, dict):
            raise ValueError("canary backend result must be an object")
        context.update(result)
        context["last_completed_stage"] = stage
        _atomic_private_json(Path(state_path), context)
        _mark_stage(evidence, stage, result)
        _write_public_evidence(Path(evidence_path), evidence)
    evidence["finished_at"] = _timestamp(now())
    _write_public_evidence(Path(evidence_path), evidence)
    return evidence


def cleanup_canary(
    backend: Any,
    state_path: Path,
    evidence_path: Path,
    *,
    now: Callable[[], datetime] = _utc_now,
    reconciliation_attempts: int = 3,
    backoff_seconds: float = 1.0,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Attempt deletion once and always perform an independent absence read probe."""

    if (
        isinstance(reconciliation_attempts, bool)
        or not isinstance(reconciliation_attempts, int)
        or not 1 <= reconciliation_attempts <= 5
    ):
        raise ValueError("reconciliation attempts must be between 1 and 5")
    if (
        isinstance(backoff_seconds, bool)
        or not isinstance(backoff_seconds, (int, float))
        or not 0 <= backoff_seconds <= 10
    ):
        raise ValueError("reconciliation backoff must be between 0 and 10 seconds")
    state = json.loads(Path(state_path).read_text(encoding="utf-8"))
    evidence = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    delete_error: Exception | None = None
    read_error: Exception | None = None
    if not state.get("project_name"):
        title = state.get("project_title")
        if not isinstance(title, str) or not title:
            evidence["cleanup"]["project_absent"] = False
            evidence["finished_at"] = _timestamp(now())
            _write_public_evidence(Path(evidence_path), evidence)
            raise ProxyError("cleanup has no private project title for identity reconciliation")
        for attempt in range(reconciliation_attempts):
            identity = backend.find_project_by_title(title)
            if identity is not None:
                if set(identity) != {"project_name", "project_id"}:
                    raise ProxyError("cleanup title reconciliation returned an invalid identity")
                name = identity["project_name"]
                project_id = identity["project_id"]
                match = PROJECT_PATTERN.fullmatch(name) if isinstance(name, str) else None
                if match is None or match.group(1) != project_id:
                    raise ProxyError("cleanup title reconciliation returned an invalid identity")
                state.update(identity)
                _atomic_private_json(Path(state_path), state)
                break
            if attempt + 1 < reconciliation_attempts:
                sleeper(float(backoff_seconds))
        if not state.get("project_name"):
            evidence["cleanup"]["project_absent"] = False
            evidence["finished_at"] = _timestamp(now())
            _write_public_evidence(Path(evidence_path), evidence)
            raise ProxyError("cleanup project identity remains unknown after title reconciliation")
    if state.get("project_name"):
        if not state.get("delete_attempted", False):
            state["delete_attempted"] = True
            _atomic_private_json(Path(state_path), state)
            evidence["cleanup"]["delete_requested"] = True
            _write_public_evidence(Path(evidence_path), evidence)
            try:
                backend.delete_project(state)
            except Exception as error:  # Preserve unknown outcome; absence read still must run.
                delete_error = error
        else:
            evidence["cleanup"]["delete_requested"] = True
        for attempt in range(reconciliation_attempts):
            try:
                evidence["cleanup"]["project_absent"] = backend.project_absent(state) is True
                read_error = None
            except Exception as error:
                evidence["cleanup"]["project_absent"] = False
                read_error = error
            if evidence["cleanup"]["project_absent"]:
                break
            if attempt + 1 < reconciliation_attempts:
                sleeper(float(backoff_seconds))
    evidence["finished_at"] = _timestamp(now())
    _write_public_evidence(Path(evidence_path), evidence)
    if read_error is not None:
        raise ProxyError("cleanup absence could not be proved") from read_error
    if delete_error is not None and not evidence["cleanup"]["project_absent"]:
        raise delete_error
    return evidence


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run or clean up one Stitch Design provider/asset smoke")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "cleanup", "validate-evidence-schema", "validate-acceptance"):
        child = commands.add_parser(name)
        child.add_argument("--state", required=name in {"run", "cleanup"}, type=Path)
        child.add_argument("--evidence", required=True, type=Path)
        if name == "run":
            child.add_argument("--workspace", required=True, type=Path)
        if name == "cleanup":
            child.add_argument("--reconciliation-attempts", type=int, default=3)
            child.add_argument("--reconciliation-backoff-seconds", type=float, default=1.0)
    return parser


def main(arguments: list[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    try:
        if args.command in {"validate-evidence-schema", "validate-acceptance"}:
            payload = json.loads(args.evidence.read_text(encoding="utf-8"))
            if args.command == "validate-evidence-schema":
                _validate_evidence_schema(payload)
                print("sanitized smoke evidence schema passed")
            else:
                _validate_acceptance_evidence(payload)
                print("provider-and-assets acceptance evidence passed")
            return 0
        backend = StitchBackend()
        if args.command == "run":
            evidence = run_canary(backend, args.state, args.evidence, args.workspace)
        else:
            evidence = cleanup_canary(
                backend,
                args.state,
                args.evidence,
                reconciliation_attempts=args.reconciliation_attempts,
                backoff_seconds=args.reconciliation_backoff_seconds,
            )
            print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))
            return 0
        print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, ValueError, ProxyError, UnknownWriteResult, json.JSONDecodeError) as error:
        print(f"live smoke {args.command} failed safely: {type(error).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
