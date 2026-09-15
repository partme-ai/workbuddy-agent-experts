"""Read-only scene commands."""

from __future__ import annotations

from pathlib import Path


class SceneCommands:
    def __init__(self, bpy_module):
        self.bpy = bpy_module

    def inspect(self, _arguments: dict) -> dict:
        objects = sorted(self.bpy.data.objects, key=lambda item: item.name)
        materials = list(getattr(self.bpy.data, "materials", ()))
        counts = {
            "objects": len(objects),
            "materials": len(materials),
            "lights": sum(obj.type == "LIGHT" for obj in objects),
            "cameras": sum(obj.type == "CAMERA" for obj in objects),
        }
        scene = self.bpy.context.scene
        collections = sorted(collection.name for collection in getattr(self.bpy.data, "collections", ()))
        material_names = sorted(material.name for material in materials)
        warnings = []
        missing_assets = []
        for image in getattr(self.bpy.data, "images", ()):
            filepath = getattr(image, "filepath", "")
            if not filepath or getattr(image, "source", "") != "FILE":
                continue
            try:
                resolved = Path(self.bpy.path.abspath(filepath)).resolve()
            except Exception:
                resolved = Path(filepath)
            if not resolved.is_file():
                missing_assets.append(str(resolved))
        if missing_assets:
            warnings.append("MISSING_ASSETS")
        return {
            "changedObjects": [],
            "result": {
                "objects": [obj.name for obj in objects],
                "objectDetails": [{"name": obj.name, "type": obj.type} for obj in objects],
                "collections": collections,
                "materials": material_names,
                "lights": [obj.name for obj in objects if obj.type == "LIGHT"],
                "cameras": [obj.name for obj in objects if obj.type == "CAMERA"],
                "summary": counts,
                "frameRange": {"start": int(scene.frame_start), "end": int(scene.frame_end)},
                "activeCamera": getattr(getattr(scene, "camera", None), "name", None),
                "currentFrame": int(getattr(scene, "frame_current", scene.frame_start)),
                "sceneName": getattr(scene, "name", "Scene"),
                "filepath": getattr(self.bpy.data, "filepath", ""),
                "missingAssets": missing_assets,
                "warnings": warnings,
            },
        }
