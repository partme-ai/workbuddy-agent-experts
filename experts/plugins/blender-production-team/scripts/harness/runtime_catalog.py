"""Registration-time descriptions and non-mutating runtime prerequisite probes.

These describe existing commands, not additional supported Blender operations.
Argument-specific object/path/authorization checks remain in the command/session.
"""
from copy import deepcopy
from pathlib import Path

from .errors import HarnessError
from .registry import CommandRegistry
from .commands.validation import closed_arguments


VECTOR = {'type': 'array', 'minItems': 3, 'maxItems': 3,
          'items': {'type': 'number'}, 'description': 'Three finite numbers; rotation uses radians'}
FIELDS = {
    **{key: {'type': 'string'} for key in (
        'name', 'newName', 'object', 'child', 'parent', 'material', 'primitive',
        'modifier', 'type', 'path', 'videoPath', 'outputDir', 'snapshotId', 'sessionId',
        'camera', 'dataPath', 'text', 'script', 'milestone', 'prompt', 'id', 'domain', 'maturity', 'view',
        'baseName', 'groupName', 'strip', 'colorDepth', 'uvLayer')},
    **{key: VECTOR for key in ('location', 'rotation', 'scale', 'color')},
    'baseColor': {'type': 'array', 'minItems': 4, 'maxItems': 4,
                  'items': {'type': 'number', 'minimum': 0, 'maximum': 1}},
    **{key: {'type': 'number'} for key in ('bevelDepth', 'size', 'extrude', 'lens', 'energy', 'metallic', 'roughness', 'alpha')},
    **{key: {'type': 'integer'} for key in ('frame', 'start', 'end', 'frameStart', 'frameEnd', 'width', 'height', 'limit', 'offset')},
    **{key: {'type': 'boolean'} for key in ('active', 'playing', 'overwrite')},
    **{key: {'type': 'boolean'} for key in ('exclusive', 'viewport', 'render')},
    'objectId': {'type': 'string', 'pattern': '^obj_[0-9a-f]{32}$'},
    'newName': {'type': 'string', 'minLength': 1},
    'collection': {'type': 'string', 'minLength': 1},
    'parent': {'type': 'string', 'minLength': 1},
    'system': {'type': 'string', 'enum': ['METRIC', 'IMPERIAL', 'NONE']},
    'scaleLength': {'type': 'number', 'exclusiveMinimum': 0},
    'origin': {'type': 'string', 'enum': ['GEOMETRY', 'CENTER_OF_MASS', 'CENTER_OF_VOLUME', 'CURSOR']},
    'method': {'type': 'string', 'enum': ['indices', 'spatial', 'connected', 'normal']},
    'operation': {'type': 'string', 'enum': ['extrude', 'inset', 'bevel', 'subdivide', 'bridge', 'weld', 'delete', 'triangulate', 'recalculate_normals']},
    'selection': {'type': 'object', 'required': ['objectId', 'topologyVersion'],
                  'description': 'Selection receipt returned by mesh.select'},
    **{key: VECTOR for key in ('min', 'max', 'direction', 'offset')},
    **{key: {'type': 'array', 'items': {'type': 'integer', 'minimum': 0}} for key in ('vertices', 'edges', 'faces')},
    **{key: {'type': 'number'} for key in ('tolerance', 'angleDegrees', 'thickness', 'depth', 'width', 'distance')},
    **{key: {'type': 'integer', 'minimum': 1} for key in ('seedVertex', 'segments', 'cuts')},
    'textureWidth': {'type': 'integer', 'minimum': 1},
    'textureHeight': {'type': 'integer', 'minimum': 1},
    'targetDensity': {'type': 'number', 'exclusiveMinimum': 0},
    'allowOpenSurface': {'type': 'boolean'},
    'allowDownload': {'type':'boolean'}, 'savePreferences': {'type':'boolean'},
    'modifierName': {'type': 'string', 'minLength': 1},
    'targetIndex': {'type': 'integer', 'minimum': 0},
    'objects': {'type': 'array', 'minItems': 2, 'items': {'type': 'object'}},
    'keepWorld': {'type': 'boolean'},
    'points': {'type': 'array', 'minItems': 2, 'items': VECTOR},
    'splineType': {'type': 'string', 'enum': ['POLY','BEZIER']},
    'cyclic': {'type': 'boolean'},
    'handleType': {'type': 'string', 'enum': ['AUTO','VECTOR','ALIGNED','FREE']},
    'bevelResolution': {'type': 'integer', 'minimum': 0},
    'resolution': {'type': 'integer', 'minimum': 1},
    'dataType': {'type': 'string', 'enum': ['OBJECT','COLLECTION']},
    'names': {'type': 'array', 'minItems': 1, 'items': {'type':'string'}},
    'link': {'type': 'boolean'},
    'childObjectId': {'type':'string','pattern':'^obj_[0-9a-f]{32}$'},
    'parentObjectId': {'type':'string','pattern':'^obj_[0-9a-f]{32}$'},
    'space': {'type':'string','enum':['LOCAL','WORLD']},
    'displayType': {'type':'string','enum':['BOUNDS','WIRE','SOLID','TEXTURED']},
    'showInFront': {'type':'boolean'},
    'seam': {'type':'boolean'},
    'usage': {'type':'string','enum':['BASE_COLOR','ROUGHNESS','METALLIC','NORMAL']},
    'margin': {'type':'number','minimum':0},
    'target': VECTOR,
    'targetObject': {'type':'string'},
    'bones': {'type':'array','minItems':1,'items':{'type':'object'}},
    'mesh': {'type':'object'}, 'armature': {'type':'object'}, 'owner': {'type':'object'},
    'bone': {'type':'string'}, 'armatureId': {'type':'string'},
    'targetObjectId': {'type':'string'}, 'poleObjectId': {'type':['string','null']},
    'chainLength': {'type':'integer','minimum':1}, 'poleAngle': {'type':'number'},
    'influence': {'type':'number','minimum':0,'maximum':1}, 'subtarget': {'type':'string'},
    'minRotation': VECTOR, 'maxRotation': VECTOR, 'value': VECTOR,
    'constraintName': {'type':'string'}, 'mode': {'type':'string'}, 'weight': {'type':'number'},
    'height': {'type':'number','exclusiveMinimum':0},
    **{key:{'type':'integer','minimum':1} for key in ('releaseFrame','apexFrame','catchFrame')},
    'arrayIndex': {'type':'integer','minimum':0},
    **{key:{'type':'number'} for key in ('timeScale','timeOffset','valueScale','valueOffset','start','repeat','positionLimit','angleLimitDegrees','floorZ')},
    'interpolation': {'type':'string','enum':['CONSTANT','LINEAR','BEZIER']},
    'action': {'type':'string'}, 'track': {'type':'string'}, 'blendType': {'type':'string'},
    'keyName': {'type':'string'}, 'fromMix': {'type':'boolean'},
    'source': {'type':'object'}, 'boneMap': {'type':'object'}, 'frameStart': {'type':'integer'},
    'frameEnd': {'type':'integer'}, 'step': {'type':'integer','minimum':1},
    'camera': {'type':'object'}, 'path': {'type':'object'},
    'jobId': {'type':'string','pattern':'^job_[A-Za-z0-9_-]{1,80}$'},
    'kind': {'type':'string','enum':['EXPORT','RENDER_STILL','BAKE_POINT_CACHES','RENDER_ANIMATION_FRAMES','COMPOSE_VIDEO']},
    'format': {'type':'string','enum':['blend','glb','gltf','fbx','obj']},
    'inputs': {'type':'array','items':{'type':'object'}}, 'groupName': {'type':'string'},
    'nodeType': {'type':'string'}, 'label': {'type':'string'}, 'fromNode': {'type':'string'},
    'fromSocket': {'type':'string'}, 'toNode': {'type':'string'}, 'toSocket': {'type':'string'},
    'node': {'type':'string'}, 'socket': {'type':'string'},
    'archCount': {'type':'integer','minimum':1}, 'rubbleDensity': {'type':'number','minimum':0},
    'voxelSize': {'type':'number','exclusiveMinimum':0}, 'strength': {'type':'number'},
    'levels': {'type':'integer','minimum':1,'maximum':6}, 'ratio': {'type':'number','exclusiveMinimum':0,'maximum':1},
    'surface': {'type':'object'}, 'strands': {'type':'array','minItems':1}, 'radius': {'type':'number','exclusiveMinimum':0},
    'bodyType': {'type':'string','enum':['ACTIVE','PASSIVE']}, 'collisionShape': {'type':'string'},
    'mass': {'type':'number','exclusiveMinimum':0}, 'thickness': {'type':'number','minimum':0},
    'quality': {'type':'integer','minimum':1}, 'flows': {'type':'array','minItems':1},
    'bakeType': {'type':'string','enum':['ROUGHNESS','NORMAL','AO','EMIT']},
    'relativePath': {'type':'string'}, 'device': {'type':'string','enum':['AUTO','CPU','GPU']},
    'allowCpuFallback': {'type':'boolean'}, 'samples': {'type':'integer','minimum':1},
    'transparent': {'type':'boolean'}, 'look': {'type':'string'}, 'exposure': {'type':'number'},
    'passes': {'type':'array','items':{'type':'string'}}, 'viewLayer': {'type':'string'}, 'glare': {'type':'boolean'},
    'layers': {'type':'array','items':{'type':'string'}}, 'inFront': {'type':'boolean'},
    'layer': {'type':'string'}, 'points': {'type':'array','minItems':2}, 'materialIndex': {'type':'integer','minimum':0},
    'type': {'type':'string'}, 'channel': {'type':'integer','minimum':1}, 'duration': {'type':'integer','minimum':1},
    'paths': {'type':'array','minItems':1,'items':{'type':'string'}}, 'scene': {'type':'string'},
    'fontSize': {'type':'number','exclusiveMinimum':0},
    'factor': {'type':'number','exclusiveMinimum':0,'maximum':100}, 'interpolate': {'type':'boolean'},
    'transitionType': {'type':'string','enum':['CROSS','GAMMA_CROSS','WIPE','SOUND_CROSSFADE']},
    'first': {'type':'string'}, 'second': {'type':'string'}, 'volume': {'type':'number','minimum':0}, 'fps': {'type':'integer','minimum':1},
    'clip': {'type':'string'}, 'markers': {'type':'array','minItems':1}, 'keyframeA': {'type':'integer'}, 'keyframeB': {'type':'integer'},
    'focalLengthPixels': {'type':'number','exclusiveMinimum':0},
    'maskName': {'type':'string'},
    'threshold': {'type':'number','minimum':0}, 'translationStrength': {'type':'number','minimum':0},
    'rotationStrength': {'type':'number','minimum':0}, 'noiseScale': {'type':'number','exclusiveMinimum':0}, 'seed': {'type':'integer'},
    'sourceObjectId': {'type':'object','description':'Object locator for the source mesh'},
    'targetObjectId': {'type':'object','description':'Object locator for the target mesh'},
    'targetName': {'type':'string','minLength':1},
    'symmetry': {'type':'string','enum':['none','x','y','z']},
    'maxDistance': {'type':'number','exclusiveMinimum':0},
    'maxDeviation': {'type':'number','exclusiveMinimum':0},
    'maxPoleValence': {'type':'integer','minimum':3},
    'dimensions': VECTOR,
    **{key:{'type':'number','exclusiveMinimum':0} for key in ('wallThickness','bevelWidth','length','shaftRadius','headLength','headRadius')},
    'settings': {'type': 'object', 'description': 'Existing modifier RNA properties; not a typed modifier workflow'},
    'parameters': {'type': 'object', 'description': 'Format-specific exporter parameters'},
    'resolution': {'type': 'string', 'description': 'Official uploader resolution label; default 720p'},
    'stage': {'type': 'string', 'minLength': 1, 'maxLength': 80},
    'progress': {'type': ['number', 'null'], 'minimum': 0, 'maximum': 1},
    'metrics': {'type': 'object', 'description': 'Per-metric toggle dict for simulation.validate'},
    'easing': {'type': 'string', 'enum': ['LINEAR', 'EASE_IN', 'EASE_OUT', 'EASE_IN_OUT', 'BOUNCE', 'ELASTIC']},
    'sizes': {'type': 'array', 'items': {'type': 'integer', 'enum': [25, 50, 75, 100]}, 'minItems': 1},
    'directory': {'type': 'string'},
    'modifierType': {'type': 'string'},
    'lift': {'type': 'array', 'minItems': 3, 'maxItems': 3, 'items': {'type': 'number'}},
    'gamma': {'type': 'array', 'minItems': 3, 'maxItems': 3, 'items': {'type': 'number'}},
    'gain': {'type': 'array', 'minItems': 3, 'maxItems': 3, 'items': {'type': 'number'}},
    'offset_x': {'type': 'number'}, 'offset_y': {'type': 'number'},
    'scale_x': {'type': 'number'}, 'scale_y': {'type': 'number'},
    'rotation': {'type': 'number'},
    'min_x': {'type': 'integer', 'minimum': 0}, 'max_x': {'type': 'integer', 'minimum': 0},
    'min_y': {'type': 'integer', 'minimum': 0}, 'max_y': {'type': 'integer', 'minimum': 0},
    'targetDirectory': {'type': 'string', 'minLength': 1},
    'includePacked': {'type': 'boolean'},
    'includeCaches': {'type': 'boolean'},
    'includeProxies': {'type': 'boolean'},
}

