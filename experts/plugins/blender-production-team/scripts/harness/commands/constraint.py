"""Typed bone and object constraints with influence animation."""
from ..errors import HarnessError
from ..identity import ObjectResolver
from .validation import finite_number,require_name,vector3


class ConstraintCommands:
    def __init__(self,bpy_module): self.bpy=bpy_module; self.objects=ObjectResolver(bpy_module)

    def _arm_bone(self,arguments):
        arm=self.objects.resolve({'objectId':arguments.get('armatureId')},required_type={'ARMATURE'})
        bone=arm.pose.bones.get(require_name(arguments.get('bone')))
        if bone is None: raise HarnessError('BONE_NOT_FOUND','pose bone was not found')
        return arm,bone

    def add_bone(self,arguments):
        arm,bone=self._arm_bone(arguments); kind=str(arguments.get('type','')).upper(); name=require_name(arguments.get('name'))
        if bone.constraints.get(name): raise HarnessError('NAME_COLLISION',f'constraint already exists: {name}')
        if kind not in {'IK','LIMIT_ROTATION','COPY_TRANSFORMS'}: raise HarnessError('INVALID_ARGUMENT','unsupported bone constraint')
        c=bone.constraints.new(kind); c.name=name
        try:
            if kind=='IK':
                c.target=self.objects.resolve({'objectId':arguments.get('targetObjectId')})
                pole=arguments.get('poleObjectId'); c.pole_target=self.objects.resolve({'objectId':pole}) if pole else None
                chain=arguments.get('chainLength',2)
                if type(chain) is not int or chain<1: raise HarnessError('INVALID_ARGUMENT','chainLength must be positive')
                c.chain_count=chain; c.pole_angle=finite_number(arguments.get('poleAngle',0),'poleAngle')
            elif kind=='COPY_TRANSFORMS':
                c.target=self.objects.resolve({'objectId':arguments.get('targetObjectId')}); c.subtarget=str(arguments.get('subtarget',''))
            else:
                minimum=vector3(arguments.get('minRotation',[-3.14159]*3),'minRotation'); maximum=vector3(arguments.get('maxRotation',[3.14159]*3),'maxRotation')
                if any(a>b for a,b in zip(minimum,maximum)): raise HarnessError('INVALID_ARGUMENT','rotation minimum exceeds maximum')
                for axis,low,high in zip('xyz',minimum,maximum):
                    setattr(c,'use_limit_'+axis,True); setattr(c,'min_'+axis,low); setattr(c,'max_'+axis,high)
                c.owner_space='LOCAL'
            c.influence=finite_number(arguments.get('influence',1),'influence',minimum=0)
            if c.influence>1: raise HarnessError('INVALID_ARGUMENT','influence must be at most 1')
        except Exception:
            bone.constraints.remove(c); raise
        return {'changedObjects':[arm.name],'result':{'armature':self.objects.receipt(arm),'bone':bone.name,'constraintName':name,'type':kind}}

    def add_object(self,arguments):
        owner=self.objects.resolve(arguments.get('owner')); kind=str(arguments.get('type','')).upper(); name=require_name(arguments.get('name'))
        if kind!='CHILD_OF': raise HarnessError('INVALID_ARGUMENT','only CHILD_OF object constraint is currently supported')
        target=self.objects.resolve(arguments.get('target'),required_type={'ARMATURE'}); bone=require_name(arguments.get('bone'))
        if target.pose.bones.get(bone) is None: raise HarnessError('BONE_NOT_FOUND','target bone was not found')
        c=owner.constraints.new('CHILD_OF'); c.name=name; c.target=target; c.subtarget=bone
        target_matrix=target.matrix_world @ target.pose.bones[bone].matrix
        c.inverse_matrix=target_matrix.inverted(); c.influence=finite_number(arguments.get('influence',1),'influence',minimum=0)
        if c.influence>1: owner.constraints.remove(c); raise HarnessError('INVALID_ARGUMENT','influence must be at most 1')
        return {'changedObjects':[owner.name],'result':{'owner':self.objects.receipt(owner),'constraintName':name,'type':kind,'bone':bone}}

    def keyframe_influence(self,arguments):
        owner=self.objects.resolve(arguments.get('owner')); name=require_name(arguments.get('constraintName'))
        c=owner.constraints.get(name); frame=arguments.get('frame'); influence=finite_number(arguments.get('influence'),'influence',minimum=0)
        if c is None: raise HarnessError('CONSTRAINT_NOT_FOUND','object constraint was not found')
        if type(frame) is not int or influence>1: raise HarnessError('INVALID_ARGUMENT','frame/influence is invalid')
        c.influence=influence; c.keyframe_insert(data_path='influence',frame=frame)
        action=getattr(getattr(owner,'animation_data',None),'action',None)
        if action:
            for curve in getattr(action,'fcurves',()):
                if f'constraints["{name}"]' in curve.data_path:
                    for point in curve.keyframe_points: point.interpolation='CONSTANT'
        return {'changedObjects':[owner.name],'result':{'constraintName':name,'frame':frame,'influence':influence}}
