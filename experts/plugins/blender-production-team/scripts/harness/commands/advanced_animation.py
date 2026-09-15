"""Blender 5 layered Action, F-Curve, NLA, shape-key and basic retarget tools."""
from ..errors import HarnessError
from ..identity import ObjectResolver
from .validation import finite_number,require_name


def action_fcurves(action):
    legacy=getattr(action,'fcurves',None)
    if legacy is not None: return list(legacy)
    curves=[]
    for layer in getattr(action,'layers',()):
        for strip in getattr(layer,'strips',()):
            for bag in getattr(strip,'channelbags',()): curves.extend(bag.fcurves)
    return curves


class AdvancedAnimationCommands:
    def __init__(self,bpy_module): self.bpy=bpy_module; self.objects=ObjectResolver(bpy_module)

    def action_list(self,_arguments):
        items=[]
        for action in self.bpy.data.actions:
            curves=action_fcurves(action); frames=[p.co.x for curve in curves for p in curve.keyframe_points]
            items.append({'name':action.name,'curves':len(curves),'frameRange':[min(frames),max(frames)] if frames else None,
                          'slots':len(getattr(action,'slots',())),'layered':not hasattr(action,'fcurves')})
        return {'changedObjects':[],'result':{'actions':items}}

    def _curve(self,arguments):
        owner=self.objects.resolve(arguments); action=getattr(getattr(owner,'animation_data',None),'action',None)
        if action is None: raise HarnessError('ACTION_NOT_FOUND','object has no active action')
        path=require_name(arguments.get('dataPath')); index=arguments.get('arrayIndex',0)
        if type(index) is not int: raise HarnessError('INVALID_ARGUMENT','arrayIndex must be integer')
        curve=next((f for f in action_fcurves(action) if f.data_path==path and f.array_index==index),None)
        if curve is None: raise HarnessError('FCURVE_NOT_FOUND','matching F-Curve was not found')
        return owner,action,curve

    def fcurve_edit(self,arguments):
        owner,action,curve=self._curve(arguments)
        time_scale=finite_number(arguments.get('timeScale',1),'timeScale',positive=True)
        time_offset=finite_number(arguments.get('timeOffset',0),'timeOffset')
        value_scale=finite_number(arguments.get('valueScale',1),'valueScale')
        value_offset=finite_number(arguments.get('valueOffset',0),'valueOffset')
        interpolation=str(arguments.get('interpolation','')).upper() if 'interpolation' in arguments else None
        if interpolation and interpolation not in {'CONSTANT','LINEAR','BEZIER'}: raise HarnessError('INVALID_ARGUMENT','unsupported interpolation')
        for point in curve.keyframe_points:
            point.co.x=point.co.x*time_scale+time_offset; point.co.y=point.co.y*value_scale+value_offset
            if interpolation: point.interpolation=interpolation
        curve.update()
        return {'changedObjects':[owner.name],'result':{'action':action.name,'dataPath':curve.data_path,
                'arrayIndex':curve.array_index,'keyframes':len(curve.keyframe_points)}}

    def fcurve_clean(self,arguments):
        owner,action,curve=self._curve(arguments);threshold=finite_number(arguments.get('threshold',.001),'threshold',minimum=0)
        points=list(curve.keyframe_points);removed=0
        for previous,current,following in zip(points,points[1:],points[2:]):
            span=following.co.x-previous.co.x
            if span<=0:continue
            factor=(current.co.x-previous.co.x)/span;expected=previous.co.y+(following.co.y-previous.co.y)*factor
            if abs(current.co.y-expected)<=threshold:
                curve.keyframe_points.remove(current);removed+=1
        curve.update()
        return {'changedObjects':[owner.name],'result':{'action':action.name,'dataPath':curve.data_path,
          'arrayIndex':curve.array_index,'removed':removed,'remaining':len(curve.keyframe_points)}}

    def nla_add_strip(self,arguments):
        owner=self.objects.resolve({'objectId':arguments.get('objectId')}); action=self.bpy.data.actions.get(require_name(arguments.get('action')))
        if action is None: raise HarnessError('ACTION_NOT_FOUND','action was not found')
        start=arguments.get('start')
        if type(start) is not int: raise HarnessError('INVALID_ARGUMENT','NLA start must be an integer frame')
        scale=finite_number(arguments.get('scale',1),'scale',positive=True)
        repeat=finite_number(arguments.get('repeat',1),'repeat',positive=True); track_name=require_name(arguments.get('track'))
        animation=owner.animation_data_create(); track=animation.nla_tracks.get(track_name) or animation.nla_tracks.new(); track.name=track_name
        strip=track.strips.new(require_name(arguments.get('name')),start,action); strip.scale=scale; strip.repeat=repeat
        blend=str(arguments.get('blendType','REPLACE')).upper()
        if blend not in {'REPLACE','COMBINE','ADD','SUBTRACT','MULTIPLY'}: track.strips.remove(strip); raise HarnessError('INVALID_ARGUMENT','unsupported NLA blend type')
        strip.blend_type=blend
        return {'changedObjects':[owner.name],'result':{'track':track.name,'strip':strip.name,'action':action.name}}

    def shape_key_add(self,arguments):
        obj=self.objects.resolve(arguments,required_type={'MESH'}); name=require_name(arguments.get('keyName'))
        if obj.data.shape_keys and obj.data.shape_keys.key_blocks.get(name): raise HarnessError('NAME_COLLISION','shape key already exists')
        from_mix=arguments.get('fromMix',False)
        if type(from_mix) is not bool:raise HarnessError('INVALID_ARGUMENT','fromMix must be boolean')
        if obj.data.shape_keys is None: obj.shape_key_add(name='Basis',from_mix=False)
        key=obj.shape_key_add(name=name,from_mix=from_mix)
        return {'changedObjects':[obj.name],'result':{'object':self.objects.receipt(obj),'keyName':key.name}}

    def shape_key_keyframe(self,arguments):
        obj=self.objects.resolve(arguments,required_type={'MESH'}); name=require_name(arguments.get('keyName'))
        key=getattr(getattr(obj.data,'shape_keys',None),'key_blocks',{}).get(name); frame=arguments.get('frame')
        value=finite_number(arguments.get('value'),'value',minimum=0)
        if key is None: raise HarnessError('SHAPE_KEY_NOT_FOUND','shape key was not found')
        if type(frame) is not int or value>1: raise HarnessError('INVALID_ARGUMENT','shape key frame/value is invalid')
        key.value=value; key.keyframe_insert(data_path='value',frame=frame)
        return {'changedObjects':[obj.name],'result':{'keyName':name,'frame':frame,'value':value}}

    def retarget(self,arguments):
        source=self.objects.resolve(arguments.get('source'),required_type={'ARMATURE'}); target=self.objects.resolve(arguments.get('target'),required_type={'ARMATURE'})
        mapping=arguments.get('boneMap'); start=arguments.get('frameStart'); end=arguments.get('frameEnd'); step=arguments.get('step',1)
        if not isinstance(mapping,dict) or not mapping or any(type(v) is not str for v in mapping.values()): raise HarnessError('INVALID_ARGUMENT','boneMap is required')
        if any(type(v) is not int for v in (start,end,step)) or start>end or step<1: raise HarnessError('INVALID_ARGUMENT','retarget frame range is invalid')
        for source_name,target_name in mapping.items():
            if source.pose.bones.get(source_name) is None or target.pose.bones.get(target_name) is None: raise HarnessError('BONE_NOT_FOUND','boneMap contains a missing bone')
        previous=self.bpy.context.scene.frame_current
        try:
            for frame in range(start,end+1,step):
                self.bpy.context.scene.frame_set(frame)
                for source_name,target_name in mapping.items():
                    source_bone=source.pose.bones[source_name]; target_bone=target.pose.bones[target_name]
                    target_bone.rotation_mode='XYZ'; target_bone.matrix_basis=source_bone.matrix_basis
                    for path in ('location','rotation_euler','scale'): target_bone.keyframe_insert(data_path=path,frame=frame)
        finally:self.bpy.context.scene.frame_set(previous)
        return {'changedObjects':[target.name],'result':{'source':source.name,'target':target.name,'frames':list(range(start,end+1,step))}}

    def camera_follow_path(self,arguments):
        camera=self.objects.resolve(arguments.get('camera'),required_type={'CAMERA'}); path=self.objects.resolve(arguments.get('path'),required_type={'CURVE'})
        name=require_name(arguments.get('name')); start=arguments.get('frameStart'); end=arguments.get('frameEnd')
        if type(start) is not int or type(end) is not int or start>=end: raise HarnessError('INVALID_ARGUMENT','camera path frame range is invalid')
        follow=camera.constraints.new('FOLLOW_PATH'); follow.name=name; follow.target=path; follow.use_fixed_location=True; follow.forward_axis='FORWARD_X'
        follow.offset_factor=0; follow.keyframe_insert(data_path='offset_factor',frame=start); follow.offset_factor=1; follow.keyframe_insert(data_path='offset_factor',frame=end)
        target=None
        if arguments.get('targetObjectId'):
            target=self.objects.resolve({'objectId':arguments['targetObjectId']}); track=camera.constraints.new('TRACK_TO'); track.name=name+' Aim'; track.target=target; track.track_axis='TRACK_NEGATIVE_Z'; track.up_axis='UP_Y'
        return {'changedObjects':[camera.name],'result':{'camera':camera.name,'path':path.name,'constraint':name,'target':target.name if target else None}}

    def camera_handheld(self,arguments):
        camera=self.objects.resolve(arguments,required_type={'CAMERA'});translation=finite_number(arguments.get('translationStrength',.015),'translationStrength',minimum=0)
        rotation=finite_number(arguments.get('rotationStrength',.01),'rotationStrength',minimum=0);noise_scale=finite_number(arguments.get('noiseScale',7),'noiseScale',positive=True);seed=arguments.get('seed',0)
        if type(seed) is not int:raise HarnessError('INVALID_ARGUMENT','seed must be integer')
        start,end=arguments.get('frameStart'),arguments.get('frameEnd')
        if type(start) is not int or type(end) is not int or start>=end:raise HarnessError('INVALID_ARGUMENT','frame range is invalid')
        for path in ('location','rotation_euler'):
            camera.keyframe_insert(data_path=path,frame=start);camera.keyframe_insert(data_path=path,frame=end)
        action=camera.animation_data.action;curves=action_fcurves(action);created=[]
        for index,curve in enumerate(curves):
            if curve.data_path not in {'location','rotation_euler'}:continue
            modifier=curve.modifiers.new('NOISE');modifier.strength=translation if curve.data_path=='location' else rotation
            modifier.scale=noise_scale;modifier.phase=seed+index*1.618;created.append({'dataPath':curve.data_path,'arrayIndex':curve.array_index})
        return {'changedObjects':[camera.name],'result':{'camera':camera.name,'noiseCurves':created,'seed':seed,'frameRange':[start,end]}}

    def driver_create(self,arguments):
        """Create an F-Curve driver on an object's property."""
        owner=self.objects.resolve(arguments.get('owner'))
        data_path=require_name(arguments.get('dataPath'))
        expression=arguments.get('expression')
        variables=arguments.get('variables',[])
        if not isinstance(expression,str) or not expression.strip():
            raise HarnessError('INVALID_ARGUMENT','expression must be a non-empty string')
        if not isinstance(variables,list):
            raise HarnessError('INVALID_ARGUMENT','variables must be a list')
        # Ensure animation data exists.
        if owner.animation_data is None:
            owner.animation_data_create()
        action=owner.animation_data.action
        if action is None:
            action=self.bpy.data.actions.new(name=owner.name+'_Action')
            owner.animation_data.action=action
        # Create a driver on the specified data path.
        # driver_add returns a single FCurve for scalar or a list for vector properties.
        try:
            driver_result=owner.driver_add(data_path)
        except Exception as exc:
            raise HarnessError('OPERATION_FAILED',f'could not add driver to {data_path}') from exc
        drivers=driver_result if isinstance(driver_result,list) else [driver_result]
        created_vars=[]
        for driver_entry in drivers:
            driver_obj=driver_entry.driver if hasattr(driver_entry,'driver') else driver_entry
            driver_obj.type='SCRIPTED'
            driver_obj.expression=expression
            for var_def in variables:
                vname=var_def.get('name','var')
                vtype=var_def.get('type','SINGLE_PROP')
                v=driver_obj.variables.new()
                v.name=vname; v.type=vtype
                if vtype=='SINGLE_PROP' and var_def.get('target'):
                    target_name=var_def['target']
                    if target_name=='self':
                        v.targets[0].id=owner
                    else:
                        target_obj=self.bpy.data.objects.get(target_name)
                        if target_obj: v.targets[0].id=target_obj
                    v.targets[0].data_path=var_def.get('dataPath','')
                created_vars.append({'name':vname,'type':vtype})
        return {'changedObjects':[owner.name],'result':{'owner':self.objects.receipt(owner),
                'dataPath':data_path,'expression':expression,'variables':created_vars,
                'driverCount':len(drivers)}}

    def keying_set_create(self,arguments):
        """Create a keying set with the given paths."""
        name=require_name(arguments.get('name'))
        paths=arguments.get('paths')
        if not isinstance(paths,list) or not paths:
            raise HarnessError('INVALID_ARGUMENT','paths must be a non-empty list')
        ks=self.bpy.context.scene.keying_sets.new(name=name)
        for p in paths:
            if not isinstance(p,dict) or 'data_path' not in p:
                raise HarnessError('INVALID_ARGUMENT','each path must have data_path')
            target_id=p.get('id')
            target=None
            if target_id:
                target=self.bpy.data.objects.get(target_id)
            ks.paths.add(target if target else self.bpy.context.active_object or self.bpy.context.scene,
                        p['data_path'],index=p.get('index',-1))
        return {'changedObjects':[],'result':{'name':name,'pathCount':len(paths)}}

    def marker_set(self,arguments):
        """Set a timeline marker."""
        name=require_name(arguments.get('name'))
        frame=arguments.get('frame')
        if type(frame) is not int:
            raise HarnessError('INVALID_ARGUMENT','frame must be an integer')
        markers=self.bpy.context.scene.timeline_markers
        existing=markers.get(name)
        if existing:
            existing.frame=frame
            marker=existing
        else:
            marker=markers.new(name=name,frame=frame)
        camera_loc=arguments.get('camera')
        if camera_loc:
            camera_obj=self.objects.resolve(camera_loc,required_type={'CAMERA'})
            marker.camera=camera_obj
        return {'changedObjects':[],'result':{'name':name,'frame':frame,
                'camera':camera_loc.get('name') if camera_loc else None}}

    def motion_path_calculate(self,arguments):
        """Calculate motion path for an object over a frame range."""
        target=self.objects.resolve(arguments.get('target'))
        start=arguments.get('frameStart')
        end=arguments.get('frameEnd')
        if type(start) is not int or type(end) is not int or start>end:
            raise HarnessError('INVALID_ARGUMENT','frame range must be integers with frameStart <= frameEnd')
        points=[]
        previous_frame=self.bpy.context.scene.frame_current
        try:
            for frame in range(start,end+1):
                self.bpy.context.scene.frame_set(frame)
                self.bpy.context.view_layer.update()
                loc=list(target.matrix_world.translation) if hasattr(target.matrix_world,'translation') else [0,0,0]
                points.append({'frame':frame,'location':loc})
        finally:
            self.bpy.context.scene.frame_set(previous_frame)
        return {'changedObjects':[],'result':{'target':target.name,'frameStart':start,'frameEnd':end,
                'pointCount':len(points),'points':points}}

    def root_motion(self,arguments):
        """Extract root motion from a source bone to a target object."""
        armature=self.objects.resolve(arguments.get('armature'),required_type={'ARMATURE'})
        source_bone=require_name(arguments.get('sourceBone'))
        target=self.objects.resolve(arguments.get('targetObject'))
        start=arguments.get('frameStart')
        end=arguments.get('frameEnd')
        if type(start) is not int or type(end) is not int or start>end:
            raise HarnessError('INVALID_ARGUMENT','frame range must be integers with frameStart <= frameEnd')
        if armature.pose.bones.get(source_bone) is None:
            raise HarnessError('BONE_NOT_FOUND',f'pose bone not found: {source_bone}')
        previous_frame=self.bpy.context.scene.frame_current
        keyframe_count=0
        try:
            for frame in range(start,end+1):
                self.bpy.context.scene.frame_set(frame)
                self.bpy.context.view_layer.update()
                bone_matrix=armature.matrix_world@armature.pose.bones[source_bone].matrix
                loc=bone_matrix.translation
                target.location=loc
                target.keyframe_insert(data_path='location',frame=frame)
                keyframe_count+=1
        finally:
            self.bpy.context.scene.frame_set(previous_frame)
        return {'changedObjects':[target.name],'result':{'armature':armature.name,
                'sourceBone':source_bone,'target':target.name,'frameStart':start,'frameEnd':end,
                'keyframeCount':keyframe_count}}