TESTS = {
    'scene': 'test_design_commands.py', 'object': 'test_design_commands.py',
    'collection': 'test_p1_foundation.py',
    'mesh': 'test_p1_foundation.py',
    'curve': 'test_p1_foundation.py', 'asset': 'test_p1_foundation.py', 'uv':'test_p1_foundation.py',
    'recipe': 'runtime/p1_recipe_smoke.py',
    'rig':'runtime/p2_character_acceptance.py','constraint':'runtime/p2_character_acceptance.py',
    'validation':'runtime/p3_animation_validation_smoke.py',
    'job':'runtime/p3_job_smoke.py',
    'job.estimate': 'test_job_scheduler.py',
    'job.list': 'test_job_scheduler.py',
    'job.events': 'test_job_scheduler.py',
    'geometry_nodes':'runtime/p4_courtyard_acceptance.py',
    'sculpt':'runtime/p5_surface_simulation_acceptance.py','hair':'runtime/p5_surface_simulation_acceptance.py',
    'simulation':'runtime/p5_surface_simulation_acceptance.py',
    'render':'runtime/p6_lookdev_render_acceptance.py','compositor':'runtime/p6_lookdev_render_acceptance.py',
    'grease_pencil':'runtime/p7_gp_sequence_acceptance.py','sequence':'runtime/p7_gp_sequence_acceptance.py',
    'tracking':'runtime/p7_tracking_foreground.py',
    'retopo': 'runtime/retopo_acceptance.py',
    'modifier': 'test_design_commands.py', 'material': 'test_lookdev_commands.py',
    'camera': 'test_lookdev_commands.py', 'light': 'test_lookdev_commands.py',
    'animation': 'test_lookdev_commands.py', 'advanced': 'test_advanced_python.py',
    'official_uploader': 'test_official_uploader.py', 'preview': 'test_milestone.py',
    'export': 'test_exporter.py', 'view': 'test_foreground_controls.py',
    'playback': 'test_foreground_controls.py', 'session': 'test_harness_session.py',
    'capability': 'test_capability_catalog.py',
    'production': 'test_production_profile.py',
}
P1_VERIFIED = {
    'scene.set_units', 'collection.create', 'collection.move_object', 'collection.set_visibility',
    'object.create_mesh', 'object.transform', 'object.rename', 'object.parent', 'object.delete',
    'object.describe', 'object.duplicate', 'object.instance', 'object.set_visibility', 'object.set_display',
    'object.apply_transform', 'object.set_origin', 'object.join', 'object.separate',
    'mesh.inspect', 'mesh.select', 'mesh.edit',
    'modifier.add', 'modifier.list', 'modifier.configure', 'modifier.move', 'modifier.set_enabled',
    'modifier.apply', 'modifier.remove', 'curve.create', 'curve.configure', 'curve.to_mesh',
    'asset.import_file', 'asset.library', 'recipe.hard_surface_shell', 'recipe.spear',
}
P2A_VERIFIED = {'uv.mark_seams','uv.unwrap','uv.pack','uv.inspect','material.create_pbr',
 'material.assign','material.connect_image_texture','material.inspect_nodes','camera.create','camera.aim_at',
 'light.create','light.set_world_color','recipe.desktop_speaker'}
