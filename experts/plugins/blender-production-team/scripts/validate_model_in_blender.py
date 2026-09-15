"""Blender-side entrypoint used by isolated model re-import validation."""

import json
import sys
from pathlib import Path

import bpy


def main(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=str(path))
    elif suffix == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(path))
    elif suffix == ".obj":
        bpy.ops.wm.obj_import(filepath=str(path))
    elif suffix == ".stl":
        bpy.ops.wm.stl_import(filepath=str(path))
    elif suffix == ".blend":
        bpy.ops.wm.open_mainfile(filepath=str(path))
    else:
        raise ValueError(f"unsupported re-import format: {suffix}")
    objects = list(bpy.context.scene.objects)
    print(
        "CODEX_REIMPORT="
        + json.dumps(
            {
                "objects": len(objects),
                "meshes": sum(obj.type == "MESH" for obj in objects),
                "materials": len(bpy.data.materials),
                "names": sorted(obj.name for obj in objects),
            }
        )
    )


if __name__ == "__main__":
    separator = sys.argv.index("--")
    main(Path(sys.argv[separator + 1]))

