"""Persistent Blender checkpoint capture and verified restore."""

from __future__ import annotations

import json
import secrets
from pathlib import Path


class BlenderCheckpointStore:
    def __init__(self, bpy_module, checkpoint_dir: Path):
        self.bpy = bpy_module
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def signature(self) -> str:
        scene = self.bpy.context.scene
        objects = []
        for obj in sorted(self.bpy.data.objects, key=lambda item: item.name):
            objects.append(
                {
                    "name": obj.name,
                    "type": obj.type,
                    "location": self._vector(obj.location),
                    "rotation": self._vector(obj.rotation_euler),
                    "scale": self._vector(obj.scale),
                }
            )
        return json.dumps(
            {
                "objects": objects,
                "frameStart": int(scene.frame_start),
                "frameEnd": int(scene.frame_end),
                "camera": getattr(getattr(scene, "camera", None), "name", None),
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def capture(self) -> dict:
        path = self.checkpoint_dir / ("checkpoint-" + secrets.token_hex(12) + ".blend")
        signature = self.signature()
        self.bpy.ops.wm.save_as_mainfile(filepath=str(path), copy=True, check_existing=False)
        return {"path": str(path), "signature": signature}

    def restore(self, snapshot: dict) -> bool:
        path = Path(snapshot["path"])
        if not path.is_file():
            return False
        self.bpy.ops.wm.open_mainfile(filepath=str(path))
        return self.signature() == snapshot["signature"]

    @staticmethod
    def _vector(value):
        return [round(float(component), 9) for component in value]

