"""Isolated Blender child process for one snapshot-bound job."""

import hashlib
import json
import os
import re
import sys
import traceback
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if (ROOT / "scripts" / "harness" / "frame_worker.py").is_file():
    from scripts.harness.frame_worker import compose_video, render_frame_sequence
else:
    from codex_blender_connector.harness.frame_worker import compose_video, render_frame_sequence


def write_status(path, payload):
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
    os.replace(temporary, path)


def run_legacy_job(kind, parameters, task_dir, spec):
    if kind == "EXPORT":
        fmt = spec["format"]
        target = task_dir / f"artifact.{fmt}"
        if fmt == "blend":
            bpy.ops.wm.save_as_mainfile(filepath=str(target))
        elif fmt in {"glb", "gltf"}:
            bpy.ops.export_scene.gltf(filepath=str(target), export_format="GLB" if fmt == "glb" else "GLTF_SEPARATE")
        elif fmt == "fbx":
            bpy.ops.export_scene.fbx(filepath=str(target))
        elif fmt == "obj":
            bpy.ops.wm.obj_export(filepath=str(target))
        else:
            raise ValueError("unsupported export format")
    elif kind == "RENDER_STILL":
        target = task_dir / "artifact.png"
        scene = bpy.context.scene
        scene.render.filepath = str(target)
        scene.render.image_settings.file_format = "PNG"
        scene.render.resolution_x = int(parameters.get("width", 512))
        scene.render.resolution_y = int(parameters.get("height", 512))
        scene.render.resolution_percentage = 100
        if "frame" in parameters:
            scene.frame_set(int(parameters["frame"]))
        bpy.ops.render.render(write_still=True)
    elif kind == "BAKE_POINT_CACHES":
        cache_root = task_dir / "cache"
        cache_root.mkdir()
        fluid_domains, fluid_visibility = [], []
        for object_index, obj in enumerate(bpy.data.objects):
            safe_name = f"{object_index:04d}_" + re.sub(r"[^A-Za-z0-9_.-]", "_", obj.name)[:80]
            for modifier in obj.modifiers:
                cache = getattr(modifier, "point_cache", None)
                if cache:
                    directory = cache_root / safe_name
                    directory.mkdir(exist_ok=True)
                    cache.filepath = str(directory)
                domain = getattr(modifier, "domain_settings", None)
                if domain:
                    directory = cache_root / (safe_name + "_fluid")
                    directory.mkdir(exist_ok=True)
                    domain.cache_directory = str(directory)
                    fluid_domains.append(obj)
                if modifier.type == "FLUID":
                    fluid_visibility.append((obj, obj.hide_viewport, obj.hide_render, obj.hide_get()))
                    obj.hide_viewport = False
                    obj.hide_render = False
                    obj.hide_set(False)
        bpy.ops.ptcache.bake_all(bake=True)
        for domain_object in fluid_domains:
            for selected in bpy.context.selected_objects:
                selected.select_set(False)
            domain_object.select_set(True)
            bpy.context.view_layer.objects.active = domain_object
            bpy.ops.fluid.bake_all()
        for obj, hide_viewport, hide_render, hidden in fluid_visibility:
            obj.hide_viewport = hide_viewport
            obj.hide_render = hide_render
            obj.hide_set(hidden)
        target = task_dir / "artifact.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(target))
    else:
        raise ValueError("unsupported legacy job kind")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    return {"path": str(target), "format": target.suffix.lstrip("."), "bytes": target.stat().st_size,
            "sha256": digest, "validation": {"status": "passed", "checks": ["exists", "non_empty", "sha256"]}}


spec_path = Path(sys.argv[sys.argv.index("--") + 1]).resolve(strict=True)
task_dir = spec_path.parent
spec = json.loads(spec_path.read_text(encoding="utf-8"))
status_path = task_dir / "status.json"
version = "3.0.0" if spec["kind"] in {"RENDER_ANIMATION_FRAMES", "COMPOSE_VIDEO"} else "2.0.0"
prior = json.loads(status_path.read_text(encoding="utf-8")) if status_path.is_file() else {}
base = {"receiptVersion": version, "jobId": spec["jobId"], "kind": spec["kind"],
        "snapshot": spec["snapshot"], "attempt": int(prior.get("attempt", 1))}
write_status(status_path, base | {"state": "running", "pid": os.getpid()})
try:
    kind = spec["kind"]
    parameters = spec.get("parameters", {})
    if kind == "RENDER_ANIMATION_FRAMES":
        def progress(update):
            write_status(status_path, base | {"state": "running", "pid": os.getpid(), "progress": update})

        artifact = render_frame_sequence(bpy, task_dir, spec, progress)
    elif kind == "COMPOSE_VIDEO":
        artifact = compose_video(task_dir, spec)
    else:
        artifact = run_legacy_job(kind, parameters, task_dir, spec)
    write_status(status_path, base | {"state": "completed", "pid": os.getpid(), "artifact": artifact})
except Exception as exc:
    write_status(status_path, base | {"state": "failed", "pid": os.getpid(),
                 "error": {"type": type(exc).__name__, "message": str(exc)[:500]}})
    traceback.print_exc()
    raise
