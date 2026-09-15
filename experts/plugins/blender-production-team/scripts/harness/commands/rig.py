"""Native armature, skin binding, controls and explicit vertex weights."""
import math
from ..errors import HarnessError
from ..identity import ObjectResolver
from ..operation_context import OperationContext
from .mesh import TOPOLOGY_VERSION_KEY
from .validation import finite_number,require_name,vector3


# ---------------------------------------------------------------------------
# Rotation-mode validation helpers
# ---------------------------------------------------------------------------

_EULER_MODES = frozenset({'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'})


def _validate_pose_channel(data_path, rotation_mode):
    """Raise HarnessError if the rotation channel is incompatible with the bone's mode.

    A silently inert pose is the exact failure mode that produced the original
    collapse-metric bug; this guard makes it impossible to pass a measurement
    that the bone will ignore.
    """
    if data_path == 'rotation_euler' and rotation_mode not in _EULER_MODES:
        raise HarnessError('ROTATION_MODE_MISMATCH',
            f'rotation_euler requires an Euler rotation mode but bone has '
            f'rotation_mode={rotation_mode}.  Use rotation_quaternion or '
            f'set rotation_mode to an Euler mode (e.g. XYZ) first.')
    if data_path == 'rotation_quaternion' and rotation_mode != 'QUATERNION':
        raise HarnessError('ROTATION_MODE_MISMATCH',
            f'rotation_quaternion requires QUATERNION rotation mode but bone has '
            f'rotation_mode={rotation_mode}.  Use rotation_euler or '
            f'set rotation_mode to QUATERNION first.')
    if data_path == 'rotation_axis_angle' and rotation_mode != 'AXIS_ANGLE':
        raise HarnessError('ROTATION_MODE_MISMATCH',
            f'rotation_axis_angle requires AXIS_ANGLE rotation mode but bone has '
            f'rotation_mode={rotation_mode}.  Use rotation_euler or '
            f'set rotation_mode to AXIS_ANGLE first.')


def _pose_value(value, data_path):
    """Validate and convert a pose value -- 3 or 4 components depending on channel."""
    if data_path in ('rotation_quaternion', 'rotation_axis_angle'):
        if not isinstance(value, (list, tuple)) or len(value) != 4:
            raise HarnessError('INVALID_ARGUMENT',
                               f'{data_path} value must contain exactly four numbers')
        if any(isinstance(item, bool) or not isinstance(item, (int, float))
               or not math.isfinite(item) for item in value):
            raise HarnessError('INVALID_ARGUMENT',
                               f'{data_path} value must contain finite numbers')
        return [float(item) for item in value]
    return vector3(value, 'pose value')


# ---------------------------------------------------------------------------
# Slotted-action fcurve helpers (Blender 5.2+)
# ---------------------------------------------------------------------------

def _get_action_fcurves(action):
    """Yield fcurves from *action*, supporting both old and slotted (5.2+) formats.

    Blender 5.2 slotted actions store fcurves at
    ``action.layers[].strips[].channelbags[].fcurves``.  Older versions
    store them directly at ``action.fcurves``.  This helper tries the
    slotted path first and falls back to the legacy path.
    """
    # Slotted format (Blender 5.2+)
    try:
        fcurves = []
        for layer in getattr(action, 'layers', ()):
            for strip in getattr(layer, 'strips', ()):
                for channelbag in getattr(strip, 'channelbags', ()):
                    fcurves.extend(getattr(channelbag, 'fcurves', ()))
        if fcurves:
            return fcurves
    except (AttributeError, TypeError):
        pass
    # Legacy format
    return list(getattr(action, 'fcurves', ()))


