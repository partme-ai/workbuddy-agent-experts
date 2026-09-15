"""Worker-side rendering and composition for durable frame-sequence jobs."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from .errors import HarnessError
from .frame_pipeline import (
    build_compose_command,
    inspect_frame_sequence,
    sha256_file,
    write_concat_manifest,
)
from .media_probe import probe_video


def _atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _entry(frame: int, path: Path) -> dict:
    return {"frame": frame, "path": str(path.resolve()), "bytes": path.stat().st_size,
            "sha256": sha256_file(path)}


def _sound_strips(scene):
    editor = getattr(scene, "sequence_editor", None)
    strips = getattr(editor, "strips", ()) if editor is not None else ()
    return [strip for strip in strips if getattr(strip, "type", None) == "SOUND" and not getattr(strip, "mute", False)]


def _effective_fps(render) -> float:
    base = float(getattr(render, "fps_base", 1.0) or 1.0)
    return float(getattr(render, "fps", 24) or 24) / base


def render_frame_sequence(bpy_module, task_dir: Path, spec: dict, status_writer=lambda _status: None) -> dict:
    task_dir = Path(task_dir).resolve()
    parameters = spec["parameters"]
    frames_dir = task_dir / "frames"
    frames_dir.mkdir(exist_ok=True)
    manifest_path = task_dir / "frame-sequence.json"
    base_manifest = {
        "receiptVersion": "3.0.0",
        "protocolVersion": "codex-blender/v1",
        "producer": {"name": "codex-blender", "version": "0.3.0"},
        "jobId": spec["jobId"],
        "snapshotSha256": spec["snapshot"]["sha256"],
        "frameStart": parameters["frameStart"],
        "frameEnd": parameters["frameEnd"],
        "frameStep": parameters["frameStep"],
        "format": parameters["imageFormat"],
        "width": parameters["width"],
        "height": parameters["height"],
        "colorMode": parameters["colorMode"],
        "colorDepth": parameters["colorDepth"],
        "frames": [],
    }
    if manifest_path.is_file():
        try:
            prior = json.loads(manifest_path.read_text(encoding="utf-8"))
            if prior.get("snapshotSha256") not in {None, spec["snapshot"]["sha256"]}:
                raise HarnessError("JOB_NOT_RESUMABLE", "frame manifest belongs to another snapshot")
            base_manifest["frames"] = prior.get("frames", [])
        except json.JSONDecodeError:
            base_manifest["frames"] = []
    inspection = inspect_frame_sequence(base_manifest, task_dir)
    entries = {entry["frame"]: entry for entry in base_manifest["frames"]
               if isinstance(entry, dict) and entry.get("frame") in inspection["complete"]}
    pending = sorted(inspection["missing"] + inspection["corrupt"])
    reused = list(inspection["complete"])
    rendered = []
    scene = bpy_module.context.scene
    render = scene.render
    image = render.image_settings
    previous = {"filepath": render.filepath, "width": render.resolution_x, "height": render.resolution_y,
                "percentage": render.resolution_percentage, "format": image.file_format,
                "media_type": getattr(image, "media_type", None),
                "mode": getattr(image, "color_mode", None), "depth": getattr(image, "color_depth", None),
                "frame": scene.frame_current}
    try:
        render.resolution_x = parameters["width"]
        render.resolution_y = parameters["height"]
        render.resolution_percentage = 100
        if hasattr(image, "media_type"):
            image.media_type = "MULTI_LAYER_IMAGE" if parameters["imageFormat"] == "OPEN_EXR_MULTILAYER" else "IMAGE"
        image.file_format = parameters["imageFormat"]
        image.color_mode = parameters["colorMode"]
        image.color_depth = parameters["colorDepth"]
        for index, frame in enumerate(pending, 1):
            target = frames_dir / f"frame_{frame:06d}.{parameters['extension']}"
            temporary = frames_dir / f".frame_{frame:06d}.tmp.{parameters['extension']}"
            scene.frame_set(frame)
            render.filepath = str(temporary)
            bpy_module.ops.render.render(write_still=True)
            if not temporary.is_file() or temporary.stat().st_size <= 0:
                raise HarnessError("ARTIFACT_INVALID", f"rendered frame is missing or empty: {frame}")
            os.replace(temporary, target)
            entries[frame] = _entry(frame, target)
            rendered.append(frame)
            base_manifest["frames"] = [entries[value] for value in sorted(entries)]
            base_manifest["fps"] = _effective_fps(render)
            _atomic_json(manifest_path, base_manifest)
            status_writer({"completedFrames": len(reused) + index, "totalFrames": len(parameters["frames"]),
                           "currentFrame": frame})
        if parameters["includeAudio"] and _sound_strips(scene) and hasattr(getattr(bpy_module.ops, "sound", None), "mixdown"):
            audio_temp = task_dir / "mix.tmp.wav"
            audio_path = task_dir / "mix.wav"
            bpy_module.ops.sound.mixdown(filepath=str(audio_temp), container="WAV", codec="PCM")
            if audio_temp.is_file() and audio_temp.stat().st_size > 0:
                os.replace(audio_temp, audio_path)
                base_manifest["audio"] = {"path": str(audio_path), "bytes": audio_path.stat().st_size,
                                          "sha256": sha256_file(audio_path), "format": "wav"}
        base_manifest["frames"] = [entries[value] for value in parameters["frames"]]
        base_manifest["fps"] = _effective_fps(render)
        final = inspect_frame_sequence(base_manifest, task_dir)
        if not final["ready"]:
            raise HarnessError("FRAME_SEQUENCE_INCOMPLETE", "render finished with missing or corrupt frames")
        base_manifest["reusedFrames"] = reused
        base_manifest["renderedFrames"] = rendered
        base_manifest["validation"] = {"status": "passed", "checks": ["frame_count", "non_empty", "sha256", "approved_root"]}
        _atomic_json(manifest_path, base_manifest)
        return base_manifest
    finally:
        render.filepath = previous["filepath"]
        render.resolution_x = previous["width"]
        render.resolution_y = previous["height"]
        render.resolution_percentage = previous["percentage"]
        if previous["media_type"] is not None:
            image.media_type = previous["media_type"]
        image.file_format = previous["format"]
        if previous["mode"] is not None:
            image.color_mode = previous["mode"]
        if previous["depth"] is not None:
            image.color_depth = previous["depth"]
        scene.frame_set(previous["frame"])


def compose_video(task_dir: Path, spec: dict, *, runner=subprocess.run, ffmpeg_path: Path | None = None,
                  video_probe=None) -> dict:
    task_dir = Path(task_dir).resolve()
    source = spec["sourceSequence"]
    manifest_path = Path(source["manifestPath"]).resolve()
    expected_manifest = (task_dir.parent / source["jobId"] / "frame-sequence.json").resolve()
    if source["jobId"] != spec["parameters"]["sourceJobId"] or manifest_path != expected_manifest:
        raise HarnessError("SOURCE_NOT_AUTHORIZED", "frame sequence is outside the declared source job")
    if not manifest_path.is_file() or hashlib.sha256(manifest_path.read_bytes()).hexdigest() != source["manifestSha256"]:
        raise HarnessError("SOURCE_CHANGED", "frame sequence manifest changed after compose submission")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_root = manifest_path.parent
    inspection = inspect_frame_sequence(manifest, source_root)
    if not inspection["ready"]:
        raise HarnessError("FRAME_SEQUENCE_INCOMPLETE", "source sequence has missing or corrupt frames")
    concat_file = write_concat_manifest(manifest, source_root, task_dir / "frames.ffconcat")
    executable = Path(ffmpeg_path) if ffmpeg_path is not None else Path(shutil.which("ffmpeg") or "")
    if not executable.is_file():
        raise HarnessError("DEPENDENCY_MISSING", "ffmpeg is required for video composition")
    audio_path = None
    audio = manifest.get("audio")
    if spec["parameters"].get("includeAudio", True) and isinstance(audio, dict):
        candidate = Path(audio.get("path", "")).resolve()
        try:
            candidate.relative_to(source_root)
        except ValueError as exc:
            raise HarnessError("ARTIFACT_INVALID", "audio escaped the source job directory") from exc
        if not candidate.is_file() or candidate.stat().st_size != audio.get("bytes") or sha256_file(candidate) != audio.get("sha256"):
            raise HarnessError("ARTIFACT_INVALID", "audio mix is missing or changed")
        audio_path = candidate
    temporary = task_dir / "artifact.tmp.mp4"
    target = task_dir / "artifact.mp4"
    command = build_compose_command(executable, concat_file, temporary, spec["parameters"],
                                    audio_path=audio_path, fps=manifest["fps"],
                                    frame_count=len(inspection["expected"]))
    process = runner(command, capture_output=True, text=True, timeout=900, check=False, shell=False)
    if process.returncode != 0:
        raise HarnessError("MEDIA_ENCODE_FAILED", str(getattr(process, "stderr", ""))[-500:] or "ffmpeg failed")
    if not temporary.is_file() or temporary.stat().st_size <= 0:
        raise HarnessError("ARTIFACT_INVALID", "ffmpeg did not produce a video")
    os.replace(temporary, target)
    if video_probe is None:
        ffprobe = Path(shutil.which("ffprobe") or "")
        if not ffprobe.is_file():
            raise HarnessError("DEPENDENCY_MISSING", "ffprobe is required for video validation")
        media = probe_video(target, ffprobe)
    else:
        media = video_probe(target)
    return {"receiptVersion": "3.0.0", "protocolVersion": "codex-blender/v1",
            "producer": {"name": "codex-blender", "version": "0.3.0"}, "jobId": spec["jobId"],
            "path": str(target), "format": "mp4", "bytes": target.stat().st_size,
            "sha256": sha256_file(target), "sourceSequence": source, "media": media,
            "validation": {"status": "passed", "checks": ["source_manifest", "frame_hashes", "ffmpeg", "ffprobe"]}}
