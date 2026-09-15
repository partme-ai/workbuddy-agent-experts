"""Blender-side local preview renderer with no upload or network handoff."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any, Callable


def _bootstrap_import_paths() -> None:
    scripts_path = str(Path(__file__).resolve().parent)
    root_path = str(Path(__file__).resolve().parents[1])
    for value in (root_path, scripts_path):
        if value not in sys.path:
            sys.path.insert(0, value)


_bootstrap_import_paths()


def _find_camera(bpy_module: Any, name: str) -> Any:
    for obj in bpy_module.data.objects:
        if getattr(obj, "type", None) == "CAMERA" and getattr(obj, "name", None) == name:
            return obj
    raise ValueError(f"no camera named {name!r} in the scene")


def render_background_movie(
    bpy_module: Any,
    scene: Any,
    output_path: Path,
    *,
    encode_sequence: Callable[[str, str, int, int], str] | None = None,
) -> str:
    """Render Workbench frames in background mode and encode them as MP4."""
    from vendor.jimeng_blender_uploader import dcc_config, viewport_render

    output = output_path.resolve()
    frames_dir = output.with_suffix("").with_name(f"{output.stem}_frames")
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True)

    frame_start = int(scene.jimeng_frame_start)
    frame_end = int(scene.jimeng_frame_end)
    width, height = viewport_render.export_resolution(scene)
    fps = int(dcc_config.DEFAULT_FPS)
    render = scene.render
    image_settings = render.image_settings
    previous = {
        "camera": scene.camera,
        "frame_current": scene.frame_current,
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
        "engine": render.engine,
        "filepath": render.filepath,
        "resolution_x": render.resolution_x,
        "resolution_y": render.resolution_y,
        "resolution_percentage": render.resolution_percentage,
        "file_format": image_settings.file_format,
    }
    try:
        scene.camera = scene.jimeng_camera
        scene.frame_start = frame_start
        scene.frame_end = frame_end
        render.engine = "BLENDER_WORKBENCH"
        render.resolution_x = width
        render.resolution_y = height
        render.resolution_percentage = 100
        image_settings.file_format = "PNG"
        for frame in range(frame_start, frame_end + 1):
            scene.frame_set(frame)
            render.filepath = str(frames_dir / f"frame_{frame:04d}.png")
            bpy_module.ops.render.render(write_still=True)
        encoder = encode_sequence or viewport_render._image_sequence_to_mp4
        return encoder(str(frames_dir), str(output), fps, frame_start)
    finally:
        scene.camera = previous["camera"]
        scene.frame_start = previous["frame_start"]
        scene.frame_end = previous["frame_end"]
        scene.frame_set(previous["frame_current"])
        render.engine = previous["engine"]
        render.filepath = previous["filepath"]
        render.resolution_x = previous["resolution_x"]
        render.resolution_y = previous["resolution_y"]
        render.resolution_percentage = previous["resolution_percentage"]
        image_settings.file_format = previous["file_format"]
        shutil.rmtree(frames_dir, ignore_errors=True)


def render_preview_only(
    bpy_module: Any,
    request: dict[str, Any],
    *,
    render_movie: Callable[[Any, Any], str] | None = None,
) -> dict[str, Any]:
    """Render one local preview without invoking any upload operator."""
    from blender_bridge import snapshot_scene_state, verify_restoration
    from codex_bridge import enable_addon
    from vendor.jimeng_blender_uploader import dcc_config, viewport_render

    enable_addon(bpy_module)
    scene = bpy_module.context.scene
    camera_name = str(request.get("camera_name") or "")
    frame_range = request.get("frame_range") or {}
    frame_start = int(frame_range.get("start"))
    frame_end = int(frame_range.get("end"))
    if frame_start > frame_end:
        raise ValueError("frame range start must not exceed end")

    scene.jimeng_camera = _find_camera(bpy_module, camera_name)
    scene.jimeng_frame_start = frame_start
    scene.jimeng_frame_end = frame_end
    scene.jimeng_resolution = str(request.get("resolution") or "720p")
    output_path = Path(str(request["output_path"])).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scene.jimeng_output_dir = str(output_path.parent)

    before = snapshot_scene_state(bpy_module)
    if render_movie is None:
        rendered_path = render_background_movie(bpy_module, scene, output_path)
    else:
        rendered_path = render_movie(scene, dcc_config.fallback_config("preview-only adapter"))
    restoration = verify_restoration(bpy_module, before)
    preview_mode = viewport_render.preview_mode_for_scene(scene)
    return {
        "rendered_path": str(Path(rendered_path).resolve()),
        "camera": camera_name,
        "frame_range": {"start": frame_start, "end": frame_end},
        "preview_kind": "material_preview" if preview_mode == "material" else "white_model",
        "restoration": {
            **restoration,
            "evidence": "vendored renderer state equals its pre-render snapshot",
        },
    }


def main(request_path: str) -> int:
    import bpy

    try:
        request = json.loads(Path(request_path).read_text(encoding="utf-8"))
        print(json.dumps(render_preview_only(bpy, request), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"category": "RENDER_FAILED", "message": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        separator = sys.argv.index("--")
        request_file = sys.argv[separator + 1]
    except (ValueError, IndexError):
        print(json.dumps({"category": "INVALID_REQUEST", "message": "missing request path"}), file=sys.stderr)
        raise SystemExit(1)
    raise SystemExit(main(request_file))
