"""Camera creation and activation."""

from __future__ import annotations

from .validation import require_name, vector3, finite_number
from ..errors import HarnessError


class CameraCommands:
    def __init__(self, bpy_module):
        self.bpy = bpy_module

    def create(self, arguments: dict) -> dict:
        name = require_name(arguments.get("name"))
        if self.bpy.data.objects.get(name) is not None:
            raise HarnessError("NAME_COLLISION", f"object already exists: {name}")
        location = vector3(arguments.get("location", [0, 0, 0]), "location")
        rotation = vector3(arguments.get("rotation", [0, 0, 0]), "rotation")
        lens = finite_number(arguments.get('lens', 50.0), 'lens', positive=True)
        if not isinstance(arguments.get('active', False), bool):
            raise HarnessError('INVALID_ARGUMENT', 'active must be boolean')
        self.bpy.ops.object.camera_add(location=location, rotation=rotation)
        camera = self.bpy.context.object
        old_name = camera.name
        camera.name = name
        if isinstance(self.bpy.data.objects, dict):
            self.bpy.data.objects.pop(old_name)
            self.bpy.data.objects[name] = camera
        camera.data.lens = lens
        if arguments.get("active", False):
            self.bpy.context.scene.camera = camera
        return {"changedObjects": [name], "result": {"name": name}}

    def aim_at(self,arguments):
        from mathutils import Vector
        name=require_name(arguments.get('name')); camera=self.bpy.data.objects.get(name)
        if camera is None or camera.type!='CAMERA': raise HarnessError('OBJECT_NOT_FOUND','camera was not found')
        if 'targetObject' in arguments:
            target=self.bpy.data.objects.get(require_name(arguments.get('targetObject')))
            if target is None: raise HarnessError('OBJECT_NOT_FOUND','target object was not found')
            point=target.matrix_world.translation
        else:
            point=Vector(vector3(arguments.get('target'),'target'))
        direction=point-camera.matrix_world.translation
        if direction.length==0: raise HarnessError('INVALID_ARGUMENT','camera and target must differ')
        camera.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
        return {'changedObjects':[camera.name],'result':{'name':camera.name,'target':list(point)}}
