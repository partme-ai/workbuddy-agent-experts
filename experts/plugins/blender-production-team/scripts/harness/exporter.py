"""Blender project and model exporters with output-scope enforcement."""

from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import tempfile

from .artifact_validator import artifact_receipt
from .errors import HarnessError
from .media_probe import probe_video


SUPPORTED_FORMATS = {"blend", "glb", "gltf", "fbx", "obj", "stl", "png", "jpg", "mp4"}
FORMAT_PARAMETERS = {
    'blend': set(), 'png': set(), 'jpg': set(),
    'glb': {'use_selection','use_visible','use_renderable','export_apply','export_animations','export_materials'},
    'gltf': {'use_selection','use_visible','use_renderable','export_apply','export_animations','export_materials'},
    'fbx': {'use_selection','use_visible','use_active_collection','bake_anim','apply_scale_options'},
    'obj': {'export_selected_objects','apply_modifiers','export_materials','export_uv'},
    'stl': {'export_selected_objects','apply_modifiers','global_scale'},
    'mp4': {'frameStart','frameEnd'},
}


class Exporter:
    def __init__(self, bpy_module, *, approved_output_root: Path, encode_runner=None, video_probe=None):
        self.bpy = bpy_module
        self._encode_runner = encode_runner or self._encode_ffmpeg
        self._custom_encode_runner = encode_runner is not None
        self._video_probe = video_probe or self._probe_video
        self.root = Path(approved_output_root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        path: Path,
        *,
        session_id: str,
        scene_revision: int,
        snapshot_id: str,
        overwrite: bool = False,
        parameters: dict | None = None,
    ) -> dict:
        path = Path(path)
        if path.is_symlink():
            raise HarnessError("OUTPUT_NOT_AUTHORIZED", f"output must not be a symlink: {path}")
        resolved = path.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError:
            raise HarnessError("OUTPUT_NOT_AUTHORIZED", f"output is outside approved root: {resolved}")
        if resolved.exists() and not overwrite:
            raise HarnessError("OVERWRITE_AUTHORIZATION_REQUIRED", f"output already exists: {resolved}")
        resolved.parent.mkdir(parents=True, exist_ok=True)
        format_name = resolved.suffix.lower().lstrip(".")
        if format_name not in SUPPORTED_FORMATS:
            raise HarnessError("UNSUPPORTED_FORMAT", f"unsupported export format: {format_name}")
        receipt_parameters = dict(parameters or {})
        unknown=sorted(set(receipt_parameters)-FORMAT_PARAMETERS[format_name])
        if unknown:
            raise HarnessError('INVALID_ARGUMENT',f'unsupported {format_name} export parameters: {unknown}')
        for key,value in receipt_parameters.items():
            if key in {'frameStart','frameEnd'} and type(value) is not int:
                raise HarnessError('INVALID_ARGUMENT',f'{key} must be an integer')
            if key.startswith('use_') or key in {'export_apply','export_animations','bake_anim','export_selected_objects','apply_modifiers','export_uv'}:
                if type(value) is not bool:raise HarnessError('INVALID_ARGUMENT',f'{key} must be boolean')
        self._run_export(format_name, resolved, receipt_parameters)
        checks = ["exists", "non_empty", "sha256"]
        if format_name == "mp4":
            receipt_parameters["media"] = self._video_probe(resolved)
            checks.append("media")
        return artifact_receipt(
            resolved,
            format_name=format_name,
            session_id=session_id,
            scene_revision=scene_revision,
            snapshot_id=snapshot_id,
            parameters=receipt_parameters,
            checks=checks,
        )

    def _run_export(self, format_name: str, path: Path, parameters: dict) -> None:
        filepath = str(path)
        if format_name == "blend":
            self.bpy.ops.wm.save_as_mainfile(filepath=filepath)
        elif format_name in {"glb", "gltf"}:
            export_format = "GLB" if format_name == "glb" else "GLTF_SEPARATE"
            self.bpy.ops.export_scene.gltf(filepath=filepath, export_format=export_format, **parameters)
        elif format_name == "fbx":
            self.bpy.ops.export_scene.fbx(filepath=filepath, **parameters)
        elif format_name == "obj":
            self.bpy.ops.wm.obj_export(filepath=filepath, **parameters)
        elif format_name == "stl":
            self.bpy.ops.wm.stl_export(filepath=filepath, **parameters)
        elif format_name in {"png", "jpg", "mp4"}:
            self._render_media(format_name, path, parameters)

    def _render_media(self, format_name: str, path: Path, parameters: dict) -> None:
        scene = self.bpy.context.scene
        render = scene.render
        image_settings = render.image_settings
        ffmpeg = getattr(render, "ffmpeg", None)
        previous = {
            "filepath": render.filepath,
            "file_format": image_settings.file_format,
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
        }
        if ffmpeg is not None:
            previous.update(
                {
                    "ffmpeg_format": ffmpeg.format,
                    "ffmpeg_codec": ffmpeg.codec,
                    "ffmpeg_quality": ffmpeg.constant_rate_factor,
                }
            )
        try:
            render.filepath = str(path)
            if format_name in {"png", "jpg"}:
                image_settings.file_format = "PNG" if format_name == "png" else "JPEG"
                self.bpy.ops.render.render(write_still=True)
            else:
                image_settings.file_format = "PNG"
                if "frameStart" in parameters:
                    scene.frame_start = int(parameters["frameStart"])
                if "frameEnd" in parameters:
                    scene.frame_end = int(parameters["frameEnd"])
                with tempfile.TemporaryDirectory(prefix="codex-blender-frames-") as directory:
                    prefix = Path(directory) / "frame_"
                    render.filepath = str(prefix)
                    self.bpy.ops.render.render(animation=True)
                    audio_path = None
                    editor = getattr(scene, 'sequence_editor', None)
                    if editor is not None and any(strip.type == 'SOUND' and not strip.mute for strip in editor.strips):
                        audio_path = Path(directory) / 'mix.wav'
                        self.bpy.ops.sound.mixdown(filepath=str(audio_path), container='WAV', codec='PCM')
                    base = (str(prefix) + "%04d.png", path, int(getattr(scene.render, "fps", 24) or 24), int(scene.frame_start))
                    if self._custom_encode_runner:
                        self._encode_runner(*base)
                    else:
                        self._encode_ffmpeg(*base, audio_path=audio_path)
        finally:
            render.filepath = previous["filepath"]
            image_settings.file_format = previous["file_format"]
            scene.frame_start = previous["frame_start"]
            scene.frame_end = previous["frame_end"]
            if ffmpeg is not None:
                ffmpeg.format = previous["ffmpeg_format"]
                ffmpeg.codec = previous["ffmpeg_codec"]
                ffmpeg.constant_rate_factor = previous["ffmpeg_quality"]

    @staticmethod
    def _encode_ffmpeg(pattern: str, target: Path, fps: int, start_frame: int, audio_path: Path | None = None) -> None:
        executable = os.environ.get("CODEX_BLENDER_FFMPEG") or shutil.which("ffmpeg")
        if not executable or not Path(executable).is_file():
            raise HarnessError("DEPENDENCY_MISSING", "ffmpeg is required for MP4 export")
        command = [
            executable, "-y", "-framerate", str(fps), "-start_number", str(start_frame),
            "-i", pattern,
        ]
        if audio_path is not None:
            command.extend(['-i', str(audio_path)])
        command.extend(["-vf", "format=yuv420p", "-c:v", "libx264", "-tag:v", "avc1"])
        if audio_path is not None:
            command.extend(['-c:a','aac','-shortest'])
        command.extend(["-movflags", "+faststart", str(target)])
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=900)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
            raise HarnessError("MEDIA_ENCODE_FAILED", f"ffmpeg failed: {exc}") from exc

    @staticmethod
    def _probe_video(path: Path) -> dict:
        executable = os.environ.get("CODEX_BLENDER_FFPROBE") or shutil.which("ffprobe")
        if not executable or not Path(executable).is_file():
            raise HarnessError("DEPENDENCY_MISSING", "ffprobe is required for MP4 validation")
        return probe_video(path, Path(executable))
