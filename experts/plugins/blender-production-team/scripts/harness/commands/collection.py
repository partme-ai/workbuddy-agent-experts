"""Scene units and collection organization commands."""
from ..errors import HarnessError
from ..identity import ObjectResolver
from .validation import require_name, finite_number


class OrganizationCommands:
    def __init__(self, bpy_module):
        self.bpy = bpy_module
        self.objects = ObjectResolver(bpy_module)

    def set_units(self, arguments):
        system = str(arguments.get('system', '')).upper()
        if system not in {'METRIC', 'IMPERIAL', 'NONE'}:
            raise HarnessError('INVALID_ARGUMENT', 'system must be METRIC, IMPERIAL or NONE')
        scale = finite_number(arguments.get('scaleLength', 1), 'scaleLength', positive=True)
        units = self.bpy.context.scene.unit_settings
        units.system, units.scale_length = system, scale
        return {'changedObjects': [], 'result': {'system': system, 'scaleLength': scale}}

    def create_collection(self, arguments):
        name = require_name(arguments.get('name'))
        if self.bpy.data.collections.get(name):
            raise HarnessError('NAME_COLLISION', f'collection already exists: {name}')
        parent_name = arguments.get('parent')
        parent = self.bpy.data.collections.get(parent_name) if parent_name else self.bpy.context.scene.collection
        if parent is None:
            raise HarnessError('COLLECTION_NOT_FOUND', f'collection not found: {parent_name}')
        collection = self.bpy.data.collections.new(name)
        parent.children.link(collection)
        return {'changedObjects': [], 'result': {'name': collection.name}}

    def move_object(self, arguments):
        obj = self.objects.resolve(arguments)
        collection = self.bpy.data.collections.get(require_name(arguments.get('collection')))
        if collection is None:
            raise HarnessError('COLLECTION_NOT_FOUND', 'target collection was not found')
        if obj.name not in collection.objects:
            collection.objects.link(obj)
        if arguments.get('exclusive', True):
            for existing in list(obj.users_collection):
                if existing is not collection:
                    existing.objects.unlink(obj)
        return {'changedObjects': [obj.name], 'result': self.objects.receipt(obj) | {'collection': collection.name}}

    def set_visibility(self, arguments):
        collection = self.bpy.data.collections.get(require_name(arguments.get('name')))
        if collection is None: raise HarnessError('COLLECTION_NOT_FOUND', 'collection was not found')
        viewport, render = arguments.get('viewport'), arguments.get('render')
        if viewport is None and render is None: raise HarnessError('INVALID_ARGUMENT', 'viewport or render is required')
        if viewport is not None and type(viewport) is not bool: raise HarnessError('INVALID_ARGUMENT', 'viewport must be boolean')
        if render is not None and type(render) is not bool: raise HarnessError('INVALID_ARGUMENT', 'render must be boolean')
        if viewport is not None:
            collection.hide_viewport = not viewport
        if render is not None:
            collection.hide_render = not render
        return {'changedObjects': [], 'result': {'name': collection.name,
                'visibleViewport': not collection.hide_viewport, 'visibleRender': not collection.hide_render}}
