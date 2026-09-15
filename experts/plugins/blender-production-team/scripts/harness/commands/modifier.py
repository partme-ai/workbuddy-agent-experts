"""Typed lifecycle for the first supported production modifier set."""
from ..errors import HarnessError
from ..identity import ObjectResolver
from ..operation_context import OperationContext
from .validation import finite_number, require_name, vector3


TYPE_ALIASES = {'SUBDIVISION': 'SUBSURF'}
SCHEMAS = {
    'MIRROR': {'use_axis': 'bool_vector', 'use_clip': 'bool', 'merge_threshold': 'nonnegative'},
    'ARRAY': {'count': 'positive_int', 'relative_offset_displace': 'vector', 'use_relative_offset': 'bool',
              'constant_offset_displace':'vector','use_constant_offset':'bool'},
    'BEVEL': {'width': 'nonnegative', 'segments': 'positive_int', 'limit_method': ('enum', {'NONE','ANGLE','WEIGHT','VGROUP'})},
    'SUBSURF': {'levels': 'nonnegative_int', 'render_levels': 'nonnegative_int',
                'subdivision_type': ('enum', {'CATMULL_CLARK','SIMPLE'})},
    'SOLIDIFY': {'thickness': 'finite', 'offset': 'finite', 'use_even_offset': 'bool'},
    'BOOLEAN': {'operation': ('enum', {'INTERSECT','UNION','DIFFERENCE'}),
                'solver': ('enum', {'FAST','EXACT','MANIFOLD'}), 'object': 'object'},
    'DECIMATE': {'ratio': 'unit', 'decimate_type': ('enum', {'COLLAPSE','UNSUBDIV','DISSOLVE'}),
                 'angle_limit': 'nonnegative'},
}