P2B_VERIFIED = {'rig.create_armature','rig.create_control','rig.bind','rig.assign_weights','rig.inspect',
 'constraint.add_bone','constraint.add_object','constraint.keyframe_influence','animation.pose_keyframe',
 'animation.set_frame_range','animation.insert_keyframe','recipe.rigged_spear_character'}
P3_VERIFIED = {'animation.action_list','animation.fcurve_edit','animation.fcurve_clean','animation.nla_add_strip','animation.shape_key_add',
 'animation.shape_key_keyframe','animation.retarget','camera.follow_path','camera.add_handheld','validation.prop_handoff',
 'validation.foot_drift','validation.limb_length','validation.floor_penetration','validation.camera_visibility',
 'validation.motion_discontinuity','job.submit','job.status','job.cancel','job.recover'}
P4_VERIFIED = {'geometry_nodes.create_group','geometry_nodes.add_node','geometry_nodes.connect',
 'geometry_nodes.set_node_input','geometry_nodes.set_modifier_input','geometry_nodes.inspect',
 'recipe.procedural_courtyard','recipe.update_procedural_courtyard'}
P5_VERIFIED = {'sculpt.set_mask','sculpt.displace','sculpt.brush_stroke','sculpt.voxel_remesh','sculpt.multires','sculpt.cleanup',
 'hair.create_curves','hair.inspect','simulation.rigid_body','simulation.collision','simulation.cloth',
 'simulation.soft_body','simulation.quick_smoke','simulation.cache_status','simulation.free_cache'}
P6_VERIFIED = {'material.create_node_group','material.bake','asset.pack_resources','asset.make_paths_relative',
 'render.configure','render.configure_passes','render.create_view_layer','render.inspect','compositor.configure','compositor.inspect','export.extended'}
