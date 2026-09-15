"""Native armature, skin binding, controls and explicit vertex weights."""
from ..errors import HarnessError
from ..identity import ObjectResolver
from ..operation_context import OperationContext
from .mesh import TOPOLOGY_VERSION_KEY
from .validation import finite_number,require_name,vector3


class RigCommands:
    def __init__(self,bpy_module,adapter=None):
        self.bpy=bpy_module; self.objects=ObjectResolver(bpy_module); self.context=OperationContext(bpy_module); self.adapter=adapter

    def create_armature(self,arguments):
        name=require_name(arguments.get('name')); specs=arguments.get('bones')
        if self.bpy.data.objects.get(name): raise HarnessError('NAME_COLLISION',f'object already exists: {name}')
        if not isinstance(specs,list) or not specs: raise HarnessError('INVALID_ARGUMENT','bones must be a non-empty list')
        parsed=[]; names=set()
        for spec in specs:
            if not isinstance(spec,dict): raise HarnessError('INVALID_ARGUMENT','bone must be an object')
            bone_name=require_name(spec.get('name'))
            if bone_name in names: raise HarnessError('INVALID_ARGUMENT','bone names must be unique')
            head,tail=vector3(spec.get('head'),'head'),vector3(spec.get('tail'),'tail')
            if sum((a-b)**2 for a,b in zip(head,tail))<=1e-12: raise HarnessError('INVALID_ARGUMENT','bone length must be positive')
            parent=spec.get('parent'); connected=spec.get('connected',False); deform=spec.get('deform',True)
            if parent is not None and parent not in names: raise HarnessError('INVALID_ARGUMENT','parent bone must appear before its child')
            if type(connected) is not bool or type(deform) is not bool: raise HarnessError('INVALID_ARGUMENT','bone flags must be boolean')
            names.add(bone_name); parsed.append((bone_name,head,tail,parent,connected,deform))
        data=self.bpy.data.armatures.new(name); obj=self.bpy.data.objects.new(name,data); self.bpy.context.scene.collection.objects.link(obj)
        try:
            with self.context.active_object(obj,mode='EDIT'):
                created={}
                for bone_name,head,tail,parent,connected,deform in parsed:
                    bone=data.edit_bones.new(bone_name); bone.head=head; bone.tail=tail; bone.use_deform=deform
                    if parent: bone.parent=created[parent]; bone.use_connect=connected
                    created[bone_name]=bone
        except Exception:
            self.bpy.data.objects.remove(obj,do_unlink=True); self.bpy.data.armatures.remove(data); raise
        return {'changedObjects':[name],'result':self.objects.receipt(obj)|{'bones':[item[0] for item in parsed]}}

    def create_control(self,arguments):
        name=require_name(arguments.get('name'))
        if self.bpy.data.objects.get(name): raise HarnessError('NAME_COLLISION',f'object already exists: {name}')
        location=vector3(arguments.get('location',[0,0,0]),'location'); size=finite_number(arguments.get('size',.12),'size',positive=True)
        shape=str(arguments.get('shape','CUBE')).upper()
        if shape not in {'CUBE','SPHERE','CIRCLE','ARROWS'}: raise HarnessError('INVALID_ARGUMENT','unsupported control shape')
        obj=self.bpy.data.objects.new(name,None); obj.empty_display_type=shape; obj.empty_display_size=size; obj.location=location
        self.bpy.context.scene.collection.objects.link(obj)
        return {'changedObjects':[name],'result':self.objects.receipt(obj)}

    def bind(self,arguments):
        mesh=self.objects.resolve(arguments.get('mesh'),required_type={'MESH'})
        armature=self.objects.resolve(arguments.get('armature'),required_type={'ARMATURE'})
        if any(mod.type=='ARMATURE' and mod.object is armature for mod in mesh.modifiers):
            raise HarnessError('INVALID_ARGUMENT','mesh is already bound to this armature')
        modifier=mesh.modifiers.new(name='Armature Deform',type='ARMATURE'); modifier.object=armature; mesh.parent=armature
        for bone in armature.data.bones:
            if bone.use_deform and mesh.vertex_groups.get(bone.name) is None: mesh.vertex_groups.new(name=bone.name)
        return {'changedObjects':[mesh.name],'result':{'mesh':self.objects.receipt(mesh),'armature':self.objects.receipt(armature),
                'modifier':modifier.name,'vertexGroups':len(mesh.vertex_groups)}}

    def assign_weights(self,arguments):
        mesh=self.objects.resolve(arguments.get('mesh'),required_type={'MESH'}); selection=arguments.get('selection')
        if not isinstance(selection,dict) or selection.get('objectId')!=self.objects.ensure_id(mesh) or selection.get('topologyVersion')!=int(mesh.data.get(TOPOLOGY_VERSION_KEY,0)):
            raise HarnessError('STALE_TOPOLOGY_SELECTION','weight selection is missing, stale or belongs to another mesh')
        indices=selection.get('vertices',[]); bone=require_name(arguments.get('bone')); group=mesh.vertex_groups.get(bone)
        if group is None: raise HarnessError('BONE_NOT_FOUND',f'vertex group not found: {bone}')
        if not indices: raise HarnessError('INVALID_ARGUMENT','weight assignment requires vertices')
        weight=finite_number(arguments.get('weight',1),'weight',minimum=0)
        if weight>1: raise HarnessError('INVALID_ARGUMENT','weight must be at most 1')
        mode=str(arguments.get('mode','REPLACE')).upper()
        if mode not in {'REPLACE','ADD','SUBTRACT'}: raise HarnessError('INVALID_ARGUMENT','unsupported weight mode')
        group.add(indices,weight,mode)
        return {'changedObjects':[mesh.name],'result':{'mesh':self.objects.receipt(mesh),'bone':bone,'vertices':len(indices),'weight':weight}}

    def inspect(self,arguments):
        arm=self.objects.resolve(arguments,required_type={'ARMATURE'})
        bones=[{'name':bone.name,'parent':bone.parent.name if bone.parent else None,'length':float(bone.length),
                'deform':bool(bone.use_deform)} for bone in arm.data.bones]
        bound=[obj.name for obj in self.bpy.data.objects if obj.type=='MESH' and any(m.type=='ARMATURE' and m.object is arm for m in obj.modifiers)]
        return {'changedObjects':[],'result':self.objects.receipt(arm)|{'bones':bones,'boundMeshes':sorted(bound)}}

    def rigify_status(self,_arguments):
        if self.adapter is not None:
            return {'changedObjects':[],'result':self.adapter.enable_rigify(self.bpy)}
        try:
            import addon_utils
            bundled=any(module.__name__=='rigify' for module in addon_utils.modules())
        except (ImportError,AttributeError):bundled=False
        addons=self.bpy.context.preferences.addons
        modules=[item if isinstance(item,str) else str(getattr(item,'module','')) for item in addons]
        enabled=addons.get('rigify') is not None or any(module=='rigify' or module.endswith('.rigify') for module in modules)
        operator=hasattr(self.bpy.ops.pose,'rigify_generate')
        return {'changedObjects':[],'result':{'installed':bundled or enabled,'bundledAvailable':bundled,'enabled':enabled,
          'operatorAvailable':operator and enabled,'blenderVersion':self.bpy.app.version_string}}

    def rigify_install(self,arguments):
        allow_download=arguments.get('allowDownload',False);save_preferences=arguments.get('savePreferences',True)
        if type(allow_download) is not bool or type(save_preferences) is not bool:
            raise HarnessError('INVALID_ARGUMENT','allowDownload and savePreferences must be boolean')
        before=self.rigify_status({})['result']
        if before['enabled']:
            return {'changedObjects':[],'result':before|{'mode':'already-enabled','preferencesSaved':False}}
        if before['bundledAvailable']:
            result=self.bpy.ops.preferences.addon_enable(module='rigify')
            if result!={'FINISHED'}:raise HarnessError('EXTENSION_INSTALL_FAILED','bundled Rigify could not be enabled')
            mode='bundled-enable'
        else:
            if not allow_download:
                raise HarnessError('EXTENSION_INSTALL_AUTHORIZATION_REQUIRED','Rigify is not bundled; explicit allowDownload is required')
            if not self.bpy.context.preferences.system.use_online_access:
                raise HarnessError('ONLINE_ACCESS_DISABLED','enable Blender online access before downloading Rigify')
            repositories=list(self.bpy.context.preferences.extensions.repos)
            repo_index=next((index for index,repo in enumerate(repositories)
                             if repo.enabled and str(repo.remote_url).startswith('https://extensions.blender.org/')),None)
            if repo_index is None:raise HarnessError('CAPABILITY_UNAVAILABLE','official Blender Extensions repository is unavailable')
            synced=self.bpy.ops.extensions.repo_sync_all()
            if synced!={'FINISHED'}:raise HarnessError('EXTENSION_INSTALL_FAILED','official repository sync failed')
            installed=self.bpy.ops.extensions.package_install(repo_index=repo_index,pkg_id='rigify',enable_on_install=True)
            if installed!={'FINISHED'}:raise HarnessError('EXTENSION_INSTALL_FAILED','official Rigify installation failed')
            mode='official-extension-download'
        saved=False
        if save_preferences:
            saved=self.bpy.ops.wm.save_userpref()=={'FINISHED'}
            if not saved:raise HarnessError('EXTENSION_INSTALL_FAILED','Rigify enabled but preferences could not be saved')
        after=self.rigify_status({})['result']
        if not after['operatorAvailable']:raise HarnessError('EXTENSION_INSTALL_FAILED','Rigify enabled but its generation operator is unavailable')
        return {'changedObjects':[],'result':after|{'mode':mode,'preferencesSaved':saved,'downloadAttempted':mode=='official-extension-download'}}

    def rigify_generate(self,arguments):
        status=self.rigify_status({})['result']
        if not status['operatorAvailable']:raise HarnessError('CAPABILITY_UNAVAILABLE','Rigify is not enabled; run authorized rig.rigify_install first')
        metarig=self.objects.resolve(arguments,required_type={'ARMATURE'});before=set(self.bpy.data.objects)
        try:
            with self.context.active_object(metarig):result=self.bpy.ops.pose.rigify_generate()
            if result!={'FINISHED'}:raise RuntimeError('not finished')
        except Exception as exc:raise HarnessError('OPERATION_FAILED','Rigify generation failed for this metarig') from exc
        created=[obj for obj in self.bpy.data.objects if obj not in before]
        return {'changedObjects':[obj.name for obj in created],'result':{'metarig':self.objects.receipt(metarig),
          'created':[self.objects.receipt(obj) for obj in created]}}
