"""Closed foreground inspection commands; never save or change scene content."""
from ..errors import HarnessError


class ViewCommands:
    def __init__(self, bpy_module):
        self.bpy = bpy_module
        self.review_window = None

    def present(self, arguments):
        window, area, region = self._context()
        windows = list(self.bpy.context.window_manager.windows)
        if self.review_window not in windows:
            with self.bpy.context.temp_override(window=window, area=area, region=region):
                self.bpy.ops.wm.window_new()
            created = [w for w in self.bpy.context.window_manager.windows if w not in windows]
            if not created:
                raise HarnessError("FRONTEND_UNAVAILABLE", "Blender did not create a review window")
            self.review_window = created[0]
        return {"changedObjects": [], "result": {"presented": True, "scene": self.review_window.scene.name,
                                                  "windowCount": len(self.bpy.context.window_manager.windows)}}

    def _context(self):
        wm = getattr(self.bpy.context, "window_manager", None)
        windows = list(getattr(wm, "windows", ()))
        active = getattr(self.bpy.context, "window", None)
        if active in windows:
            windows.remove(active)
            windows.insert(0, active)
        for window in windows:
            if getattr(window, "scene", self.bpy.context.scene) != self.bpy.context.scene:
                continue
            for area in window.screen.areas:
                if area.type == "VIEW_3D":
                    for region in area.regions:
                        if region.type == "WINDOW":
                            return window, area, region
        raise HarnessError("FRONTEND_UNAVAILABLE", "no foreground 3D viewport is available")

    def set_view(self, arguments):
        view = arguments.get("view")
        if view not in {"CAMERA", "FRONT", "SIDE", "TOP"}:
            raise HarnessError("INVALID_ARGUMENT", "view must be CAMERA, FRONT, SIDE or TOP")
        window, area, region = self._context()
        if view == "CAMERA":
            if self.bpy.context.scene.camera is None:
                raise HarnessError("CAMERA_REQUIRED", "create or select an active camera first")
            area.spaces.active.region_3d.view_perspective = "CAMERA"
        else:
            with self.bpy.context.temp_override(window=window, area=area, region=region):
                self.bpy.ops.view3d.view_axis(type={"SIDE": "RIGHT"}.get(view, view))
        area.tag_redraw()
        return {"changedObjects": [], "result": {"view": view}}

    def focus(self, arguments):
        name = arguments.get("object")
        obj = self.bpy.data.objects.get(name) if isinstance(name, str) else None
        if obj is None:
            raise HarnessError("OBJECT_NOT_FOUND", "focus requires an existing object")
        _window, area, _region = self._context()
        from mathutils import Vector
        points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        center = sum(points, Vector()) / len(points)
        radius = max((point - center).length for point in points)
        view = area.spaces.active.region_3d
        view.view_perspective = "PERSP"
        view.view_location = center
        view.view_distance = max(radius * 3, 1.0)
        area.tag_redraw()
        return {"changedObjects": [], "result": {"focusedObject": name}}

    def set_frame(self, arguments):
        frame = arguments.get("frame")
        scene = self.bpy.context.scene
        if type(frame) is not int or not scene.frame_start <= frame <= scene.frame_end:
            raise HarnessError("INVALID_ARGUMENT", "frame must be an integer inside the scene frame range")
        scene.frame_set(frame)
        return {"changedObjects": [], "result": {"frame": scene.frame_current}}

    def set_playback(self, arguments):
        playing = arguments.get("playing")
        if type(playing) is not bool:
            raise HarnessError("INVALID_ARGUMENT", "playing must be boolean")
        window, area, region = self._context()
        if bool(window.screen.is_animation_playing) != playing:
            with self.bpy.context.temp_override(window=window, area=area, region=region):
                if playing:
                    self.bpy.ops.screen.animation_play()
                else:
                    self.bpy.ops.screen.animation_cancel(restore_frame=False)
        return {"changedObjects": [], "result": {"playing": bool(window.screen.is_animation_playing)}}
