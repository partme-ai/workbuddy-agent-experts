"""Composition root shared by managed and Connector modes."""

from __future__ import annotations

from .commands.animation import AnimationCommands
from .commands.camera import CameraCommands
from .commands.light import LightCommands
from .commands.material import MaterialCommands
from .commands.object import ObjectCommands
from .commands.official_uploader import OfficialUploaderCommands
from .commands.scene import SceneCommands
from .commands.view import ViewCommands
from .commands.collection import OrganizationCommands
from .commands.mesh import MeshCommands
from .commands.modifier import ModifierCommands
from .commands.curve import CurveCommands
from .commands.asset import AssetCommands
from .commands.recipe import RecipeCommands
from .commands.uv import UVCommands
from .commands.rig import RigCommands
from .commands.constraint import ConstraintCommands
from .commands.advanced_animation import AdvancedAnimationCommands
from .commands.quality import QualityCommands
from .jobs import JobManager
from .commands.geometry_nodes import GeometryNodeCommands
from .commands.sculpt import SculptCommands
from .commands.hair import HairCommands
from .commands.simulation import SimulationCommands
from .commands.render import RenderCommands
from .commands.compositor import CompositorCommands
from .extended_export import ExtendedExporter
from .commands.grease_pencil import GreasePencilCommands
from .commands.sequence import SequenceCommands
from .commands.tracking import TrackingCommands
from .commands.retopo import RetopoCommands
from .commands.validation import closed_arguments
from pathlib import Path
import re

from .advanced_python import AdvancedPythonExecutor
from .exporter import Exporter
from .preview import PreviewEngine
from .path_policy import PathPolicy
from .errors import HarnessError
from .production_profile import ProductionProfile, RuntimeIdentity
from .compat.selector import select_adapter
from .registry import CommandRegistry
from .runtime_catalog import RuntimeCommandRegistry
from .session import HarnessSession
from .execution_policy import ExecutionMode, ExecutionPolicy


