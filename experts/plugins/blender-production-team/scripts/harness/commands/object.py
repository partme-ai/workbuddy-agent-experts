"""Object creation, transform, hierarchy, deletion, and modifier commands."""

from __future__ import annotations

from .validation import require_name, vector3, finite_number
from ..errors import HarnessError
from ..identity import ObjectResolver
from ..operation_context import OperationContext


PRIMITIVE_OPERATORS = {
    "cube": "primitive_cube_add",
    "sphere": "primitive_uv_sphere_add",
    "cylinder": "primitive_cylinder_add",
    "cone": "primitive_cone_add",
    "plane": "primitive_plane_add",
    "torus": "primitive_torus_add",
}


class ObjectCommands:
    def __init__(self, bpy_module):
        self.bpy = bpy_module
        self.resolver = ObjectResolver(bpy_module)
        self.operation_context = OperationContext(bpy_module)

    def _object(self, name: str):
        obj = self.bpy.data.objects.get(name)
        if obj is None:
            raise HarnessError("OBJECT_NOT_FOUND", f"object not found: {name}")
        return obj

    def create_mesh(self, arguments: dict) -> dict:
        name = require_name(arguments.get("name"))
        primitive = str(arguments.get("primitive", "")).lower()
        operator_name = PRIMITIVE_OPERATORS.get(primitive)
        if operator_name is None:
            raise HarnessError("INVALID_ARGUMENT", f"unsupported primitive: {primitive}")
        if self.bpy.data.objects.get(name) is not None:
            raise HarnessError("NAME_COLLISION", f"object already exists: {name}")
        transforms = {field: vector3(arguments[field], field)
                      for field in ('location', 'rotation', 'scale') if field in arguments}
        getattr(self.bpy.ops.mesh, operator_name)()
        obj = self.bpy.context.object
        old_name = obj.name
        obj.name = name
        if isinstance(self.bpy.data.objects, dict) and old_name in self.bpy.data.objects:
            self.bpy.data.objects.pop(old_name)
            self.bpy.data.objects[name] = obj
        for field, attr, fallback in (
            ("location", "location", [0, 0, 0]),
            ("rotation", "rotation_euler", [0, 0, 0]),
            ("scale", "scale", [1, 1, 1]),
        ):
            if field in arguments:
                setattr(obj, attr, transforms[field])
        return {"changedObjects": [name], "result": self.resolver.receipt(obj)}

    def create_curve(self, arguments: dict) -> dict:
        name = require_name(arguments.get("name"))
        depth = finite_number(arguments.get('bevelDepth', 0), 'bevelDepth', minimum=0)
        if self.bpy.data.objects.get(name) is not None:
            raise HarnessError("NAME_COLLISION", f"object already exists: {name}")
        self.bpy.ops.curve.primitive_bezier_curve_add()
        curve = self._rename_active(name)
        if "bevelDepth" in arguments:
            curve.data.bevel_depth = depth
        return {"changedObjects": [name], "result": self.resolver.receipt(curve)}

    def create_text(self, arguments: dict) -> dict:
        name = require_name(arguments.get("name"))
        text = str(arguments.get("text", ""))
        size = finite_number(arguments.get('size', 1), 'size', positive=True)
        extrude = finite_number(arguments.get('extrude', 0), 'extrude', minimum=0)
        if self.bpy.data.objects.get(name) is not None:
            raise HarnessError("NAME_COLLISION", f"object already exists: {name}")
        self.bpy.ops.object.text_add()
        obj = self._rename_active(name)
        obj.data.body = text
        if "size" in arguments:
            obj.data.size = size
        if "extrude" in arguments:
            obj.data.extrude = extrude
        return {"changedObjects": [name], "result": self.resolver.receipt(obj)}

    def _rename_active(self, name: str):
        obj = self.bpy.context.object
        old_name = obj.name
        obj.name = name
        if isinstance(self.bpy.data.objects, dict):
            self.bpy.data.objects.pop(old_name)
            self.bpy.data.objects[name] = obj
        return obj

    def transform(self, arguments: dict) -> dict:
        obj = self.resolver.resolve(arguments)
        name = obj.name
        transforms = {field: vector3(arguments[field], field)
                      for field in ('location', 'rotation', 'scale') if field in arguments}
        space = str(arguments.get('space', 'LOCAL')).upper()
        if space not in {'LOCAL', 'WORLD'}: raise HarnessError('INVALID_ARGUMENT', 'space must be LOCAL or WORLD')
        if not transforms: raise HarnessError("INVALID_ARGUMENT", "transform requires location, rotation, or scale")
        if space == 'WORLD':
            from mathutils import Euler, Matrix, Vector
            location, rotation, scale = obj.matrix_world.decompose()
            location = Vector(transforms.get('location', location))
            rotation = Euler(transforms['rotation']).to_quaternion() if 'rotation' in transforms else rotation
            scale = Vector(transforms.get('scale', scale))
            obj.matrix_world = Matrix.LocRotScale(location, rotation, scale)
            return {'changedObjects': [name], 'result': self.resolver.receipt(obj)}
        changed = False
        for field, attr in (("location", "location"), ("rotation", "rotation_euler"), ("scale", "scale")):
            if field in arguments:
                setattr(obj, attr, transforms[field])
                changed = True
        return {"changedObjects": [name], 'result': self.resolver.receipt(obj)}

    def rename(self, arguments: dict) -> dict:
        obj = self.resolver.resolve(arguments)
        name = obj.name
        new_name = require_name(arguments.get("newName"))
        if self.bpy.data.objects.get(new_name) is not None:
            raise HarnessError("NAME_COLLISION", f"object already exists: {new_name}")
        obj.name = new_name
        if isinstance(self.bpy.data.objects, dict):
            self.bpy.data.objects.pop(name)
            self.bpy.data.objects[new_name] = obj
        return {"changedObjects": [new_name]}

    def delete(self, arguments: dict) -> dict:
        obj = self.resolver.resolve(arguments)
        name = obj.name
        self.bpy.data.objects.remove(obj, do_unlink=True)
        return {"changedObjects": [name]}

    def parent(self, arguments: dict) -> dict:
        child = self.resolver.resolve({'name':arguments.get('child'), 'objectId':arguments.get('childObjectId')})
        parent = self.resolver.resolve({'name':arguments.get('parent'), 'objectId':arguments.get('parentObjectId')})
        child_name, parent_name = child.name, parent.name
        ancestor = parent
        visited = set()
        while ancestor is not None:
            if ancestor is child or id(ancestor) in visited:
                raise HarnessError('INVALID_ARGUMENT', 'parent hierarchy must not contain a cycle')
            visited.add(id(ancestor))
            ancestor = ancestor.parent
        keep_world = arguments.get('keepWorld', False)
        if type(keep_world) is not bool: raise HarnessError('INVALID_ARGUMENT', 'keepWorld must be boolean')
        world = child.matrix_world.copy() if keep_world and hasattr(child, 'matrix_world') else None
        child.parent = parent
        if world is not None: child.matrix_world = world
        return {"changedObjects": [child_name]}

    def add_modifier(self, arguments: dict) -> dict:
        name = require_name(arguments.get("name"))
        modifier_type = str(arguments.get("modifier", "")).upper()
        if not modifier_type:
            raise HarnessError("INVALID_ARGUMENT", "modifier is required")
        settings = arguments.get('settings', {})
        if not isinstance(settings, dict) or any(not isinstance(key, str) or key.startswith('_') for key in settings):
            raise HarnessError('INVALID_ARGUMENT', 'settings must be an object with public property names')
        obj = self._object(name)
        modifier = None
        try:
            modifier = obj.modifiers.new(name=f"Codex {modifier_type.title()}", type=modifier_type)
            for key, value in settings.items():
                if not hasattr(modifier, key):
                    raise HarnessError("INVALID_ARGUMENT", f"unsupported modifier setting: {key}")
                setattr(modifier, key, value)
        except Exception as exc:
            if modifier is not None:
                obj.modifiers.remove(modifier)
            if isinstance(exc, HarnessError):
                raise
            raise HarnessError('INVALID_ARGUMENT', 'modifier type or settings are not supported') from exc
        return {"changedObjects": [name], "result": {"modifier": modifier.name}}

    def describe(self, arguments):
        obj = self.resolver.resolve(arguments)
        parent = self.resolver.receipt(obj.parent) if obj.parent else None
        collections = sorted(collection.name for collection in getattr(obj, 'users_collection', ()))
        return {'changedObjects': [], 'result': self.resolver.receipt(obj) | {
            'location': list(obj.location), 'rotation': list(obj.rotation_euler), 'scale': list(obj.scale),
            'visibleViewport': not bool(getattr(obj, 'hide_viewport', False)),
            'visibleRender': not bool(getattr(obj, 'hide_render', False)),
            'parent': parent, 'collections': collections}}

    def duplicate(self, arguments, *, linked=False):
        source = self.resolver.resolve(arguments)
        name = require_name(arguments.get('newName'))
        if self.bpy.data.objects.get(name):
            raise HarnessError('NAME_COLLISION', f'object already exists: {name}')
        duplicate = source.copy()
        self.resolver.assign_new_id(duplicate)
        if not linked and getattr(source, 'data', None) is not None:
            duplicate.data = source.data.copy()
        duplicate.name = name
        target = source.users_collection[0] if source.users_collection else self.bpy.context.scene.collection
        target.objects.link(duplicate)
        return {'changedObjects': [name], 'result': self.resolver.receipt(duplicate) | {'linkedData': linked}}

    def instance(self, arguments):
        return self.duplicate(arguments, linked=True)

    def set_visibility(self, arguments):
        obj = self.resolver.resolve(arguments)
        viewport, render = arguments.get('viewport'), arguments.get('render')
        if viewport is None and render is None:
            raise HarnessError('INVALID_ARGUMENT', 'viewport or render visibility is required')
        if viewport is not None and type(viewport) is not bool:
            raise HarnessError('INVALID_ARGUMENT', 'viewport must be boolean')
        if render is not None and type(render) is not bool:
            raise HarnessError('INVALID_ARGUMENT', 'render must be boolean')
        if viewport is not None:
            obj.hide_viewport = not viewport
        if render is not None:
            obj.hide_render = not render
        return {'changedObjects': [obj.name], 'result': self.resolver.receipt(obj)}

    def set_display(self, arguments):
        obj = self.resolver.resolve(arguments)
        display = str(arguments.get('displayType', '')).upper()
        if display not in {'BOUNDS', 'WIRE', 'SOLID', 'TEXTURED'}:
            raise HarnessError('INVALID_ARGUMENT', 'displayType must be BOUNDS, WIRE, SOLID or TEXTURED')
        in_front = arguments.get('showInFront', False)
        if type(in_front) is not bool: raise HarnessError('INVALID_ARGUMENT', 'showInFront must be boolean')
        obj.display_type = display; obj.show_in_front = in_front
        return {'changedObjects':[obj.name],'result':self.resolver.receipt(obj) | {
            'displayType':display,'showInFront':in_front}}

    def apply_transform(self, arguments):
        obj = self.resolver.resolve(arguments)
        flags = {key: arguments.get(key, False) for key in ('location', 'rotation', 'scale')}
        if not any(flags.values()) or any(type(value) is not bool for value in flags.values()):
            raise HarnessError('INVALID_ARGUMENT', 'one or more boolean transform flags are required')
        try:
            with self.operation_context.active_object(obj):
                result = self.bpy.ops.object.transform_apply(**flags)
                if result != {'FINISHED'}:
                    raise HarnessError('OPERATION_FAILED', 'Blender did not apply the transform')
        except HarnessError:
            raise
        except Exception as exc:
            raise HarnessError('OPERATION_FAILED',
                               'transform could not be applied; linked data may require an explicit duplicate') from exc
        return {'changedObjects': [obj.name], 'result': self.resolver.receipt(obj)}

    def set_origin(self, arguments):
        obj = self.resolver.resolve(arguments)
        origin = str(arguments.get('origin', '')).upper()
        if origin not in {'GEOMETRY', 'CENTER_OF_MASS', 'CENTER_OF_VOLUME', 'CURSOR'}:
            raise HarnessError('INVALID_ARGUMENT', 'unsupported origin method')
        operator_type = {'GEOMETRY': 'ORIGIN_GEOMETRY', 'CENTER_OF_MASS': 'ORIGIN_CENTER_OF_MASS',
                         'CENTER_OF_VOLUME': 'ORIGIN_CENTER_OF_VOLUME', 'CURSOR': 'ORIGIN_CURSOR'}[origin]
        with self.operation_context.active_object(obj):
            self.bpy.ops.object.origin_set(type=operator_type, center='MEDIAN')
        return {'changedObjects': [obj.name], 'result': self.resolver.receipt(obj)}

    def join(self, arguments):
        locators = arguments.get('objects')
        if not isinstance(locators, list) or len(locators) < 2:
            raise HarnessError('INVALID_ARGUMENT', 'objects must contain at least two locators')
        objects = [self.resolver.resolve(locator, required_type={'MESH'}) for locator in locators]
        if len({id(obj) for obj in objects}) != len(objects):
            raise HarnessError('INVALID_ARGUMENT', 'objects must be unique')
        changed_names = [obj.name for obj in objects]
        active = objects[0]
        new_name = arguments.get('newName')
        if new_name:
            new_name = require_name(new_name)
            if self.bpy.data.objects.get(new_name) not in {None, active}:
                raise HarnessError('NAME_COLLISION', f'object already exists: {new_name}')
        with self.operation_context.active_objects(objects, active=active):
            result = self.bpy.ops.object.join()
            if result != {'FINISHED'}: raise HarnessError('OPERATION_FAILED', 'join did not finish')
        if new_name:
            active.name = new_name
        return {'changedObjects': changed_names, 'result': self.resolver.receipt(active)}

    def separate(self, arguments):
        obj = self.resolver.resolve(arguments, required_type={'MESH'})
        method = str(arguments.get('method', 'LOOSE')).upper()
        if method not in {'LOOSE', 'MATERIAL'}:
            raise HarnessError('INVALID_ARGUMENT', 'method must be LOOSE or MATERIAL')
        before = set(self.bpy.data.objects)
        with self.operation_context.active_object(obj, mode='EDIT'):
            self.bpy.ops.mesh.select_all(action='SELECT')
            result = self.bpy.ops.mesh.separate(type=method)
            if result != {'FINISHED'}: raise HarnessError('OPERATION_FAILED', 'separate did not finish')
        created = sorted((candidate for candidate in self.bpy.data.objects if candidate not in before), key=lambda item: item.name)
        return {'changedObjects': [obj.name, *[item.name for item in created]],
                'result': {'source': self.resolver.receipt(obj), 'created': [self.resolver.receipt(item) for item in created]}}