P7_VERIFIED = {'grease_pencil.create','grease_pencil.add_material','grease_pencil.add_stroke','grease_pencil.inspect',
 'sequence.add','sequence.trim','sequence.move','sequence.transition','sequence.set_volume','sequence.inspect',
 'sequence.configure_output','tracking.load_clip','tracking.add_track','tracking.solve_camera','tracking.setup_scene',
 'tracking.inspect','compositor.add_tracking_mask','rig.rigify_status'}
P8_VERIFIED = {'job.submit','job.resume','sequence.set_speed','sequence.keyframe_volume',
 'sequence.add_compositor_modifier','compositor.add_file_output','compositor.create_strip_group'}
P9_L4_VERIFIED = {'job.resume','rig.rigify_install','rig.rigify_generate'}

# Task 9: surface-motion commands verified by surface_motion_acceptance.py.
# These are new commands with acceptance evidence from the Task 9 acceptance.
SURFACE_MOTION_VERIFIED = {
    'hair.groom', 'hair.validate',
    'simulation.bake', 'simulation.validate',
    'grease_pencil.add_modifier', 'grease_pencil.interpolate',
}

# Task 10: post-production commands verified by postproduction_acceptance.py.
POSTPRODUCTION_VERIFIED = {
    'material.add_node', 'material.connect_nodes',
    'sequence.split', 'sequence.configure_proxy',
    'sequence.add_modifier', 'sequence.color_grade',
    'sequence.set_transform', 'sequence.set_crop',
    'compositor.add_node',
}

# Task 11: project portability commands verified by project_portability_acceptance.py.
PORTABILITY_VERIFIED = {
    'asset.dependencies',
    'asset.validate_portability',
    'asset.package_project',
}

# Task 12: scheduler, estimate, list, events verified by test_job_scheduler.py.
SCHEDULER_VERIFIED = {
    'job.estimate',
    'job.list',
    'job.events',
}

# Lifecycle commands graduated to L3 with runtime acceptance evidence.
LIFECYCLE_VERIFIED = {
    'capability.list', 'capability.describe',
    'session.status', 'session.capabilities', 'session.pause', 'session.resume', 'session.set_progress',
    'scene.inspect',
    'object.create_curve', 'object.create_text',
    'material.attach_image_texture',
    'playback.set_frame',
    'production.status',
}

# Foreground-only lifecycle commands graduated to L3 with evidence from a real
# macOS arm64 foreground session.  The production-profile validator does NOT
# check RuntimeIdentity; the acceptance script and run record
# (docs/verification/foreground-lifecycle-macos-arm64.md) record the scope
# so a reader can see it.  Task 4's coverage matrix is the mechanism for
# other versions/platforms.
LIFECYCLE_FOREGROUND_VERIFIED = frozenset({
    'view.set', 'view.focus', 'view.present',
    'playback.set',
    'preview.capture',
})

UI_COMMANDS = {'view.set', 'view.focus', 'view.present', 'playback.set', 'sculpt.brush_stroke'}
LONG_COMMANDS = {'preview.capture', 'export.file', 'official_uploader.render_and_link'}
NON_SCENE = {'capability', 'session', 'view', 'playback', 'preview', 'export', 'official_uploader'}
NON_SCENE.add('job')

DOMAIN_SKILLS = {
    'scene': ['codex-blender-scene-assembly'],
    'collection': ['codex-blender-scene-assembly'],
    'asset': ['codex-blender-scene-assembly'],
    'object': ['codex-blender-scene-assembly'],
    'mesh': ['codex-blender-hard-surface'],
    'modifier': ['codex-blender-hard-surface'],
    'curve': ['codex-blender-curves'],
    'uv': ['codex-blender-uv-material'],
    'material': ['codex-blender-uv-material'],
    'rig': ['codex-blender-character-rigging'],
    'constraint': ['codex-blender-character-rigging'],
    'animation': ['codex-blender-character-animation'],
    'camera': ['codex-blender-cinematography'],
    'light': ['codex-blender-render-compositing'],
    'geometry_nodes': ['codex-blender-procedural-modeling'],
    'sculpt': ['codex-blender-sculpt-surface'],
    'hair': ['codex-blender-hair'],
    'simulation': ['codex-blender-simulation'],
    'render': ['codex-blender-render-compositing'],
    'compositor': ['codex-blender-render-compositing'],
    'grease_pencil': ['codex-blender-grease-pencil'],
    'tracking': ['codex-blender-tracking'],
    'sequence': ['codex-blender-sequence-editing'],
    'validation': ['codex-blender-quality-validation'],
    'job': ['codex-blender-background-jobs'],
    'preview': ['codex-blender-preview'],
    'export': ['codex-blender-export'],
    'official_uploader': ['codex-blender-jimeng-web'],
    'advanced': ['codex-blender-use'],
    'capability': ['codex-blender-use'],
    'session': ['codex-blender-use'],
    'view': ['codex-blender-use'],
    'playback': ['codex-blender-use'],
    'retopo': ['codex-blender-retopology'],
}

COMMAND_SKILLS = {
    'scene.inspect': ['codex-blender-inspect'],
    'object.describe': ['codex-blender-inspect', 'codex-blender-scene-assembly'],
    'object.create_mesh': ['codex-blender-hard-surface'],
    'object.create_curve': ['codex-blender-curves'],
    'object.join': ['codex-blender-hard-surface'],
    'object.separate': ['codex-blender-hard-surface'],
    'object.apply_transform': ['codex-blender-hard-surface'],
    'object.set_origin': ['codex-blender-hard-surface'],
    'asset.pack_resources': ['codex-blender-render-compositing'],
    'asset.make_paths_relative': ['codex-blender-render-compositing'],
    'asset.dependencies': ['codex-blender-scene-assembly'],
    'asset.validate_portability': ['codex-blender-scene-assembly'],
    'asset.package_project': ['codex-blender-scene-assembly', 'codex-blender-export'],
    'export.extended': ['codex-blender-export', 'codex-blender-render-compositing'],
    'validation.camera_visibility': ['codex-blender-quality-validation', 'codex-blender-cinematography'],
    'validation.floor_penetration': ['codex-blender-quality-validation', 'codex-blender-character-animation'],
    'validation.foot_drift': ['codex-blender-quality-validation', 'codex-blender-character-animation'],
    'validation.limb_length': ['codex-blender-quality-validation', 'codex-blender-character-animation'],
    'validation.motion_discontinuity': ['codex-blender-quality-validation', 'codex-blender-character-animation'],
    'validation.prop_handoff': ['codex-blender-quality-validation', 'codex-blender-character-animation'],
}


