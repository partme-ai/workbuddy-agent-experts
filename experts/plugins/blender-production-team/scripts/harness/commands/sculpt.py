"""Controlled sculpt-adjacent surface edits, masks, Multires and remesh."""
from ..errors import HarnessError
from ..identity import ObjectResolver
from ..operation_context import OperationContext
from .mesh import TOPOLOGY_VERSION_KEY
from .validation import finite_number,require_name,vector3


class SculptCommands:
    def __init__(self,bpy_module):self.bpy=bpy_module;self.objects=ObjectResolver(bpy_module);self.context=OperationContext(bpy_module)
    def _selection(self,args):
        selection=args.get('selection')
        if not isinstance(selection,dict):raise HarnessError('INVALID_ARGUMENT','selection is required')
        obj=self.objects.resolve({'objectId':selection.get('objectId')},required_type={'MESH'})
        if selection.get('topologyVersion')!=int(obj.data.get(TOPOLOGY_VERSION_KEY,0)):raise HarnessError('STALE_TOPOLOGY_SELECTION','selection is stale')
        indices=selection.get('vertices',[])
        if not isinstance(indices,list) or any(type(i) is not int or not 0<=i<len(obj.data.vertices) for i in indices):raise HarnessError('INVALID_ARGUMENT','vertex selection is invalid')
        return obj,indices
    def set_mask(self,args):
        obj,indices=self._selection(args);value=finite_number(args.get('value'),'value',minimum=0)
        if value>1:raise HarnessError('INVALID_ARGUMENT','mask value must be at most 1')
        attribute=obj.data.attributes.get('.sculpt_mask') or obj.data.attributes.new('.sculpt_mask','FLOAT','POINT')
        for index in indices:attribute.data[index].value=value
        obj.data.update();return {'changedObjects':[obj.name],'result':self.objects.receipt(obj)|{'vertices':len(indices),'value':value}}
    def displace(self,args):
        from mathutils import Vector
        obj,indices=self._selection(args);strength=finite_number(args.get('strength'),'strength');direction=args.get('direction')
        direction=Vector(vector3(direction,'direction')).normalized() if direction is not None else None
        mask=obj.data.attributes.get('.sculpt_mask')
        for index in indices:
            vertex=obj.data.vertices[index];factor=1-(mask.data[index].value if mask else 0)
            vertex.co+=(direction or vertex.normal.normalized())*strength*factor
        obj.data.update();return {'changedObjects':[obj.name],'result':self.objects.receipt(obj)|{'vertices':len(indices),'strength':strength}}
    def voxel_remesh(self,args):
        obj=self.objects.resolve(args,required_type={'MESH'});size=finite_number(args.get('voxelSize'),'voxelSize',positive=True)
        obj.data.remesh_voxel_size=size
        try:
            with self.context.active_object(obj):result=self.bpy.ops.object.voxel_remesh()
            if result!={'FINISHED'}:raise RuntimeError('not finished')
        except Exception as exc:raise HarnessError('OPERATION_FAILED','voxel remesh failed') from exc
        obj.data[TOPOLOGY_VERSION_KEY]=int(obj.data.get(TOPOLOGY_VERSION_KEY,0))+1
        return {'changedObjects':[obj.name],'result':self.objects.receipt(obj)|{'topologyVersion':obj.data[TOPOLOGY_VERSION_KEY],'voxelSize':size}}
    def multires(self,args):
        obj=self.objects.resolve(args,required_type={'MESH'});levels=args.get('levels',1);name=require_name(args.get('modifierName','Multires'))
        if type(levels) is not int or not 1<=levels<=6:raise HarnessError('INVALID_ARGUMENT','levels must be 1..6')
        if obj.modifiers.get(name):raise HarnessError('NAME_COLLISION','modifier already exists')
        modifier=obj.modifiers.new(name=name,type='MULTIRES')
        try:
            with self.context.active_object(obj):
                for _ in range(levels):self.bpy.ops.object.multires_subdivide(modifier=name,mode='CATMULL_CLARK')
        except Exception as exc:
            obj.modifiers.remove(modifier);raise HarnessError('OPERATION_FAILED','Multires subdivision failed') from exc
        return {'changedObjects':[obj.name],'result':self.objects.receipt(obj)|{'modifierName':name,'levels':modifier.total_levels}}
    def cleanup(self,args):
        obj=self.objects.resolve(args,required_type={'MESH'});ratio=finite_number(args.get('ratio',1),'ratio',positive=True)
        if ratio>1:raise HarnessError('INVALID_ARGUMENT','ratio must be at most 1')
        decimate=obj.modifiers.new(name=require_name(args.get('modifierName','Cleanup Decimate')),type='DECIMATE');decimate.ratio=ratio
        target=args.get('target');shrinkwrap=None
        if target:
            target_obj=self.objects.resolve(target,required_type={'MESH'});shrinkwrap=obj.modifiers.new(name='Cleanup Shrinkwrap',type='SHRINKWRAP');shrinkwrap.target=target_obj
        return {'changedObjects':[obj.name],'result':self.objects.receipt(obj)|{'modifiers':[decimate.name,*([shrinkwrap.name] if shrinkwrap else [])],
          'limitations':['This is modifier-based cleanup, not production character retopology']}}

    def brush_stroke(self,args):
        obj=self.objects.resolve(args,required_type={'MESH'});points=args.get('points')
        if not isinstance(points,list) or not 1<=len(points)<=4096:raise HarnessError('INVALID_ARGUMENT','brush requires 1..4096 points')
        stroke=[]
        for index,point in enumerate(points):
            if not isinstance(point,dict):raise HarnessError('INVALID_ARGUMENT','brush point must be an object')
            location=vector3(point.get('location'),'location');mouse=point.get('mouse');pressure=finite_number(point.get('pressure',1),'pressure',minimum=0);size=finite_number(point.get('size',50),'size',positive=True)
            if not isinstance(mouse,(list,tuple)) or len(mouse)!=2:raise HarnessError('INVALID_ARGUMENT','mouse requires two coordinates')
            if pressure>1 or size>2048:raise HarnessError('INVALID_ARGUMENT','brush pressure/size exceeds safe bounds')
            mouse=[finite_number(v,'mouse') for v in mouse]
            stroke.append({'name':'','location':location,'mouse':mouse,'mouse_event':mouse,'pressure':pressure,'size':size,
                           'x_tilt':0,'y_tilt':0,'time':index*.02,'is_start':index==0})
        manager=getattr(self.bpy.context,'window_manager',None);found=None
        for window in getattr(manager,'windows',()):
            for area in window.screen.areas:
                if area.type=='VIEW_3D':
                    region=next((r for r in area.regions if r.type=='WINDOW'),None)
                    if region:found=(window,area,region);break
            if found:break
        if not found:raise HarnessError('FRONTEND_UNAVAILABLE','sculpt brush requires a foreground VIEW_3D area')
        window,area,region=found
        try:
            with self.context.active_object(obj,mode='SCULPT'):
                with self.bpy.context.temp_override(window=window,area=area,region=region):
                    result=self.bpy.ops.sculpt.brush_stroke(stroke=stroke,mode='NORMAL',override_location=True)
            if result!={'FINISHED'}:raise RuntimeError('stroke did not finish')
        except HarnessError:raise
        except Exception as exc:raise HarnessError('OPERATION_FAILED','sculpt brush stroke failed') from exc
        return {'changedObjects':[obj.name],'result':self.objects.receipt(obj)|{'points':len(stroke),'brush':'active Draw-compatible sculpt brush'}}
