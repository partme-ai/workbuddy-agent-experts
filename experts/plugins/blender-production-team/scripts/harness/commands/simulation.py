"""Typed rigid-body, cloth, soft-body, collision, fluid and cache controls."""
from pathlib import Path
from ..errors import HarnessError
from ..identity import ObjectResolver
from ..operation_context import OperationContext
from .validation import finite_number,require_name


class SimulationCommands:
    def __init__(self,bpy_module,output_root=None):
        self.bpy=bpy_module;self.objects=ObjectResolver(bpy_module);self.context=OperationContext(bpy_module);self.output=Path(output_root).resolve() if output_root else None
    def _cache_path(self,obj):
        if self.output is None:return None
        path=self.output/'simulation-cache'/self.objects.ensure_id(obj);path.mkdir(parents=True,exist_ok=True);return path
    def rigid_body(self,args):
        obj=self.objects.resolve(args,required_type={'MESH'});kind=str(args.get('bodyType','ACTIVE')).upper();shape=str(args.get('collisionShape','CONVEX_HULL')).upper()
        if kind not in {'ACTIVE','PASSIVE'} or shape not in {'BOX','SPHERE','CAPSULE','CYLINDER','CONE','CONVEX_HULL','MESH'}:raise HarnessError('INVALID_ARGUMENT','rigid body type/shape is invalid')
        mass=finite_number(args.get('mass',1),'mass',positive=True)
        with self.context.active_object(obj):
            if obj.rigid_body is None:self.bpy.ops.rigidbody.object_add()
            obj.rigid_body.type=kind;obj.rigid_body.collision_shape=shape;obj.rigid_body.mass=mass
        return {'changedObjects':[obj.name],'result':self.objects.receipt(obj)|{'bodyType':kind,'collisionShape':shape,'mass':mass}}
    def collision(self,args):
        obj=self.objects.resolve(args,required_type={'MESH'});thickness=finite_number(args.get('thickness',.015),'thickness',minimum=0)
        with self.context.active_object(obj):
            if not any(m.type=='COLLISION' for m in obj.modifiers):self.bpy.ops.object.modifier_add(type='COLLISION')
        if getattr(obj,'collision',None):obj.collision.thickness_outer=thickness
        return {'changedObjects':[obj.name],'result':self.objects.receipt(obj)|{'thickness':thickness}}
    def cloth(self,args):
        obj=self.objects.resolve(args,required_type={'MESH'});name=require_name(args.get('modifierName','Cloth'))
        quality=args.get('quality',5);mass=finite_number(args.get('mass',.3),'mass',positive=True)
        if type(quality) is not int or not 1<=quality<=80:raise HarnessError('INVALID_ARGUMENT','quality must be 1..80')
        if obj.modifiers.get(name):raise HarnessError('NAME_COLLISION','modifier already exists')
        modifier=obj.modifiers.new(name=name,type='CLOTH');modifier.settings.quality=quality;modifier.settings.mass=mass
        self._configure_cache(obj,modifier.point_cache,args)
        return {'changedObjects':[obj.name],'result':self.objects.receipt(obj)|{'modifierName':name,'cache':self._cache_receipt(modifier.point_cache)}}
    def soft_body(self,args):
        obj=self.objects.resolve(args,required_type={'MESH'});name=require_name(args.get('modifierName','Soft Body'))
        if obj.modifiers.get(name):raise HarnessError('NAME_COLLISION','modifier already exists')
        before=set(obj.modifiers)
        with self.context.active_object(obj):self.bpy.ops.object.modifier_add(type='SOFT_BODY')
        modifier=next(m for m in obj.modifiers if m not in before and m.type=='SOFT_BODY')
        modifier.name=name;self._configure_cache(obj,modifier.point_cache,args)
        return {'changedObjects':[obj.name],'result':self.objects.receipt(obj)|{'modifierName':name,'cache':self._cache_receipt(modifier.point_cache)}}
    def _configure_cache(self,obj,cache,args):
        start,end=args.get('frameStart',1),args.get('frameEnd',50)
        if type(start) is not int or type(end) is not int or start>end:raise HarnessError('INVALID_ARGUMENT','cache frame range is invalid')
        cache.frame_start=start;cache.frame_end=end
        path=self._cache_path(obj)
        if path:cache.filepath=str(path)
    @staticmethod
    def _cache_receipt(cache):return {'frameStart':cache.frame_start,'frameEnd':cache.frame_end,'filepath':cache.filepath,'isBaked':bool(cache.is_baked)}
    def quick_smoke(self,args):
        flows=args.get('flows')
        if not isinstance(flows,list) or not flows:raise HarnessError('INVALID_ARGUMENT','flows must contain object locators')
        resolution=args.get('resolution',32);start=args.get('frameStart',1);end=args.get('frameEnd',50)
        if type(resolution) is not int or not 16<=resolution<=256:raise HarnessError('INVALID_ARGUMENT','resolution must be 16..256')
        if type(start) is not int or type(end) is not int or start>end:raise HarnessError('INVALID_ARGUMENT','frame range is invalid')
        objects=[self.objects.resolve(locator,required_type={'MESH'}) for locator in flows];before=set(self.bpy.data.objects)
        with self.context.active_objects(objects,active=objects[0]):
            properties={item.identifier for item in self.bpy.ops.object.quick_smoke.get_rna_type().properties}
            options={'style':'SMOKE'}
            if 'show_flows' in properties:options['show_flows']=True
            elif 'render' in properties:options['render']=False
            result=self.bpy.ops.object.quick_smoke(**options)
            if result!={'FINISHED'}:raise HarnessError('OPERATION_FAILED','quick smoke did not finish')
        created=[obj for obj in self.bpy.data.objects if obj not in before];domain=next((obj for obj in created if any(m.type=='FLUID' and m.fluid_type=='DOMAIN' for m in obj.modifiers)),None)
        if domain is None:raise HarnessError('OPERATION_FAILED','smoke domain was not created')
        modifier=next(m for m in domain.modifiers if m.type=='FLUID');settings=modifier.domain_settings
        settings.resolution_max=resolution
        settings.cache_frame_start=start;settings.cache_frame_end=end
        path=self._cache_path(domain)
        if path:settings.cache_directory=str(path)
        return {'changedObjects':[obj.name for obj in [*objects,domain]],'result':{'domain':self.objects.receipt(domain),
          'flows':[self.objects.receipt(obj) for obj in objects],'resolution':resolution,'cacheDirectory':settings.cache_directory}}
    def _caches(self,obj):
        caches=[]
        for modifier in obj.modifiers:
            cache=getattr(modifier,'point_cache',None)
            if cache:caches.append((modifier.name,cache))
        return caches
    def cache_status(self,args):
        obj=self.objects.resolve(args);items=[{'modifierName':name,**self._cache_receipt(cache)} for name,cache in self._caches(obj)]
        for modifier in obj.modifiers:
            settings=getattr(modifier,'domain_settings',None)
            if settings:items.append({'modifierName':modifier.name,'frameStart':settings.cache_frame_start,'frameEnd':settings.cache_frame_end,
              'filepath':settings.cache_directory,'isBaked':bool(getattr(settings,'has_cache_baked_any',False) or getattr(settings,'cache_status',None)=='BAKED')})
        return {'changedObjects':[],'result':self.objects.receipt(obj)|{'caches':items}}
    def free_cache(self,args):
        obj=self.objects.resolve(args);freed=[]
        for name,cache in self._caches(obj):
            if cache.is_baked:
                try:
                    with self.bpy.context.temp_override(point_cache=cache):self.bpy.ops.ptcache.free_bake()
                    freed.append(name)
                except Exception as exc:raise HarnessError('OPERATION_FAILED',f'could not free cache: {name}') from exc
        for modifier in obj.modifiers:
            settings=getattr(modifier,'domain_settings',None)
            if settings and (getattr(settings,'has_cache_baked_any',False) or getattr(settings,'cache_status',None)=='BAKED'):
                hidden=(obj.hide_viewport,obj.hide_render,obj.hide_get())
                try:
                    obj.hide_viewport=False;obj.hide_render=False;obj.hide_set(False)
                    with self.context.active_object(obj):self.bpy.ops.fluid.free_all()
                    freed.append(modifier.name)
                except Exception as exc:raise HarnessError('OPERATION_FAILED',f'could not free fluid cache: {modifier.name}') from exc
                finally:
                    obj.hide_viewport,obj.hide_render=hidden[0],hidden[1];obj.hide_set(hidden[2])
        return {'changedObjects':[obj.name] if freed else [],'result':{'object':self.objects.receipt(obj),'freed':freed}}
