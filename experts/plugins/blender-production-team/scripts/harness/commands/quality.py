"""Explicit frame/object quality measurements; no inferred performance intent."""
import math
from ..errors import HarnessError
from ..identity import ObjectResolver
from .validation import finite_number,require_name,vector3


class QualityCommands:
    def __init__(self,bpy_module): self.bpy=bpy_module; self.objects=ObjectResolver(bpy_module)
    def _range(self,args):
        start,end=args.get('frameStart'),args.get('frameEnd')
        if type(start) is not int or type(end) is not int or start>end: raise HarnessError('INVALID_ARGUMENT','frame range is invalid')
        return range(start,end+1)
    def _arm_bone(self,args):
        arm=self.objects.resolve(args.get('armature'),required_type={'ARMATURE'}); bone=arm.pose.bones.get(require_name(args.get('bone')))
        if bone is None: raise HarnessError('BONE_NOT_FOUND','bone was not found')
        return arm,bone
    def foot_drift(self,args):
        arm,bone=self._arm_bone(args); points=[]; previous=self.bpy.context.scene.frame_current
        try:
            for frame in self._range(args):
                self.bpy.context.scene.frame_set(frame); points.append((arm.matrix_world@bone.matrix).translation.copy())
        finally:self.bpy.context.scene.frame_set(previous)
        drift=max((point-points[0]).length for point in points); limit=finite_number(args.get('limit',.01),'limit',minimum=0)
        return {'changedObjects':[],'result':{'object':arm.name,'bone':bone.name,'maxDrift':drift,'limit':limit,'passed':drift<=limit}}
    def limb_length(self,args):
        arm=self.objects.resolve(args.get('armature'),required_type={'ARMATURE'}); names=args.get('bones'); previous=self.bpy.context.scene.frame_current
        if not isinstance(names,list) or not names: raise HarnessError('INVALID_ARGUMENT','bones are required')
        rest={name:arm.data.bones[name].length if arm.data.bones.get(name) else None for name in names}
        if any(v is None for v in rest.values()): raise HarnessError('BONE_NOT_FOUND','bone list contains a missing bone')
        error=0
        try:
            for frame in self._range(args):
                self.bpy.context.scene.frame_set(frame)
                for name in names:
                    posed=(arm.matrix_world@arm.pose.bones[name].tail-arm.matrix_world@arm.pose.bones[name].head).length
                    error=max(error,abs(posed-rest[name])/rest[name])
        finally:self.bpy.context.scene.frame_set(previous)
        limit=finite_number(args.get('limit',.005),'limit',minimum=0)
        return {'changedObjects':[],'result':{'maxRelativeError':error,'limit':limit,'passed':error<=limit}}
    def floor_penetration(self,args):
        from mathutils import Vector
        obj=self.objects.resolve(args.get('object')); floor=finite_number(args.get('floorZ',0),'floorZ'); previous=self.bpy.context.scene.frame_current; minimum=float('inf')
        try:
            for frame in self._range(args):
                self.bpy.context.scene.frame_set(frame); minimum=min(minimum,min((obj.matrix_world@Vector(corner)).z for corner in obj.bound_box))
        finally:self.bpy.context.scene.frame_set(previous)
        limit=finite_number(args.get('limit',.002),'limit',minimum=0); penetration=max(0,floor-minimum)
        return {'changedObjects':[],'result':{'minimumZ':minimum,'floorZ':floor,'penetration':penetration,'limit':limit,'passed':penetration<=limit}}
    def prop_handoff(self,args):
        prop=self.objects.resolve(args.get('object')); arm,bone=self._arm_bone(args); start,end=self._range(args).start,self._range(args).stop-1
        catch=args.get('catchFrame'); constraint_name=require_name(args.get('constraintName')); constraint=prop.constraints.get(constraint_name)
        if type(catch) is not int or constraint is None: raise HarnessError('INVALID_ARGUMENT','catchFrame/constraint is invalid')
        previous=self.bpy.context.scene.frame_current; distances=[]
        try:
            for frame in range(start,end+1):
                self.bpy.context.scene.frame_set(frame); hand=(arm.matrix_world@bone.matrix).translation; distances.append((frame,(prop.matrix_world.translation-hand).length,constraint.influence))
            self.bpy.context.scene.frame_set(catch); before=prop.matrix_world.copy(); self.bpy.context.scene.frame_set(catch+1); after=prop.matrix_world.copy()
        finally:self.bpy.context.scene.frame_set(previous)
        run=max_run=0
        for _,distance,influence in distances:
            run=run+1 if distance>=.05 and influence<=1e-6 else 0; max_run=max(max_run,run)
        position=(after.translation-before.translation).length; angle=before.to_quaternion().rotation_difference(after.to_quaternion()).angle
        passed=max_run>=6 and position<=.01 and angle<=math.radians(2)
        return {'changedObjects':[],'result':{'releaseRunFrames':max_run,'maxDistance':max(d[1] for d in distances),
                'catchPositionJump':position,'catchRotationJumpDegrees':math.degrees(angle),'passed':passed}}
    def camera_visibility(self,args):
        from bpy_extras.object_utils import world_to_camera_view
        from mathutils import Vector
        camera=self.objects.resolve(args.get('camera'),required_type={'CAMERA'}); locators=args.get('objects')
        if not isinstance(locators,list) or not locators: raise HarnessError('INVALID_ARGUMENT','objects are required')
        objects=[self.objects.resolve(locator) for locator in locators]; missed=[]; previous=self.bpy.context.scene.frame_current
        try:
            for frame in self._range(args):
                self.bpy.context.scene.frame_set(frame)
                for obj in objects:
                    projected=[world_to_camera_view(self.bpy.context.scene,camera,obj.matrix_world@Vector(c)) for c in obj.bound_box]
                    if not any(0<=p.x<=1 and 0<=p.y<=1 and p.z>0 for p in projected): missed.append({'frame':frame,'object':obj.name})
        finally:self.bpy.context.scene.frame_set(previous)
        return {'changedObjects':[],'result':{'missed':missed,'passed':not missed}}
    def motion_discontinuity(self,args):
        obj=self.objects.resolve(args.get('object')); pos_limit=finite_number(args.get('positionLimit'),'positionLimit',minimum=0); angle_limit=finite_number(args.get('angleLimitDegrees'),'angleLimitDegrees',minimum=0)
        previous=self.bpy.context.scene.frame_current; samples=[]; issues=[]
        try:
            for frame in self._range(args):
                self.bpy.context.scene.frame_set(frame); samples.append((frame,obj.matrix_world.copy()))
        finally:self.bpy.context.scene.frame_set(previous)
        for (frame_a,a),(frame_b,b) in zip(samples,samples[1:]):
            distance=(b.translation-a.translation).length; angle=math.degrees(a.to_quaternion().rotation_difference(b.to_quaternion()).angle)
            if distance>pos_limit or angle>angle_limit: issues.append({'from':frame_a,'to':frame_b,'position':distance,'angleDegrees':angle})
        return {'changedObjects':[],'result':{'issues':issues,'passed':not issues}}