def command_skills(name, domain, metadata):
    explicit = (metadata or {}).get('skills')
    if explicit:
        return list(explicit)
    return list(COMMAND_SKILLS.get(name, DOMAIN_SKILLS.get(domain, ['codex-blender-design'])))


def runtime_evidence(name):
    if name in LIFECYCLE_FOREGROUND_VERIFIED:
        return ['tests/runtime/foreground_lifecycle_acceptance.py']
    if name in LIFECYCLE_VERIFIED:
        return ['tests/runtime/lifecycle_commands_acceptance.py']
    if name in {'rig.rigify_install','rig.rigify_generate'}:
        return ['tests/runtime/p9_rigify_install_acceptance.py']
    if name == 'job.submit':
        return ['tests/runtime/p3_job_smoke.py','tests/runtime/p3_foreground_job_bootstrap.py',
                'tests/runtime/p8_frame_pipeline_acceptance.py']
    if name == 'job.resume':
        return ['tests/runtime/p8_frame_pipeline_acceptance.py']
    if name in SCHEDULER_VERIFIED:
        return ['tests/test_job_scheduler.py']
    if name in {'sequence.set_speed','sequence.keyframe_volume'}:
        return ['tests/runtime/p8_vse_extended_acceptance.py']
    if name in {'sequence.add_compositor_modifier','compositor.add_file_output','compositor.create_strip_group'}:
        return ['tests/runtime/p8_compositor_delivery_acceptance.py']
    if name == 'rig.rigify_status':
        return ['tests/runtime/p7_extension_status.py']
    if name.startswith('tracking.'):
        return ['tests/runtime/p7_tracking_foreground.py']
    if name == 'compositor.add_tracking_mask':
        return ['tests/runtime/p7_compositor_tracking_acceptance.py']
    if name in {'hair.groom','hair.validate','simulation.bake','simulation.validate',
                'grease_pencil.add_modifier','grease_pencil.interpolate'}:
        return ['tests/runtime/surface_motion_acceptance.py']
    if name in POSTPRODUCTION_VERIFIED:
        return ['tests/runtime/postproduction_acceptance.py']
    if name in PORTABILITY_VERIFIED:
        return ['tests/runtime/project_portability_acceptance.py']
    if name in P7_VERIFIED:
        return ['tests/runtime/p7_gp_sequence_acceptance.py']
    if name in P6_VERIFIED:
        return ['tests/runtime/p6_lookdev_render_acceptance.py']
    if name == 'sculpt.brush_stroke':
        return ['tests/runtime/p5_sculpt_foreground.py']
    if name in P5_VERIFIED:
        return ['tests/runtime/p5_surface_simulation_acceptance.py']
    if name in P4_VERIFIED:
        return ['tests/runtime/p4_courtyard_acceptance.py']
    if name.startswith('job.'):
        return ['tests/runtime/p3_job_smoke.py', 'tests/runtime/p3_foreground_job_bootstrap.py']
    if name in P3_VERIFIED:
        return ['tests/runtime/p3_animation_validation_smoke.py', 'tests/runtime/p3_reopen_validate.py']
    if name in P2B_VERIFIED:
        return ['tests/runtime/p2_character_acceptance.py']
    if name in P2A_VERIFIED:
        return ['tests/runtime/p2_product_acceptance.py']
    if name.startswith('mesh.'):
        return ['tests/runtime/p1_mesh_smoke.py']
    if name.startswith('modifier.'):
        return ['tests/runtime/p1_modifier_smoke.py']
    if name.startswith(('curve.', 'asset.')):
        return ['tests/runtime/p1_curve_asset_smoke.py']
    if name.startswith('recipe.'):
        return ['tests/runtime/p1_recipe_smoke.py', 'tests/runtime/p1_delivery_acceptance.py']
    return ['tests/runtime/p1_foundation_smoke.py', 'tests/runtime/p1_delivery_acceptance.py']


def skill_coverage_role(name, domain, skills):
    if domain == 'recipe' or len(skills) > 1:
        return 'composite-workflow'
    if name == 'scene.inspect':
        return 'lifecycle-inspection'
    if domain in {'session', 'capability', 'view', 'playback'}:
        return 'lifecycle-routing'
    if domain == 'job':
        return 'background-workflow'
    if domain == 'advanced':
        return 'gated-expert-entry'
    return 'domain-workflow'

MODIFIER_SETTINGS_SCHEMA={'type':'object','oneOf':[
 {'title':'Mirror','properties':{'use_axis':{'type':'array','items':{'type':'boolean'},'minItems':3,'maxItems':3},'use_clip':{'type':'boolean'},'merge_threshold':{'type':'number','minimum':0}}},
 {'title':'Array','properties':{'count':{'type':'integer','minimum':1},'use_relative_offset':{'type':'boolean'},'relative_offset_displace':VECTOR,'use_constant_offset':{'type':'boolean'},'constant_offset_displace':VECTOR}},
 {'title':'Bevel','properties':{'width':{'type':'number','minimum':0},'segments':{'type':'integer','minimum':1},'limit_method':{'type':'string'}}},
 {'title':'Subdivision','properties':{'levels':{'type':'integer','minimum':0},'render_levels':{'type':'integer','minimum':0},'subdivision_type':{'type':'string'}}},
 {'title':'Solidify','properties':{'thickness':{'type':'number'},'offset':{'type':'number'},'use_even_offset':{'type':'boolean'}}},
 {'title':'Boolean','properties':{'operation':{'type':'string'},'solver':{'type':'string'},'object':{'type':['string','object']}}},
 {'title':'Decimate','properties':{'ratio':{'type':'number','minimum':0,'maximum':1},'decimate_type':{'type':'string'},'angle_limit':{'type':'number','minimum':0}}},
]}
EXPORT_PARAMETERS_SCHEMA={'type':'object','description':'Allowed keys depend on path extension',
 'properties':{'use_selection':{'type':'boolean'},'use_visible':{'type':'boolean'},'use_renderable':{'type':'boolean'},
 'export_apply':{'type':'boolean'},'export_animations':{'type':'boolean'},'export_materials':{},'bake_anim':{'type':'boolean'},
 'export_selected_objects':{'type':'boolean'},'apply_modifiers':{'type':'boolean'},'export_uv':{'type':'boolean'},
 'global_scale':{'type':'number'},'frameStart':{'type':'integer'},'frameEnd':{'type':'integer'}},'additionalProperties':False}


