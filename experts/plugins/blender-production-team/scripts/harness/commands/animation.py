"""Frame range and keyframe commands."""

from __future__ import annotations

from .validation import require_name,vector3
from ..errors import HarnessError


class AnimationCommands:
    def __init__(self, bpy_module):
        self.bpy = bpy_module

    def set_frame_range(self, arguments: dict) -> dict:
        start = arguments.get("start")
        end = arguments.get("end")
        if isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, int) or not isinstance(end, int) or start > end:
            raise HarnessError("INVALID_ARGUMENT", "frame range requires integer start <= end")
        scene = self.bpy.context.scene
        scene.frame_start = start
        scene.frame_end = end
        return {"changedObjects": [], "result": {"start": start, "end": end}}

    def insert_keyframe(self, arguments: dict) -> dict:
        name = require_name(arguments.get("object"))
        data_path = require_name(arguments.get("dataPath"))
        frame = arguments.get("frame")
        if isinstance(frame, bool) or not isinstance(frame, int):
            raise HarnessError("INVALID_ARGUMENT", "frame must be an integer")
        obj = self.bpy.data.objects.get(name)
        if obj is None:
            raise HarnessError("OBJECT_NOT_FOUND", f"object not found: {name}")
        obj.keyframe_insert(data_path=data_path, frame=frame)
        return {"changedObjects": [name]}

    def pose_keyframe(self,arguments):
        armature=self.bpy.data.objects.get(require_name(arguments.get('armature')))
        if armature is None or armature.type!='ARMATURE': raise HarnessError('OBJECT_NOT_FOUND','armature was not found')
        bone=armature.pose.bones.get(require_name(arguments.get('bone')))
        if bone is None: raise HarnessError('BONE_NOT_FOUND','pose bone was not found')
        path=require_name(arguments.get('dataPath')); frame=arguments.get('frame'); value=arguments.get('value')
        if path not in {'location','rotation_euler','scale'} or type(frame) is not int:
            raise HarnessError('INVALID_ARGUMENT','unsupported pose dataPath or frame')
        setattr(bone,path,vector3(value,'value')); bone.rotation_mode='XYZ'; bone.keyframe_insert(data_path=path,frame=frame)
        return {'changedObjects':[armature.name],'result':{'bone':bone.name,'dataPath':path,'frame':frame}}