def _cleanup_temp_keyframes(action, bone_path, temp_frame):
    """Remove keyframes at *temp_frame* on *bone_path*, handling slotted actions."""
    if action is None:
        return
    seen_ptrs = set()
    for fc in _get_action_fcurves(action):
        ptr = fc.as_pointer()
        if ptr in seen_ptrs:
            continue
        seen_ptrs.add(ptr)
        if fc.data_path == bone_path:
            for kp in list(fc.keyframe_points):
                if kp.co.x == temp_frame:
                    try:
                        fc.keyframe_points.remove(kp)
                    except RuntimeError:
                        # Blender raises "Keyframe not in F-Curve" when a stale
                        # reference is iterated after prior removal.
                        pass


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

    def auto_weights(self,arguments):
        """Auto-assign bone weights with normalisation and influence capping.

        Computes distance-based weights for each vertex to every deform bone,
        normalises so weights sum to 1 per vertex, then keeps only the
        top *maxInfluences* bones per vertex (default 4).
        """
        mesh=self.objects.resolve(arguments.get('mesh'),required_type={'MESH'})
        armature=self.objects.resolve(arguments.get('armature'),required_type={'ARMATURE'})
        max_influences=arguments.get('maxInfluences',4)
        if type(max_influences) is not int or max_influences<1:
            raise HarnessError('INVALID_ARGUMENT','maxInfluences must be a positive integer')
        deform_bones=[bone for bone in armature.data.bones if bone.use_deform]
        if not deform_bones:
            raise HarnessError('INVALID_ARGUMENT','armature has no deform bones')
        for bone in deform_bones:
            if mesh.vertex_groups.get(bone.name) is None:
                mesh.vertex_groups.new(name=bone.name)
        # Compute bone segment midpoints and half-lengths for distance weighting.
        bone_info=[]
        for bone in deform_bones:
            h=bone.head_local; t=bone.tail_local
            mid=[(a+b)/2 for a,b in zip(h,t)]
            half_len=math.sqrt(sum((a-b)**2 for a,b in zip(h,t)))/2
            bone_info.append((bone.name,mid,max(half_len,1e-6)))
        for vertex in mesh.data.vertices:
            co=vertex.co
            raw=[]
            for name,mid,half_len in bone_info:
                dist=math.sqrt(sum((a-b)**2 for a,b in zip(co,mid)))
                # Weight = 1/(distance+epsilon)^2, capped by bone half-length influence.
                w=1.0/(max(dist-half_len,0)+0.01)**2
                raw.append((name,w))
            # Sort descending and keep top maxInfluences.
            raw.sort(key=lambda x:-x[1])
            kept=raw[:max_influences]
            total=sum(w for _,w in kept)
            if total<1e-12:
                # Fallback: assign uniform to first bone.
                kept=[(raw[0][0],1.0)]; total=1.0
            # Normalise.
            for name,w in kept:
                group=mesh.vertex_groups[name]
                group.add([vertex.index],w/total,'REPLACE')
        return {'changedObjects':[mesh.name],'result':{'mesh':self.objects.receipt(mesh),
                'armature':self.objects.receipt(armature),'maxInfluences':max_influences,
                'deformBoneCount':len(deform_bones),'vertexCount':len(mesh.data.vertices)}}

    def validate_deformation(self,arguments):
        """Check that extreme poses do not collapse mesh geometry beyond threshold.

        The *collapse* metric measures **loss of local scale**, not displacement.
        It compares edge lengths in the posed mesh (evaluated via depsgraph)
        to edge lengths in the neutral (unposed) evaluated mesh.  Rigid
        translation or rotation preserves edge lengths, so only genuine
        deformation such as shrinkage or stretching registers.

        collapse = max over edges of max(0, 1 - posedLen / restLen)

        **Known limitation**: the ``max over edges`` formulation is dominated
        by the shortest edge above the floor (1e-4 scene units).  A mesh with
        near-degenerate edges (e.g. 0.1 mm) will register large shrinkage from
        sub-micron deformation on that edge alone.  The ``p99Shrinkage`` field
        gives the 99th-percentile shrinkage, which is more robust for
        production gating when short edges are present.  Use ``collapse``
        (the max) for regression detection and ``p99Shrinkage`` for acceptance.

        Each pose dict must contain *bone*, *dataPath* and *value*.  If
        *dataPath* is a rotation channel incompatible with the bone's
        *rotation_mode*, a ``ROTATION_MODE_MISMATCH`` error is raised.
        """
        mesh=self.objects.resolve(arguments.get('mesh'),required_type={'MESH'})
        armature=self.objects.resolve(arguments.get('armature'),required_type={'ARMATURE'})
        poses=arguments.get('poses')
        thresholds=arguments.get('thresholds')
        if not isinstance(thresholds,dict) or 'collapse' not in thresholds:
            raise HarnessError('INVALID_ARGUMENT','thresholds must include collapse')
        collapse_threshold=finite_number(thresholds['collapse'],'collapse',positive=True)
        if not isinstance(poses,list) or not poses:
            raise HarnessError('INVALID_ARGUMENT','poses must be a non-empty list')

        scene=self.bpy.context.scene
        original_frame=scene.frame_current

        # ---- neutral (unposed) evaluated mesh ----
        depsgraph=self.bpy.context.evaluated_depsgraph_get()
        eval_neutral=mesh.evaluated_get(depsgraph)
        neutral_mesh=eval_neutral.to_mesh()
        neutral_verts=[(v.co[0],v.co[1],v.co[2]) for v in neutral_mesh.vertices]
        neutral_edges=[(e.vertices[0],e.vertices[1]) for e in neutral_mesh.edges]
        eval_neutral.to_mesh_clear()

        results=[]
        for pose_index,pose in enumerate(poses):
            bone_name=pose.get('bone'); data_path=pose.get('dataPath'); value=pose.get('value')
            if not bone_name or not data_path or value is None:
                raise HarnessError('INVALID_ARGUMENT','each pose must have bone, dataPath and value')
            pose_bone=armature.pose.bones.get(bone_name)
            if pose_bone is None:
                raise HarnessError('BONE_NOT_FOUND',f'pose bone not found: {bone_name}')

            # Guard: rotation channel must match the bone's rotation_mode.
            _validate_pose_channel(data_path,pose_bone.rotation_mode)

            parsed_value=_pose_value(value,data_path)
            temp_frame=9000+pose_index
            # Snapshot the current value before writing.  Blender's
            # mathutils properties return a live reference, not a copy;
            # getattr(bone, 'scale') reads through to whatever the bone
            # currently holds.  We must capture a plain copy so the
            # restore below actually resets the bone to its pre-pose state.
            old_raw=getattr(pose_bone,data_path,None)
            if old_raw is not None:
                old_value=list(old_raw)
            else:
                old_value=None
            try:
                setattr(pose_bone,data_path,parsed_value)
                pose_bone.keyframe_insert(data_path=data_path,frame=temp_frame)
                scene.frame_set(temp_frame)
                self.bpy.context.view_layer.update()

                # ---- posed evaluated mesh ----
                depsgraph=self.bpy.context.evaluated_depsgraph_get()
                eval_posed=mesh.evaluated_get(depsgraph)
                posed_mesh=eval_posed.to_mesh()

                # Topology must not change under armature deformation.
                if len(neutral_verts)!=len(posed_mesh.vertices):
                    raise HarnessError('TOPOLOGY_MISMATCH',
                        f'neutral has {len(neutral_verts)} vertices but posed has '
                        f'{len(posed_mesh.vertices)} -- armature changed topology')

                # ---- edge-shrinkage metric ----
                # Edge-length floor: edges shorter than this are excluded.
                # 1e-4 (0.1 mm) avoids degenerate short edges dominating the
                # max collapse; the floor is deliberately above the old 1e-12
                # guard to make the metric meaningful on production meshes.
                edge_floor=1e-4
                max_collapse=0.0
                max_stretch=0.0
                edges_compared=0
                shrinkages=[]
                for i,j in neutral_edges:
                    ni=neutral_verts[i]; nj=neutral_verts[j]
                    pi=posed_mesh.vertices[i].co; pj=posed_mesh.vertices[j].co
                    rest_len=math.sqrt(sum((a-b)**2 for a,b in zip(ni,nj)))
                    posed_len=math.sqrt(sum((a-b)**2 for a,b in zip(pi,pj)))
                    if rest_len>edge_floor:
                        edges_compared+=1
                        ratio=posed_len/rest_len
                        shrinkage=max(0.0,1.0-ratio)
                        stretch=max(0.0,ratio-1.0)
                        shrinkages.append(shrinkage)
                        if shrinkage>max_collapse: max_collapse=shrinkage
                        if stretch>max_stretch: max_stretch=stretch

                eval_posed.to_mesh_clear()

                # p99 shrinkage: more robust than max on meshes with
                # near-degenerate edges.
                if shrinkages:
                    shrinkages.sort()
                    p99_index=max(0,int(len(shrinkages)*0.99)-1)
                    p99_shrinkage=shrinkages[p99_index]
                else:
                    p99_shrinkage=0.0

                passed=max_collapse<=collapse_threshold
                results.append({'bone':bone_name,'dataPath':data_path,
                                'collapse':max_collapse,'maxStretch':max_stretch,
                                'p99Shrinkage':p99_shrinkage,
                                'edgesCompared':edges_compared,
                                'verticesCompared':len(neutral_verts),
                                'passed':passed})
            finally:
                # ---- clean up temporary keyframe (slotted-action safe) ----
                arm_action=getattr(getattr(armature,'animation_data',None),'action',None)
                bone_path=f'pose.bones["{bone_name}"].{data_path}'
                _cleanup_temp_keyframes(arm_action,bone_path,temp_frame)
                if old_value is not None:
                    setattr(pose_bone,data_path,old_value)

        # Restore original frame.
        scene.frame_set(original_frame)
        self.bpy.context.view_layer.update()
        all_passed=all(r['passed'] for r in results)
        return {'changedObjects':[],'result':{'results':results,'allPassed':all_passed,
                'collapseThreshold':collapse_threshold}}