class RuntimeCommandRegistry(CommandRegistry):
    """Enrich each registration once; retain CommandRegistry as the query authority."""
    def __init__(self, bpy_module, *, output_root=None, asset_roots=()):
        super().__init__()
        self.bpy = bpy_module
        self.output_root = output_root
        self.asset_roots = tuple(asset_roots)

    def register(self, name, handler, *, validate=None, risk='standard', metadata=None, availability=None):
        domain = name.split('.')[0]
        if validate is None and name.startswith('session.'):
            validate = (closed_arguments(required=('stage',), optional=('progress',))
                        if name == 'session.set_progress' else closed_arguments())
        if validate is not None and hasattr(validate, 'schema'):
            validate.schema = deepcopy(validate.schema)
            for field in validate.schema['properties']:
                validate.schema['properties'][field] = deepcopy(FIELDS.get(field, {
                    'description': 'See command validation; detailed type not yet audited'}))
            if name in {'modifier.add','modifier.configure'} and 'settings' in validate.schema['properties']:
                validate.schema['properties']['settings']=deepcopy(MODIFIER_SETTINGS_SCHEMA)
            if name=='export.file' and 'parameters' in validate.schema['properties']:
                validate.schema['properties']['parameters']=deepcopy(EXPORT_PARAMETERS_SCHEMA)
            if name=='compositor.add_file_output':
                validate.schema['properties']['format']={'type':'string','enum':['PNG','OPEN_EXR_MULTILAYER']}
                validate.schema['properties']['colorDepth']={'type':'string','enum':['8','16','32']}
            if name=='sequence.set_speed':
                validate.schema['properties']['source']={'type':'string','minLength':1}
            if name=='simulation.bake':
                validate.schema['properties']['bakeType']={'type':'string','enum':['CLOTH','SOFT_BODY','FLUID','DYNAMIC_PAINT','RIGID_BODY','PARTICLE']}
            if name=='hair.groom':
                validate.schema['properties']['operation']={'type':'string','enum':['COMB','CUT','LENGTH','CLUMP','NOISE','SMOOTH']}
            if name=='sequence.add':
                validate.schema['properties']['type']={'type':'string','enum':['MOVIE','SOUND','IMAGE','IMAGE_SEQUENCE','SCENE','TEXT']}
            if name=='sequence.add_modifier':
                validate.schema['properties']['modifierType']={'type':'string','enum':[
                    'Color Balance','Brightness/Contrast','Hue Correct','Mask',
                    'White Balance','Tonemap','Curves',
                    'BRIGHT_CONTRAST','COLOR_BALANCE','COMPOSITOR','CURVES',
                    'HUE_CORRECT','MASK','TONEMAP','WHITE_BALANCE']}
            if name=='material.add_node':
                validate.schema['properties']['nodeType']={'type':'string','enum':[
                    'Principled','Image Texture','Normal Map','Mapping','Math','Mix','ColorRamp']}
            if name=='compositor.add_node':
                validate.schema['properties']['nodeType']={'type':'string','enum':[
                    'Render Layers','File Output','Cryptomatte','Keying','Mask']}
        module = getattr(handler, '__module__', '')
        source = module.replace('.', '/') + '.py' if module.startswith('scripts.') else None
        requirements = ['Per-request argument checks and session policy still apply']
        if name in UI_COMMANDS:
            requirements.append('Foreground window with a VIEW_3D area')
        if name in {'preview.capture', 'export.file'}:
            requirements.append('Approved output root; export additionally requires a committed snapshot')
        if name == 'material.attach_image_texture':
            requirements.append('Approved asset root and an existing image file')
        if domain == 'official_uploader':
            requirements.append('Enabled compatible official uploader; use official_uploader.inspect')
        skills = command_skills(name, domain, metadata)
        defaults = {
            'domain': domain, 'maturity': 'L1', 'implementationSource': source,
            'context': {'objectTypes': [], 'modes': [], 'requirements': requirements},
            'effects': {'sceneMutation': (domain not in NON_SCENE and name != 'scene.inspect')
                                        or name == 'official_uploader.render_and_link',
                        'longRunning': name in LONG_COMMANDS or domain == 'advanced' or name in {'job.submit','job.resume'},
                        'cancellable': name in {'job.submit','job.resume'}},
            'skills': skills, 'skillCoverage': skill_coverage_role(name, domain, skills),
            'tests': ['tests/' + TESTS[domain]] if domain in TESTS else [],
            'testCoverage': 'Related regression suite; not proof that every parameter is exercised',
            'versions': {'running': getattr(getattr(self.bpy, 'app', None), 'version_string', None),
                         'verified': [], 'extensions': []},
            'limitations': ['Input types document intended use; legacy coercions remain in handlers.',
                            'Probe does not validate a particular object, path, authorization or artistic outcome.'],
        }
        context_types=[]
        if domain in {'mesh','uv','sculpt','retopo'}:context_types=['MESH']
        elif domain=='rig':context_types=['ARMATURE','MESH','EMPTY']
        elif domain=='constraint':context_types=['ARMATURE','MESH']
        elif domain=='curve':context_types=['CURVE']
        elif domain=='grease_pencil':context_types=['GREASEPENCIL']
        elif domain=='hair':context_types=['CURVES','MESH']
        defaults['context']={'objectTypes':context_types,'modes':['OBJECT'] if context_types else [],'requirements':requirements}
        if name.startswith('rig.rigify_'):defaults['versions']['extensions']=['Rigify (bundled enable preferred; official download requires explicit authorization)']
        if name == 'job.submit':
            defaults['skillRouting'] = {'byArguments': {'kind': {
                'EXPORT': ['codex-blender-render-compositing'],
                'RENDER_STILL': ['codex-blender-render-compositing'],
                'BAKE_POINT_CACHES': ['codex-blender-simulation'],
                'RENDER_ANIMATION_FRAMES': ['codex-blender-render-compositing','codex-blender-background-jobs'],
                'COMPOSE_VIDEO': ['codex-blender-sequence-editing','codex-blender-background-jobs'],
            }}}
        defaults.update(metadata or {})
        if name in LIFECYCLE_VERIFIED:
            # Evidence gathered on Blender 5.2.1 / darwin / arm64 / managed.
            # The production-profile validator does NOT check RuntimeIdentity;
            # the acceptance script records the identity in its output artifact
            # (lifecycle_acceptance.json) so a reader can see the scope.
            # Task 4's coverage matrix is the mechanism for other versions/platforms.
            defaults['maturity'] = 'L3'
            defaults['verification'] = {
                'runtime': runtime_evidence(name),
                'visual': ['docs/verification/capability-catalog-baseline.md'],
                'delivery': ['tests/runtime/lifecycle_commands_acceptance.py'],
                'recoveryAndCompatibility': [],
            }
        elif name in LIFECYCLE_FOREGROUND_VERIFIED:
            # Evidence gathered on Blender 5.2.1 / darwin / arm64 / managed
            # foreground session.  See docs/verification/foreground-lifecycle-macos-arm64.md
            # for the full run record and milestone PNG sha256 checksums.
            defaults['maturity'] = 'L3'
            defaults['verification'] = {
                'runtime': runtime_evidence(name),
                'visual': ['docs/verification/foreground-lifecycle-macos-arm64.md'],
                'delivery': ['tests/runtime/foreground_lifecycle_acceptance.py'],
                'recoveryAndCompatibility': [],
            }
        elif name in P1_VERIFIED or name in P2A_VERIFIED or name in P2B_VERIFIED or name in P3_VERIFIED or name in P4_VERIFIED or name in P5_VERIFIED or name in P6_VERIFIED or name in P7_VERIFIED or name in P8_VERIFIED or name in SURFACE_MOTION_VERIFIED or name in POSTPRODUCTION_VERIFIED or name in PORTABILITY_VERIFIED or name in SCHEDULER_VERIFIED:
            defaults['maturity'] = 'L3'
            defaults['verification'] = {
                'runtime': runtime_evidence(name),
                'visual': ['docs/verification/p8-video-pipeline-acceptance.md' if name in P8_VERIFIED else
                           'docs/verification/p7-editors-tracking-acceptance.md' if name in P7_VERIFIED else
                           'docs/verification/p6-lookdev-render-acceptance.md' if name in P6_VERIFIED else
                           'docs/verification/p5-surface-simulation-acceptance.md' if name in P5_VERIFIED else
                           'docs/verification/p4-procedural-courtyard-acceptance.md' if name in P4_VERIFIED else
                           'docs/verification/p3-animation-jobs-acceptance.md' if name in P3_VERIFIED else
                           'docs/verification/p2-character-acceptance.md' if name in P2B_VERIFIED else
                           'docs/verification/p2-product-acceptance.md' if name in P2A_VERIFIED else
                           'docs/verification/p5-surface-simulation-acceptance.md' if name in SURFACE_MOTION_VERIFIED else
                           'docs/verification/postproduction-acceptance.md' if name in POSTPRODUCTION_VERIFIED else
                           'docs/verification/project-portability-acceptance.md' if name in PORTABILITY_VERIFIED else
                           'docs/verification/scheduler-policy.md' if name in SCHEDULER_VERIFIED else
                           'docs/verification/blender-domain-coverage-matrix.md#sceneobjectcollection'],
                'delivery': [('tests/test_job_scheduler.py' if name in SCHEDULER_VERIFIED else
                             'tests/runtime/p8_frame_pipeline_acceptance.py' if name.startswith('job.') else
                              'tests/runtime/p8_vse_extended_acceptance.py' if name in {'sequence.set_speed','sequence.keyframe_volume'} else
                              'tests/runtime/p8_compositor_delivery_acceptance.py') if name in P8_VERIFIED else
                             'tests/runtime/p7_extension_status.py' if name=='rig.rigify_status' else
                             'tests/runtime/p7_tracking_foreground.py' if name.startswith('tracking.') else
                             'tests/runtime/p7_compositor_tracking_acceptance.py' if name=='compositor.add_tracking_mask' else
                             'tests/runtime/p7_gp_sequence_acceptance.py' if name in P7_VERIFIED else
                             'tests/runtime/p6_lookdev_render_acceptance.py' if name in P6_VERIFIED else
                             'tests/runtime/p5_surface_simulation_acceptance.py' if name in P5_VERIFIED else
                             'tests/runtime/p4_courtyard_acceptance.py' if name in P4_VERIFIED else
                             'tests/runtime/p3_job_smoke.py' if name.startswith('job.') else
                             'tests/runtime/p3_animation_validation_smoke.py' if name in P3_VERIFIED else
                             'tests/runtime/p2_character_acceptance.py' if name in P2B_VERIFIED else
                             'tests/runtime/p2_product_acceptance.py' if name in P2A_VERIFIED else
                             'tests/runtime/surface_motion_acceptance.py' if name in SURFACE_MOTION_VERIFIED else
                             'tests/runtime/postproduction_acceptance.py' if name in POSTPRODUCTION_VERIFIED else
                             'tests/runtime/project_portability_acceptance.py' if name in PORTABILITY_VERIFIED else
                             'tests/runtime/p1_delivery_acceptance.py'],
                'recoveryAndCompatibility': [],
            }
        if name in P9_L4_VERIFIED:
            defaults['maturity']='L4'
            defaults['verification']={
                'runtime':runtime_evidence(name),
                'visual':['docs/verification/windows-l4-rigify.md'],
                'delivery':['.github/workflows/windows-l4.yml',
                            'tests/runtime/p8_frame_pipeline_acceptance.py' if name=='job.resume'
                            else 'tests/runtime/p9_rigify_install_acceptance.py'],
                'recoveryAndCompatibility':['docs/verification/windows-l4-rigify.md',
                                            '.github/workflows/windows-l4.yml'],
            }
        super().register(name, handler, validate=validate, risk=risk, metadata=defaults,
                         availability=availability or (lambda: self._probe(name)))

    def _probe(self, name):
        if name.startswith('job.') and self.output_root is None:
            return {'status':'unavailable','reason':'No approved output root'}
        if name in {'preview.capture', 'export.file'} and self.output_root is None:
            return {'status': 'unavailable', 'reason': 'No approved output root'}
        if name == 'material.attach_image_texture' and not self.asset_roots:
            return {'status': 'unavailable', 'reason': 'No approved asset roots'}
        if name in UI_COMMANDS:
            if getattr(getattr(self.bpy, 'app', None), 'background', False):
                return {'status': 'unavailable', 'reason': 'Blender is running in background mode'}
            manager = getattr(self.bpy.context, 'window_manager', None)
            windows = getattr(manager, 'windows', ())
            if not any(area.type == 'VIEW_3D' for window in windows for area in window.screen.areas):
                return {'status': 'unavailable', 'reason': 'No VIEW_3D window available'}
        if name in {'tracking.solve_camera','tracking.setup_scene'}:
            if getattr(getattr(self.bpy,'app',None),'background',False):return {'status':'unavailable','reason':'Foreground CLIP_EDITOR required'}
        if name=='rig.rigify_generate' and self.bpy.context.preferences.addons.get('rigify') is None:
            return {'status':'unavailable','reason':'Rigify is not enabled; run authorized rig.rigify_install'}
        if name.startswith('official_uploader.'):
            return {'status': 'unknown', 'reason': 'Run official_uploader.inspect to verify the optional adapter'}
        if name in {'scene.inspect', 'session.status', 'session.capabilities'}:
            return {'status': 'available', 'reason': None}
        return {'status': 'unknown', 'reason': 'Basic environment checked; target arguments and session policy still require validation'}