def build_registry(bpy_module, *, runtime_mode: str = "managed", approved_output_root: Path | None = None, approved_asset_roots=(), revision_provider=lambda: 0) -> CommandRegistry:
    scene = SceneCommands(bpy_module)
    objects = ObjectCommands(bpy_module)
    materials = MaterialCommands(bpy_module, asset_policy=PathPolicy(approved_asset_roots) if approved_asset_roots else None,
                                 output_root=approved_output_root)
    cameras = CameraCommands(bpy_module)
    lights = LightCommands(bpy_module)
    animation = AnimationCommands(bpy_module)
    view = ViewCommands(bpy_module)
    if runtime_mode not in {"managed", "connector"}:
        raise ValueError("runtime_mode must be managed or connector")
    # Select version adapter once; pass to commands that need it.
    # Only HarnessError is caught (out-of-range version); unexpected errors
    # propagate so they are not silently swallowed.
    _version_adapter = None
    try:
        _bv = getattr(getattr(bpy_module, 'app', None), 'version', None)
        if _bv is not None:
            import platform as _platform
            _identity = RuntimeIdentity(
                blender_version=tuple(_bv)[:3] if isinstance(_bv, tuple) else (0, 0, 0),
                platform=_platform.system().lower(),
                architecture=_platform.machine().lower(),
                runtime_mode=runtime_mode,
            )
            _version_adapter = select_adapter(_identity, bpy_module)
    except HarnessError:
        _version_adapter = None
    official = OfficialUploaderCommands(bpy_module, approved_output_root=approved_output_root, approved_asset_roots=approved_asset_roots)
    organization = OrganizationCommands(bpy_module)
    meshes = MeshCommands(bpy_module)
    modifiers = ModifierCommands(bpy_module)
    curves = CurveCommands(bpy_module)
    asset_policy = PathPolicy(approved_asset_roots) if approved_asset_roots else None
    assets = AssetCommands(bpy_module, asset_policy=asset_policy)
    uvs = UVCommands(bpy_module)
    rigs = RigCommands(bpy_module, adapter=_version_adapter)
    constraints = ConstraintCommands(bpy_module)
    advanced_animation = AdvancedAnimationCommands(bpy_module)
    quality = QualityCommands(bpy_module)
    jobs = JobManager(bpy_module, approved_output_root)
    geometry_nodes = GeometryNodeCommands(bpy_module, adapter=_version_adapter)
    sculpt = SculptCommands(bpy_module)
    retopo = RetopoCommands(bpy_module)
    hair = HairCommands(bpy_module)
    simulation = SimulationCommands(bpy_module,approved_output_root)
    rendering = RenderCommands(bpy_module);compositor=CompositorCommands(bpy_module,approved_output_root);extended=ExtendedExporter(bpy_module,approved_output_root)
    grease_pencil=GreasePencilCommands(bpy_module);sequence=SequenceCommands(bpy_module,asset_policy);tracking=TrackingCommands(bpy_module,asset_policy)
    advanced = AdvancedPythonExecutor(bpy_module)
    exporter = Exporter(bpy_module, approved_output_root=approved_output_root) if approved_output_root else None
    preview = PreviewEngine(bpy_module)

    registry = RuntimeCommandRegistry(bpy_module, output_root=approved_output_root, asset_roots=approved_asset_roots)
    registry.register('capability.list',
                      lambda args: {'changedObjects': [], 'result': registry.list_capabilities(args)},
                      validate=closed_arguments(optional=('domain', 'maturity', 'offset', 'limit',
                                                         'profile', 'runtime', 'blenderVersion', 'platform', 'runtimeMode')),
                      risk='read',
                      availability=lambda: {'status': 'available', 'reason': None},
                      metadata={'effects': {'sceneMutation': False, 'longRunning': False, 'cancellable': False},
                                'tests': ['tests/test_capability_catalog.py', 'tests/test_production_profile.py']})
    registry.register('capability.describe',
                      lambda args: {'changedObjects': [], 'result': registry.describe_capability(args)},
                      validate=closed_arguments(required=('id',), optional=('profile', 'runtime', 'blenderVersion', 'platform', 'runtimeMode')),
                      risk='read',
                      availability=lambda: {'status': 'available', 'reason': None},
                      metadata={'effects': {'sceneMutation': False, 'longRunning': False, 'cancellable': False},
                                'tests': ['tests/test_capability_catalog.py', 'tests/test_production_profile.py']})
    # Production status command: loads the default profile and computes status.
    _default_profile_path = Path(__file__).resolve().parents[2] / 'config' / 'production-profile.json'
    _production_profile = ProductionProfile.load(_default_profile_path) if _default_profile_path.is_file() else None

    def _build_runtime_identity() -> RuntimeIdentity:
        bv = getattr(getattr(bpy_module, 'app', None), 'version', (0, 0, 0))
        import platform as _platform
        return RuntimeIdentity(
            blender_version=tuple(bv)[:3] if isinstance(bv, tuple) else (0, 0, 0),
            platform=_platform.system().lower(),
            architecture=_platform.machine().lower(),
            runtime_mode=runtime_mode,
        )

    def _production_status(_args):
        if _production_profile is None:
            return {'changedObjects': [], 'result': {
                'status': 'unavailable', 'reason': 'No production profile found'}}
        identity = _build_runtime_identity()
        result = _production_profile.status(identity, registry)
        return {'changedObjects': [], 'result': result}

    registry.register('production.status',
                      _production_status,
                      validate=closed_arguments(), risk='read',
                      availability=lambda: {'status': 'available', 'reason': None},
                      metadata={'effects': {'sceneMutation': False, 'longRunning': False, 'cancellable': False},
                                'tests': ['tests/test_production_profile.py']})
    registry.register("scene.inspect", scene.inspect, validate=closed_arguments(), risk="read")
    registry.register('scene.set_units', organization.set_units,
                      validate=closed_arguments(required=('system',), optional=('scaleLength',)))
    registry.register('collection.create', organization.create_collection,
                      validate=closed_arguments(required=('name',), optional=('parent',)))
    registry.register('collection.move_object', organization.move_object,
                      validate=closed_arguments(required=('collection',), optional=('name', 'objectId', 'exclusive')))
    registry.register('collection.set_visibility', organization.set_visibility,
                      validate=closed_arguments(required=('name',), optional=('viewport', 'render')))
    registry.register("view.set", view.set_view, validate=closed_arguments(required=("view",)), risk="read")
    registry.register("view.present", view.present, validate=closed_arguments(), risk="read")
    registry.register("view.focus", view.focus, validate=closed_arguments(required=("object",)), risk="read")
    registry.register("playback.set_frame", view.set_frame, validate=closed_arguments(required=("frame",)), risk="read")
    registry.register("playback.set", view.set_playback, validate=closed_arguments(required=("playing",)), risk="read")
    for command in ("session.pause", "session.resume", "session.set_progress"):
        # Session state operations are intercepted by HarnessSession.handle.
        registry.register(command, lambda _args: {}, risk="gated" if command == "session.resume" else "read")
    registry.register("object.create_mesh", objects.create_mesh, validate=closed_arguments(required=("primitive", "name"), optional=("location", "rotation", "scale")))
    registry.register("object.create_curve", objects.create_curve, validate=closed_arguments(required=("name",), optional=("bevelDepth",)))
    registry.register("object.create_text", objects.create_text, validate=closed_arguments(required=("name", "text"), optional=("size", "extrude")))
    registry.register("object.transform", objects.transform, validate=closed_arguments(optional=("name",'objectId', "location", "rotation", "scale",'space')))
    registry.register("object.rename", objects.rename, validate=closed_arguments(required=("newName",), optional=("name",'objectId')))
    registry.register("object.parent", objects.parent, validate=closed_arguments(optional=("child", "parent",'childObjectId','parentObjectId','keepWorld')))
    registry.register("object.delete", objects.delete, validate=closed_arguments(optional=("name",'objectId')), risk="gated")
    registry.register('object.describe', objects.describe,
                      validate=closed_arguments(optional=('name', 'objectId')), risk='read')
    registry.register('object.duplicate', objects.duplicate,
                      validate=closed_arguments(required=('newName',), optional=('name', 'objectId')))
    registry.register('object.instance', objects.instance,
                      validate=closed_arguments(required=('newName',), optional=('name', 'objectId')))
    registry.register('object.set_visibility', objects.set_visibility,
                      validate=closed_arguments(optional=('name', 'objectId', 'viewport', 'render')))
    registry.register('object.set_display', objects.set_display,
                      validate=closed_arguments(required=('displayType',), optional=('name','objectId','showInFront')))
    registry.register('object.apply_transform', objects.apply_transform,
                      validate=closed_arguments(optional=('name', 'objectId', 'location', 'rotation', 'scale')))
    registry.register('object.set_origin', objects.set_origin,
                      validate=closed_arguments(required=('origin',), optional=('name', 'objectId')))
    registry.register('object.join', objects.join,
                      validate=closed_arguments(required=('objects',), optional=('newName',)))
    registry.register('object.separate', objects.separate,
                      validate=closed_arguments(optional=('name', 'objectId', 'method')))
    registry.register('mesh.inspect', meshes.inspect,
                      validate=closed_arguments(optional=('name', 'objectId', 'tolerance', 'allowOpenSurface')), risk='read')
    registry.register('mesh.select', meshes.select,
                      validate=closed_arguments(required=('method',), optional=('name', 'objectId', 'vertices', 'edges',
                                               'faces', 'min', 'max', 'seedVertex', 'direction', 'angleDegrees')), risk='read')
    registry.register('mesh.edit', meshes.edit,
                      validate=closed_arguments(required=('operation', 'selection'), optional=('offset', 'thickness',
                                               'depth', 'width', 'segments', 'cuts', 'distance')))
    registry.register("modifier.add", modifiers.create, validate=closed_arguments(required=("modifier",), optional=("name", "objectId", "modifierName", "settings")))
    registry.register('modifier.list', modifiers.list, validate=closed_arguments(optional=('name', 'objectId')), risk='read')
    registry.register('modifier.configure', modifiers.configure,
                      validate=closed_arguments(required=('modifierName', 'settings'), optional=('name', 'objectId')))
    registry.register('modifier.move', modifiers.move,
                      validate=closed_arguments(required=('modifierName', 'targetIndex'), optional=('name', 'objectId')))
    registry.register('modifier.set_enabled', modifiers.set_enabled,
                      validate=closed_arguments(required=('modifierName',), optional=('name', 'objectId', 'viewport', 'render')))
    registry.register('modifier.apply', modifiers.apply,
                      validate=closed_arguments(required=('modifierName',), optional=('name', 'objectId')))
    registry.register('modifier.remove', modifiers.remove,
                      validate=closed_arguments(required=('modifierName',), optional=('name', 'objectId')))
    registry.register('curve.create', curves.create,
                      validate=closed_arguments(required=('name','points'), optional=('splineType','cyclic','handleType',
                                               'bevelDepth','bevelResolution','resolution')))
    registry.register('curve.configure', curves.configure,
                      validate=closed_arguments(optional=('name','objectId','bevelDepth','bevelResolution','resolution')))
    registry.register('curve.to_mesh', curves.to_mesh,
                      validate=closed_arguments(optional=('name','objectId')))
    registry.register('asset.import_file', assets.import_file,
                      validate=closed_arguments(required=('path',)))
    registry.register('asset.library', assets.library,
                      validate=closed_arguments(required=('path','dataType','names'), optional=('link',)))
    registry.register('asset.pack_resources',assets.pack_resources,validate=closed_arguments())
    registry.register('asset.make_paths_relative',assets.make_paths_relative,validate=closed_arguments())
    registry.register('uv.mark_seams',uvs.mark_seams,
                      validate=closed_arguments(required=('selection',),optional=('seam',)))
    registry.register('uv.unwrap',uvs.unwrap,
                      validate=closed_arguments(required=('selection',),optional=('method','margin')))
    registry.register('uv.pack',uvs.pack,
                      validate=closed_arguments(required=('selection',),optional=('margin',)))
    registry.register('uv.inspect',uvs.inspect,
                      validate=closed_arguments(optional=('name','objectId')),risk='read')
    registry.register('uv.detect_overlap',uvs.detect_overlap,
                      validate=closed_arguments(optional=('name','objectId','uvLayer','tolerance')),risk='read')
    registry.register('uv.measure_texel_density',uvs.measure_texel_density,
                      validate=closed_arguments(required=('textureWidth','textureHeight'),optional=('name','objectId','uvLayer','targetDensity')),risk='read')
    registry.register('rig.create_armature',rigs.create_armature,
                      validate=closed_arguments(required=('name','bones')))
    registry.register('rig.create_control',rigs.create_control,
                      validate=closed_arguments(required=('name','location'),optional=('size','shape')))
    registry.register('rig.bind',rigs.bind,
                      validate=closed_arguments(required=('mesh','armature')))
    registry.register('rig.assign_weights',rigs.assign_weights,
                      validate=closed_arguments(required=('mesh','selection','bone'),optional=('weight','mode')))
    registry.register('rig.inspect',rigs.inspect,
                      validate=closed_arguments(optional=('name','objectId')),risk='read')
    registry.register('constraint.add_bone',constraints.add_bone,
                      validate=closed_arguments(required=('armatureId','bone','type','name'),optional=('targetObjectId','poleObjectId',
                        'chainLength','poleAngle','influence','subtarget','minRotation','maxRotation')))
    registry.register('constraint.add_object',constraints.add_object,
                      validate=closed_arguments(required=('owner','target','bone','type','name'),optional=('influence',)))
    registry.register('constraint.keyframe_influence',constraints.keyframe_influence,
                      validate=closed_arguments(required=('owner','constraintName','frame','influence')))
    registry.register("material.create_pbr", materials.create_pbr, validate=closed_arguments(required=("name",), optional=("baseColor", "metallic", "roughness", "alpha")))
    registry.register("material.assign", materials.assign, validate=closed_arguments(required=("object", "material")))
    registry.register("material.attach_image_texture", materials.attach_image_texture, validate=closed_arguments(required=("material", "path")))
    registry.register('material.connect_image_texture',materials.connect_image_texture,
                      validate=closed_arguments(required=('material','path','usage')))
    registry.register('material.inspect_nodes',materials.inspect_nodes,
                      validate=closed_arguments(required=('material',)),risk='read')
    registry.register('material.create_node_group',materials.create_node_group,
                      validate=closed_arguments(required=('material','groupName'),optional=('baseColor','roughness')))
    registry.register('material.bake',materials.bake,
                      validate=closed_arguments(required=('object','relativePath'),optional=('bakeType','width','height','margin')))
    registry.register("camera.create", cameras.create, validate=closed_arguments(required=("name",), optional=("location", "rotation", "lens", "active")))
    registry.register('camera.aim_at',cameras.aim_at,
                      validate=closed_arguments(required=('name',),optional=('target','targetObject')))
    registry.register("light.create", lights.create, validate=closed_arguments(required=("name",), optional=("type", "location", "energy", "color", "size")))
    registry.register("light.set_world_color", lights.set_world_color, validate=closed_arguments(required=("color",)))
    registry.register("animation.set_frame_range", animation.set_frame_range, validate=closed_arguments(required=("start", "end")))
    registry.register("animation.insert_keyframe", animation.insert_keyframe, validate=closed_arguments(required=("object", "dataPath", "frame")))
    registry.register('animation.pose_keyframe',animation.pose_keyframe,
                      validate=closed_arguments(required=('armature','bone','dataPath','frame','value')))
    registry.register('animation.action_list',advanced_animation.action_list,validate=closed_arguments(),risk='read')
    registry.register('animation.fcurve_edit',advanced_animation.fcurve_edit,
                      validate=closed_arguments(required=('dataPath',),optional=('name','objectId','arrayIndex','timeScale','timeOffset','valueScale','valueOffset','interpolation')))
    registry.register('animation.fcurve_clean',advanced_animation.fcurve_clean,
                      validate=closed_arguments(required=('dataPath',),optional=('name','objectId','arrayIndex','threshold')))
    registry.register('animation.nla_add_strip',advanced_animation.nla_add_strip,
                      validate=closed_arguments(required=('action','track','name','start'),optional=('objectId','scale','repeat','blendType')))
    registry.register('animation.shape_key_add',advanced_animation.shape_key_add,
                      validate=closed_arguments(required=('keyName',),optional=('name','objectId','fromMix')))
    registry.register('animation.shape_key_keyframe',advanced_animation.shape_key_keyframe,
                      validate=closed_arguments(required=('keyName','frame','value'),optional=('name','objectId')))
    registry.register('animation.retarget',advanced_animation.retarget,
                      validate=closed_arguments(required=('source','target','boneMap','frameStart','frameEnd'),optional=('step',)))
    registry.register('camera.follow_path',advanced_animation.camera_follow_path,
                      validate=closed_arguments(required=('camera','path','name','frameStart','frameEnd'),optional=('targetObjectId',)))
    registry.register('camera.add_handheld',advanced_animation.camera_handheld,
                      validate=closed_arguments(required=('frameStart','frameEnd'),optional=('name','objectId','translationStrength','rotationStrength','noiseScale','seed')))
    common_validation=('frameStart','frameEnd','limit')
    registry.register('validation.foot_drift',quality.foot_drift,
                      validate=closed_arguments(required=('armature','bone','frameStart','frameEnd'),optional=('limit',)),risk='read')
    registry.register('validation.limb_length',quality.limb_length,
                      validate=closed_arguments(required=('armature','bones','frameStart','frameEnd'),optional=('limit',)),risk='read')
    registry.register('validation.floor_penetration',quality.floor_penetration,
                      validate=closed_arguments(required=('object','frameStart','frameEnd'),optional=('floorZ','limit')),risk='read')
    registry.register('validation.prop_handoff',quality.prop_handoff,
                      validate=closed_arguments(required=('object','armature','bone','constraintName','frameStart','frameEnd','catchFrame')),risk='read')
    registry.register('validation.camera_visibility',quality.camera_visibility,
                      validate=closed_arguments(required=('camera','objects','frameStart','frameEnd')),risk='read')
    registry.register('validation.motion_discontinuity',quality.motion_discontinuity,
                      validate=closed_arguments(required=('object','frameStart','frameEnd','positionLimit','angleLimitDegrees')),risk='read')
    registry.register('job.submit',jobs.submit,
                      validate=closed_arguments(required=('kind',),optional=('jobId','format','parameters')))
    registry.register('job.status',jobs.status,validate=closed_arguments(required=('jobId',)),risk='read')
    registry.register('job.cancel',jobs.cancel,validate=closed_arguments(required=('jobId',)),risk='read')
    registry.register('job.recover',jobs.recover,validate=closed_arguments(required=('jobId',)),risk='read')
    registry.register('job.resume',jobs.resume,validate=closed_arguments(required=('jobId',)))
    registry.register('geometry_nodes.create_group',geometry_nodes.create_group,
                      validate=closed_arguments(required=('object','groupName','modifierName'),optional=('inputs',)))
    registry.register('geometry_nodes.add_node',geometry_nodes.add_node,
                      validate=closed_arguments(required=('groupName','nodeType','name'),optional=('label',)))
    registry.register('geometry_nodes.connect',geometry_nodes.connect,
                      validate=closed_arguments(required=('groupName','fromNode','fromSocket','toNode','toSocket')))
    registry.register('geometry_nodes.set_node_input',geometry_nodes.set_node_input,
                      validate=closed_arguments(required=('groupName','node','socket','value')))
    registry.register('geometry_nodes.set_modifier_input',geometry_nodes.set_modifier_input,
                      validate=closed_arguments(required=('object','modifierName','socket','value')))
    registry.register('geometry_nodes.inspect',geometry_nodes.inspect,
                      validate=closed_arguments(required=('groupName',)),risk='read')
    registry.register('sculpt.set_mask',sculpt.set_mask,validate=closed_arguments(required=('selection','value')))
    registry.register('sculpt.displace',sculpt.displace,validate=closed_arguments(required=('selection','strength'),optional=('direction',)))
    registry.register('sculpt.voxel_remesh',sculpt.voxel_remesh,validate=closed_arguments(required=('voxelSize',),optional=('name','objectId')))
    registry.register('sculpt.multires',sculpt.multires,validate=closed_arguments(optional=('name','objectId','levels','modifierName')))
    registry.register('sculpt.cleanup',sculpt.cleanup,validate=closed_arguments(optional=('name','objectId','ratio','modifierName','target')))
    registry.register('sculpt.brush_stroke',sculpt.brush_stroke,validate=closed_arguments(required=('points',),optional=('name','objectId')))
    registry.register('retopo.setup_surface',retopo.setup_surface,
                      validate=closed_arguments(required=('sourceObjectId','targetName'),optional=('symmetry','offset')))
    registry.register('retopo.project',retopo.project,
                      validate=closed_arguments(required=('objectId','sourceObjectId'),optional=('method','maxDistance')))
    registry.register('retopo.transfer_layers',retopo.transfer_layers,
                      validate=closed_arguments(required=('sourceObjectId','targetObjectId','layers')))
    registry.register('retopo.validate',retopo.validate,
                      validate=closed_arguments(required=('objectId','sourceObjectId'),optional=('maxDeviation','maxPoleValence')),
                      risk='read')
    registry.register('hair.create_curves',hair.create_curves,validate=closed_arguments(required=('surface','name','strands'),optional=('radius',)))
    registry.register('hair.inspect',hair.inspect,validate=closed_arguments(optional=('name','objectId')),risk='read')
    registry.register('simulation.rigid_body',simulation.rigid_body,validate=closed_arguments(required=('bodyType',),optional=('name','objectId','collisionShape','mass')))
    registry.register('simulation.collision',simulation.collision,validate=closed_arguments(optional=('name','objectId','thickness')))
    registry.register('simulation.cloth',simulation.cloth,validate=closed_arguments(optional=('name','objectId','modifierName','quality','mass','frameStart','frameEnd')))
    registry.register('simulation.soft_body',simulation.soft_body,validate=closed_arguments(optional=('name','objectId','modifierName','frameStart','frameEnd')))
    registry.register('simulation.quick_smoke',simulation.quick_smoke,validate=closed_arguments(required=('flows',),optional=('resolution','frameStart','frameEnd')))
    registry.register('simulation.cache_status',simulation.cache_status,validate=closed_arguments(optional=('name','objectId')),risk='read')
    registry.register('simulation.free_cache',simulation.free_cache,validate=closed_arguments(optional=('name','objectId')))
    registry.register('render.configure',rendering.configure,
                      validate=closed_arguments(required=('engine',),optional=('device','allowCpuFallback','width','height','samples','transparent','look','exposure')))
    registry.register('render.configure_passes',rendering.configure_passes,
                      validate=closed_arguments(required=('passes',),optional=('viewLayer',)))
    registry.register('render.create_view_layer',rendering.create_view_layer,validate=closed_arguments(required=('name',)))
    registry.register('render.inspect',rendering.inspect,validate=closed_arguments(),risk='read')
    registry.register('compositor.configure',compositor.configure,validate=closed_arguments(optional=('exposure','glare')))
    registry.register('compositor.inspect',compositor.inspect,validate=closed_arguments(),risk='read')
    registry.register('compositor.add_tracking_mask',compositor.add_tracking_mask,
                      validate=closed_arguments(required=('clip','maskName','points')))
    registry.register('compositor.add_file_output',compositor.add_file_output,
                      validate=closed_arguments(required=('name','outputDir','baseName','format'),optional=('colorDepth',)))
    registry.register('compositor.create_strip_group',compositor.create_strip_group,
                      validate=closed_arguments(required=('name',),optional=('exposure',)))
    registry.register('export.extended',extended.export,validate=closed_arguments(required=('path','format')),risk='gated')
    registry.register('grease_pencil.create',grease_pencil.create,validate=closed_arguments(required=('name',),optional=('layers','inFront')))
    registry.register('grease_pencil.add_material',grease_pencil.add_material,
                      validate=closed_arguments(required=('material','color'),optional=('name','objectId')))
    registry.register('grease_pencil.add_stroke',grease_pencil.add_stroke,
                      validate=closed_arguments(required=('layer','frame','points'),optional=('name','objectId','materialIndex','cyclic')))
    registry.register('grease_pencil.inspect',grease_pencil.inspect,validate=closed_arguments(optional=('name','objectId')),risk='read')
    registry.register('sequence.add',sequence.add,validate=closed_arguments(required=('type','name','channel','frameStart'),
                      optional=('path','paths','scene','text','duration','fontSize')))
    registry.register('sequence.trim',sequence.trim,validate=closed_arguments(required=('name',),optional=('frameStart','frameEnd')))
    registry.register('sequence.move',sequence.move,validate=closed_arguments(required=('name','frameStart'),optional=('channel',)))
    registry.register('sequence.transition',sequence.transition,validate=closed_arguments(required=('name','first','second','channel'),optional=('transitionType',)))
    registry.register('sequence.set_speed',sequence.set_speed,
                      validate=closed_arguments(required=('name','source','channel','factor'),optional=('interpolate',)))
    registry.register('sequence.set_volume',sequence.set_volume,validate=closed_arguments(required=('name','volume')))
    registry.register('sequence.keyframe_volume',sequence.keyframe_volume,
                      validate=closed_arguments(required=('name','frame','volume')))
    registry.register('sequence.add_compositor_modifier',sequence.add_compositor_modifier,
                      validate=closed_arguments(required=('strip','name','groupName')))
    registry.register('sequence.configure_output',sequence.configure_output,
                      validate=closed_arguments(required=('frameStart','frameEnd'),optional=('width','height','fps')))
    registry.register('sequence.inspect',sequence.inspect,validate=closed_arguments(),risk='read')
    registry.register('tracking.load_clip',tracking.load_clip,validate=closed_arguments(required=('name','path'),optional=('focalLengthPixels',)))
    registry.register('tracking.add_track',tracking.add_track,validate=closed_arguments(required=('clip','name','markers')))
    registry.register('tracking.solve_camera',tracking.solve_camera,validate=closed_arguments(required=('clip','keyframeA','keyframeB')))
    registry.register('tracking.setup_scene',tracking.setup_scene,validate=closed_arguments(required=('clip',)))
    registry.register('tracking.inspect',tracking.inspect,validate=closed_arguments(required=('clip',)),risk='read')
    registry.register('rig.rigify_status',rigs.rigify_status,validate=closed_arguments(),risk='read')
    registry.register('rig.rigify_install',rigs.rigify_install,
                      validate=closed_arguments(optional=('allowDownload','savePreferences')),risk='gated')
    registry.register('rig.rigify_generate',rigs.rigify_generate,validate=closed_arguments(optional=('name','objectId')))
    registry.register("advanced.execute_python", advanced.execute, validate=closed_arguments(required=("script",)), risk="gated",
                      metadata={'class': 'expert'})
    if runtime_mode == "connector":
        registry.register("official_uploader.inspect", official.inspect, validate=closed_arguments(), risk="read")
        registry.register("official_uploader.status", official.status, validate=closed_arguments(), risk="read")
        registry.register("official_uploader.render_and_link", official.render_and_link, validate=closed_arguments(required=("camera", "frameStart", "frameEnd", "outputDir"), optional=("resolution", "prompt")), risk="gated")
        registry.register("official_uploader.link_existing", official.link_existing, validate=closed_arguments(required=("videoPath",), optional=("prompt",)), risk="gated")
        registry.register("official_uploader.open_link", official.open_link, validate=closed_arguments(), risk="gated")
    def capture_preview(arguments):
        from .errors import HarnessError
        if approved_output_root is None:
            from .errors import HarnessError
            raise HarnessError("OUTPUT_NOT_AUTHORIZED", "preview output root is unavailable")
        snapshot_id = str(arguments.get("snapshotId", "uncommitted"))
        if re.fullmatch(r"[A-Za-z0-9_-]{1,128}", snapshot_id) is None:
            raise HarnessError("INVALID_ARGUMENT", "snapshotId must be a simple identifier, not a path")
        output_dir = Path(approved_output_root) / "milestones" / snapshot_id
        if not output_dir.resolve().is_relative_to(Path(approved_output_root).resolve()):
            raise HarnessError("OUTPUT_NOT_AUTHORIZED", "preview directory escapes the approved output root")
        receipt = preview.capture_milestone(
            output_dir,
            milestone=str(arguments.get("milestone", "final_preview")),
            scene_revision=revision_provider(),
            snapshot_id=snapshot_id,
            width=int(arguments.get("width", 512)),
            height=int(arguments.get("height", 512)),
        )
        return {"changedObjects": [], "result": {"milestone": receipt}}

    registry.register(
        "preview.capture",
        capture_preview,
        validate=closed_arguments(required=("snapshotId",), optional=("milestone", "width", "height")),
        risk="read",
    )
    if exporter is not None:
        def export_file(arguments):
            receipt = exporter.export(
                Path(arguments["path"]),
                session_id=str(arguments.get("sessionId", "active")),
                scene_revision=revision_provider(),
                snapshot_id=str(arguments.get("snapshotId", "uncommitted")),
                overwrite=bool(arguments.get("overwrite", False)),
                parameters=dict(arguments.get("parameters", {})),
            )
            return {"changedObjects": [], "result": {"artifact": receipt}}

        registry.register(
            "export.file",
            export_file,
            validate=closed_arguments(required=("path", "snapshotId"), optional=("sessionId", "overwrite", "parameters")),
            risk="gated",
        )
    registry.register(
        "session.status",
        lambda _arguments: {"changedObjects": [], "result": {"sceneRevision": revision_provider()}},
        risk="read",
    )
    registry.register(
        "session.capabilities",
        lambda _arguments: {"changedObjects": [], "result": {"commands": registry.capabilities()}},
        risk="read",
    )
    recipes = RecipeCommands(bpy_module, registry.dispatch)
    registry.register('recipe.hard_surface_shell', recipes.hard_surface_shell,
                      validate=closed_arguments(required=('name','dimensions','wallThickness'), optional=('bevelWidth',)),
                      metadata={'skills':['blender-hard-surface'],
                                'effects':{'sceneMutation':True,'longRunning':False,'cancellable':False},
                                'tests':['tests/runtime/p1_recipe_smoke.py']})
    registry.register('recipe.spear', recipes.spear,
                      validate=closed_arguments(required=('name','length','shaftRadius','headLength','headRadius')),
                      metadata={'skills':['blender-hard-surface'],
                                'effects':{'sceneMutation':True,'longRunning':False,'cancellable':False},
                                'tests':['tests/runtime/p1_recipe_smoke.py']})
    registry.register('recipe.desktop_speaker',recipes.desktop_speaker,
                      validate=closed_arguments(required=('name','dimensions'),optional=('bevelWidth','wallThickness')),
                      metadata={'maturity':'L2','skills':['blender-hard-surface','blender-uv-material'],
                                'effects':{'sceneMutation':True,'longRunning':False,'cancellable':False},
                                'tests':['tests/runtime/p2_product_acceptance.py']})
    registry.register('recipe.rigged_spear_character',recipes.rigged_spear_character,
                      validate=closed_arguments(required=('name',),optional=('height','releaseFrame','apexFrame','catchFrame')),
                      metadata={'maturity':'L2','skills':['blender-character-rigging','blender-character-animation'],
                                'effects':{'sceneMutation':True,'longRunning':False,'cancellable':False},
                                'tests':['tests/runtime/p2_character_acceptance.py']})
    registry.register('recipe.procedural_courtyard',recipes.procedural_courtyard,
                      validate=closed_arguments(required=('name','dimensions','archCount'),optional=('rubbleDensity',)),
                      metadata={'maturity':'L2','skills':['blender-procedural-modeling'],
                                'effects':{'sceneMutation':True,'longRunning':False,'cancellable':False},
                                'tests':['tests/runtime/p4_courtyard_acceptance.py']})
    registry.register('recipe.update_procedural_courtyard',recipes.update_procedural_courtyard,
                      validate=closed_arguments(required=('name',),optional=('dimensions','archCount','rubbleDensity')),
                      metadata={'maturity':'L2','skills':['blender-procedural-modeling'],
                                'effects':{'sceneMutation':True,'longRunning':False,'cancellable':False},
                                'tests':['tests/runtime/p4_courtyard_acceptance.py']})
    return registry


def create_session(bpy_module, session_id: str, *, runtime_mode: str = "managed", approved_output_root: Path | None = None, approved_asset_roots=(), transactions=None, execution_policy: ExecutionPolicy | None = None) -> HarnessSession:
    policy = execution_policy or ExecutionPolicy.interactive()
    if policy.mode is ExecutionMode.AUTO_WITH_BUDGET and (
        approved_output_root is None or Path(policy.approved_output_root) != Path(approved_output_root).resolve()
    ):
        raise ValueError("execution policy output root must match the runtime output root")
    holder = {}
    registry = build_registry(
        bpy_module,
        runtime_mode=runtime_mode,
        approved_output_root=approved_output_root,
        approved_asset_roots=approved_asset_roots,
        revision_provider=lambda: holder["session"].scene_revision,
    )
    session = HarnessSession(session_id, dispatch=registry.dispatch, transactions=transactions, execution_policy=policy)
    holder["session"] = session
    return session