class ModifierCommands:
    def __init__(self, bpy_module):
        self.bpy = bpy_module
        self.objects = ObjectResolver(bpy_module)
        self.context = OperationContext(bpy_module)

    def _object(self, args):
        return self.objects.resolve(args, required_type={'MESH', 'CURVE', 'FONT', 'SURFACE'})

    @staticmethod
    def _modifier(obj, name):
        name = require_name(name)
        modifier = obj.modifiers.get(name) if hasattr(obj.modifiers, 'get') else next((m for m in obj.modifiers if m.name == name), None)
        if modifier is None:
            raise HarnessError('MODIFIER_NOT_FOUND', f'modifier not found: {name}')
        return modifier

    def _settings(self, modifier_type, settings):
        if not isinstance(settings, dict):
            raise HarnessError('INVALID_ARGUMENT', 'settings must be an object')
        schema = SCHEMAS.get(modifier_type)
        if schema is None:
            raise HarnessError('INVALID_ARGUMENT', f'unsupported modifier type: {modifier_type}')
        result = {}
        for key, value in settings.items():
            kind = schema.get(key)
            if kind is None:
                raise HarnessError('INVALID_ARGUMENT', f'unsupported {modifier_type} setting: {key}')
            if kind == 'bool':
                if type(value) is not bool: raise HarnessError('INVALID_ARGUMENT', f'{key} must be boolean')
            elif kind == 'bool_vector':
                if not isinstance(value, list) or len(value) != 3 or any(type(item) is not bool for item in value):
                    raise HarnessError('INVALID_ARGUMENT', f'{key} must contain three booleans')
            elif kind == 'positive_int' or kind == 'nonnegative_int':
                limit = 1 if kind == 'positive_int' else 0
                if type(value) is not int or value < limit: raise HarnessError('INVALID_ARGUMENT', f'{key} is outside its range')
            elif kind == 'vector': value = vector3(value, key)
            elif kind == 'object':
                value = self.objects.resolve({'name': value}) if isinstance(value, str) else self.objects.resolve(value)
            elif kind == 'unit':
                value = finite_number(value, key, minimum=0)
                if value > 1: raise HarnessError('INVALID_ARGUMENT', f'{key} must be at most 1')
            elif kind == 'nonnegative': value = finite_number(value, key, minimum=0)
            elif kind == 'finite': value = finite_number(value, key)
            elif isinstance(kind, tuple) and kind[0] == 'enum':
                value = str(value).upper()
                if value not in kind[1]: raise HarnessError('INVALID_ARGUMENT', f'{key} has an unsupported value')
            result[key] = value
        return result

    def create(self, arguments):
        obj = self._object(arguments)
        modifier_type = TYPE_ALIASES.get(str(arguments.get('modifier', '')).upper(),
                                         str(arguments.get('modifier', '')).upper())
        settings = self._settings(modifier_type, arguments.get('settings', {}))
        requested_name = arguments.get('modifierName') or f'Codex {modifier_type.title()}'
        requested_name = require_name(requested_name)
        if self._find(obj, requested_name):
            raise HarnessError('NAME_COLLISION', f'modifier already exists: {requested_name}')
        try:
            modifier = obj.modifiers.new(name=requested_name, type=modifier_type)
            for key, value in settings.items(): setattr(modifier, key, value)
        except Exception as exc:
            if 'modifier' in locals() and modifier in obj.modifiers: obj.modifiers.remove(modifier)
            raise HarnessError('OPERATION_FAILED', 'Blender rejected the modifier configuration') from exc
        return {'changedObjects': [obj.name], 'result': self.objects.receipt(obj) | {
            'modifierName': modifier.name, 'modifierType': modifier.type}}

    @staticmethod
    def _find(obj, name):
        return obj.modifiers.get(name) if hasattr(obj.modifiers, 'get') else next((m for m in obj.modifiers if m.name == name), None)

    def list(self, arguments):
        obj = self._object(arguments)
        return {'changedObjects': [], 'result': self.objects.receipt(obj) | {'modifiers': [
            {'name': m.name, 'type': m.type, 'index': i, 'viewport': bool(m.show_viewport),
             'render': bool(m.show_render)} for i, m in enumerate(obj.modifiers)]}}

    def configure(self, arguments):
        obj = self._object(arguments); modifier = self._modifier(obj, arguments.get('modifierName'))
        settings = self._settings(modifier.type, arguments.get('settings'))
        try:
            for key, value in settings.items(): setattr(modifier, key, value)
        except Exception as exc:
            raise HarnessError('OPERATION_FAILED', 'Blender rejected the modifier settings') from exc
        return {'changedObjects': [obj.name], 'result': {'modifierName': modifier.name, 'modifierType': modifier.type}}

    def move(self, arguments):
        obj = self._object(arguments); modifier = self._modifier(obj, arguments.get('modifierName'))
        target = arguments.get('targetIndex')
        if type(target) is not int or not 0 <= target < len(obj.modifiers):
            raise HarnessError('INVALID_ARGUMENT', 'targetIndex is outside the modifier stack')
        obj.modifiers.move(list(obj.modifiers).index(modifier), target)
        return {'changedObjects': [obj.name], 'result': {'modifierName': modifier.name, 'index': target}}

    def set_enabled(self, arguments):
        obj = self._object(arguments); modifier = self._modifier(obj, arguments.get('modifierName'))
        viewport, render = arguments.get('viewport'), arguments.get('render')
        if viewport is None and render is None: raise HarnessError('INVALID_ARGUMENT', 'viewport or render is required')
        if viewport is not None:
            if type(viewport) is not bool: raise HarnessError('INVALID_ARGUMENT', 'viewport must be boolean')
            modifier.show_viewport = viewport
        if render is not None:
            if type(render) is not bool: raise HarnessError('INVALID_ARGUMENT', 'render must be boolean')
            modifier.show_render = render
        return {'changedObjects': [obj.name], 'result': {'modifierName': modifier.name,
                 'viewport': bool(modifier.show_viewport), 'render': bool(modifier.show_render)}}

    def apply(self, arguments):
        obj = self._object(arguments); modifier = self._modifier(obj, arguments.get('modifierName'))
        name = modifier.name
        try:
            with self.context.active_object(obj):
                result = self.bpy.ops.object.modifier_apply(modifier=name)
                if result != {'FINISHED'}: raise RuntimeError('operator did not finish')
        except Exception as exc:
            raise HarnessError('OPERATION_FAILED', 'modifier could not be applied; verify object mode and linked data') from exc
        return {'changedObjects': [obj.name], 'result': {'applied': name}}

    def remove(self, arguments):
        obj = self._object(arguments); modifier = self._modifier(obj, arguments.get('modifierName'))
        name = modifier.name; obj.modifiers.remove(modifier)
        return {'changedObjects': [obj.name], 'result': {'removed': name}}