# ---------------------------------------------------------------------------
# Generated coverage summaries (1.0 production baseline)
#
# The documented command/Skill counts are generated from the registry, never
# hand-maintained: the 0.3.x docs carried a single merged figure that matched
# neither runtime mode and drifted unnoticed. Managed and Connector are counted
# separately on purpose -- a combined total is forbidden by the 1.0 spec.
# ---------------------------------------------------------------------------

SUPPORTED_RUNTIME_MODES = ('managed', 'connector')
_MATURITY_GRADES = ('L1', 'L2', 'L3', 'L4')
_COUNT_PAGE_LIMIT = 100


def _registration_only_bpy():
    """A stub sufficient to *register* commands for counting.

    A coverage count describes the catalog, not a live Blender. Registration
    only needs the attributes handlers close over, so no scene is involved and
    availability probes are never run.
    """
    import os
    import types

    module = types.ModuleType('bpy')
    module.app = types.SimpleNamespace(
        version_string='0.0.0', version=(0, 0, 0), version_file=(0, 0, 0), background=True)
    module.path = types.SimpleNamespace(abspath=lambda value: os.path.abspath(str(value)))
    module.context = types.SimpleNamespace(scene=None, preferences=None)
    module.data = types.SimpleNamespace(objects=[], materials=[], scenes=[])
    module.ops = types.SimpleNamespace()
    return module


