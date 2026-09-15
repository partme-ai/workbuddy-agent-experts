"""Runtime-only delegation to a user-installed official Jimeng uploader."""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlsplit

from ..errors import HarnessError


MODULE_NAME = "jimeng_blender_uploader"


class OfficialUploaderCommands:
    """Project the official add-on's public operators into Harness commands."""

    def __init__(self, bpy_module, *, approved_output_root=None, approved_asset_roots=()):
        self.bpy = bpy_module
        self.output_root = Path(approved_output_root).resolve() if approved_output_root else None
        from ..path_policy import PathPolicy
        self.asset_policy = PathPolicy(approved_asset_roots) if approved_asset_roots else None

    def _addon(self):
        addons = getattr(getattr(self.bpy.context, "preferences", None), "addons", {})
        addon = addons.get(MODULE_NAME) if hasattr(addons, "get") else None
        operators = getattr(getattr(self.bpy, "ops", None), "jimeng", None)
        required = ("render_upload", "upload_existing", "open_redirect_url")
        if addon is None or operators is None or any(not callable(getattr(operators, name, None)) for name in required):
            raise HarnessError(
                "OFFICIAL_UPLOADER_NOT_AVAILABLE",
                "enable the official jimeng_blender_uploader add-on in Blender first",
            )
        self._version(addon)
        blender_version = tuple(getattr(getattr(self.bpy, "app", None), "version", ()))
        if blender_version and not ((5, 2, 0) <= blender_version < (5, 3, 0)):
            raise HarnessError(
                "OFFICIAL_UPLOADER_UNSUPPORTED",
                "official uploader integration is verified only for Blender 5.2.x",
            )
        return addon, operators

    @staticmethod
    def _version(addon) -> str:
        module_name = getattr(addon, "module", None)
        module = sys.modules.get(module_name) if isinstance(module_name, str) else module_name
        info = getattr(module, "bl_info", {}) if module is not None else {}
        version = info.get("version") if isinstance(info, dict) else None
        if isinstance(version, (tuple, list)):
            normalized = tuple(int(value) for value in version)
            if normalized < (1, 0, 0):
                raise HarnessError("OFFICIAL_UPLOADER_UNSUPPORTED", "official uploader 1.0.0 or newer is required")
            return ".".join(str(value) for value in normalized)
        raise HarnessError("OFFICIAL_UPLOADER_UNSUPPORTED", "official uploader version metadata is unavailable")

    def _require_output_dir(self, value) -> Path:
        if self.output_root is None:
            raise HarnessError("OUTPUT_NOT_AUTHORIZED", "official uploader output root is unavailable")
        path = Path(value)
        if path.is_symlink():
            raise HarnessError("OUTPUT_NOT_AUTHORIZED", "output directory must not be a symlink")
        resolved = path.resolve()
        try:
            resolved.relative_to(self.output_root)
        except ValueError as exc:
            raise HarnessError("OUTPUT_NOT_AUTHORIZED", "output directory is outside the approved root") from exc
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    def inspect(self, _arguments: dict) -> dict:
        addon, _operators = self._addon()
        return {
            "changedObjects": [],
            "result": {
                "installed": True,
                "module": MODULE_NAME,
                "version": self._version(addon),
                "operations": ["render_and_link", "link_existing", "status", "open_link"],
                "completionState": "JimengLinkReady",
            },
        }

    def render_and_link(self, arguments: dict) -> dict:
        _addon, operators = self._addon()
        scene = self.bpy.context.scene
        camera_name = arguments["camera"]
        camera = next(
            (obj for obj in self.bpy.data.objects if getattr(obj, "type", None) == "CAMERA" and obj.name == camera_name),
            None,
        )
        if camera is None:
            raise HarnessError("CAMERA_NOT_FOUND", f"no camera named {camera_name!r}")
        scene.jimeng_camera = camera
        scene.jimeng_resolution = arguments.get("resolution", "720p")
        scene.jimeng_frame_start = int(arguments["frameStart"])
        scene.jimeng_frame_end = int(arguments["frameEnd"])
        scene.jimeng_output_dir = str(self._require_output_dir(arguments["outputDir"]))
        scene.jimeng_prompt = arguments.get("prompt", "")
        result = operators.render_upload()
        self._require_finished(result)
        return self.status({})

    def link_existing(self, arguments: dict) -> dict:
        _addon, operators = self._addon()
        scene = self.bpy.context.scene
        if self.asset_policy is None:
            raise HarnessError("ASSET_NOT_AUTHORIZED", "official uploader asset roots are unavailable")
        scene.jimeng_video_path = str(self.asset_policy.require_file(arguments["videoPath"]))
        scene.jimeng_prompt = arguments.get("prompt", "")
        result = operators.upload_existing()
        self._require_finished(result)
        return self.status({})

    def status(self, _arguments: dict) -> dict:
        self._addon()
        scene = self.bpy.context.scene
        link_ready = bool(getattr(scene, "jimeng_link_ready", False))
        raw_url = str(getattr(scene, "jimeng_redirect_url", "") or "")
        parsed = urlsplit(raw_url) if raw_url else None
        origin = f"{parsed.scheme}://{parsed.netloc}" if parsed and parsed.scheme and parsed.netloc else ""
        return {
            "changedObjects": [],
            "result": {
                "taskState": str(getattr(scene, "jimeng_task_state", "IDLE")),
                "error": str(getattr(scene, "jimeng_error_message", "") or ""),
                "linkReady": link_ready,
                "linkOrigin": origin,
                "completionState": "JimengLinkReady" if link_ready else "Pending",
            },
        }

    def open_link(self, _arguments: dict) -> dict:
        _addon, operators = self._addon()
        if not bool(getattr(self.bpy.context.scene, "jimeng_link_ready", False)):
            raise HarnessError("OFFICIAL_LINK_NOT_READY", "no current Jimeng link is ready")
        self._require_finished(operators.open_redirect_url())
        return {"changedObjects": [], "result": {"opened": True, "completionState": "LinkOpened"}}

    @staticmethod
    def _require_finished(result) -> None:
        if "FINISHED" not in set(result or ()):
            raise HarnessError("OFFICIAL_OPERATION_FAILED", "official uploader operator did not finish")
