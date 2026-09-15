"""Generate camera/front/side/top milestone renders in Blender."""

from __future__ import annotations

from pathlib import Path

from .errors import HarnessError
from .milestone import build_milestone_receipt, view_positions


class PreviewEngine:
    def __init__(self, bpy_module):
        self.bpy = bpy_module

    def capture_milestone(self, output_dir: Path, *, milestone: str, scene_revision: int, snapshot_id: str, width: int = 512, height: int = 512):
        from mathutils import Vector

        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        scene = self.bpy.context.scene
        render = scene.render
        original = (scene.camera, render.filepath, render.resolution_x, render.resolution_y, render.resolution_percentage, render.image_settings.file_format, scene.frame_current)
        minimum, maximum = self._bounds()
        center = Vector(tuple((minimum[i] + maximum[i]) / 2 for i in range(3)))
        temporary = []
        paths = {}
        try:
            render.resolution_x = int(width)
            render.resolution_y = int(height)
            render.resolution_percentage = 100
            render.image_settings.file_format = "PNG"
            if scene.camera is None:
                position = view_positions(minimum, maximum)["front"]
                scene.camera = self._camera("CodexMilestoneCamera", position, center)
                temporary.append(scene.camera)
            primary_camera = scene.camera
            paths["camera"] = self._render(output_dir / "camera.png")
            for name, position in view_positions(minimum, maximum).items():
                camera = self._camera(f"CodexMilestone{name.title()}", position, center)
                temporary.append(camera)
                scene.camera = camera
                paths[name] = self._render(output_dir / f"{name}.png")
            if milestone == "animation":
                scene.camera = primary_camera
                samples = {
                    "first": int(scene.frame_start),
                    "middle": int((scene.frame_start + scene.frame_end) // 2),
                    "last": int(scene.frame_end),
                }
                for name, frame in samples.items():
                    scene.frame_set(frame)
                    paths[name] = self._render(output_dir / f"{name}.png")
        finally:
            scene.camera, render.filepath, render.resolution_x, render.resolution_y, render.resolution_percentage, render.image_settings.file_format, frame_current = original
            scene.frame_set(frame_current)
            for camera in temporary:
                data = camera.data
                self.bpy.data.objects.remove(camera, do_unlink=True)
                self.bpy.data.cameras.remove(data)
        return build_milestone_receipt(
            milestone,
            scene_revision=scene_revision,
            snapshot_id=snapshot_id,
            view_paths=paths,
            scene_summary=self._summary(),
        )

    def _render(self, path: Path) -> Path:
        self.bpy.context.scene.render.filepath = str(path)
        self.bpy.ops.render.render(write_still=True)
        return path

    def _bounds(self):
        from mathutils import Vector

        points = []
        for obj in self.bpy.context.scene.objects:
            if getattr(obj, "type", None) == "MESH" and not getattr(obj, "hide_render", False):
                points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
        if not points:
            return (-1.0, -1.0, -1.0), (1.0, 1.0, 1.0)
        return tuple(min(point[i] for point in points) for i in range(3)), tuple(max(point[i] for point in points) for i in range(3))

    def _camera(self, name, position, target):
        camera_data = self.bpy.data.cameras.new(name)
        camera = self.bpy.data.objects.new(name, camera_data)
        self.bpy.context.scene.collection.objects.link(camera)
        camera.location = position
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        return camera

    def _summary(self):
        objects = list(self.bpy.context.scene.objects)
        return {
            "objects": len(objects),
            "materials": len(self.bpy.data.materials),
            "lights": sum(obj.type == "LIGHT" for obj in objects),
            "cameras": sum(obj.type == "CAMERA" for obj in objects),
        }