def generate_coverage_summary(runtime_mode):
    """Count the registered capability surface for one runtime mode.

    Returns a dict with the command total and per-maturity counts, the domain
    names, the Skill counts (on disk vs referenced by the catalog), and the
    command ids (so a caller can diff the two modes).
    """
    if runtime_mode not in SUPPORTED_RUNTIME_MODES:
        raise HarnessError(
            'INVALID_ARGUMENT',
            'runtime_mode must be one of {0}'.format(', '.join(SUPPORTED_RUNTIME_MODES)),
        )
    # Imported lazily: runtime.py imports this module at import time.
    from .runtime import build_registry

    registry = build_registry(_registration_only_bpy(), runtime_mode=runtime_mode)

    commands = {grade: 0 for grade in _MATURITY_GRADES}
    domain_names = set()
    referenced_skills = set()
    command_ids = []
    offset = 0
    while True:
        page = registry.list_capabilities({'offset': offset, 'limit': _COUNT_PAGE_LIMIT})
        batch = page.get('items', [])
        if not batch:
            break
        for item in batch:
            command_ids.append(item['id'])
            grade = item.get('maturity', 'L1')
            commands[grade] = commands.get(grade, 0) + 1
            if item.get('domain'):
                domain_names.add(item['domain'])
            for skill in item.get('skills') or ():
                referenced_skills.add(skill)
        offset = page.get('nextOffset')
        if offset is None:
            break

    skills_dir = Path(__file__).resolve().parents[2] / 'skills'
    on_disk = sorted(entry.name for entry in skills_dir.iterdir() if entry.is_dir()) \
        if skills_dir.is_dir() else []

    return {
        'runtimeMode': runtime_mode,
        'commands': dict(
            {'total': len(command_ids)},
            **{grade: commands.get(grade, 0) for grade in _MATURITY_GRADES}
        ),
        'domains': {'total': len(domain_names), 'names': sorted(domain_names)},
        'skills': {
            'onDisk': len(on_disk),
            'referenced': len(referenced_skills),
            'referencedNames': sorted(referenced_skills),
        },
        'commandIds': sorted(command_ids),
    }


def generate_coverage_summaries():
    """Both runtime modes plus their difference.

    The difference is reported explicitly because the Connector adds the
    optional official uploader surface; folding it into a single number would
    hide exactly the distinction the 1.0 spec requires.
    """
    managed = generate_coverage_summary('managed')
    connector = generate_coverage_summary('connector')
    managed_ids = set(managed['commandIds'])
    connector_ids = set(connector['commandIds'])
    return {
        'generatedFrom': 'scripts/harness/runtime_catalog.py',
        'managed': managed,
        'connector': connector,
        'modeDifference': {
            'onlyManaged': sorted(managed_ids - connector_ids),
            'onlyConnector': sorted(connector_ids - managed_ids),
        },
    }


def write_coverage_counts(target: Path | str) -> None:
    """Write capability-counts.json with a trailing newline."""
    import json
    target = Path(target)
    target.write_text(json.dumps(generate_coverage_summaries(), indent=2) + '\n',
                      encoding='utf-8')
