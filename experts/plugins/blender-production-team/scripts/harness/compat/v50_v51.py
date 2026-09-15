"""Compatibility adapter for Blender 5.0.x and 5.1.x.

Blender 5.0 introduced the Grease Pencil v3 rewrite (GreasePencil
data-block with layers/drawings replacing GPencil).  The compositor
is assumed to still use scene.node_tree in 5.0-5.1 (unverified;
CompositorNodeComposite was removed by 5.2).

Runtime-verified: NO.  Only Blender 5.2.1 is installed.  The adapter
here is based on changelog analysis, not live testing.
"""

from ..errors import HarnessError
from .base import BlenderCompatibilityAdapter


class Blender5051Adapter(BlenderCompatibilityAdapter):
    """Adapter for Blender 5.0.x and 5.1.x.

    Overrides create_grease_pencil_data for the GreasePencil v3 API.
    Other methods inherit the base class defaults where the 5.0/5.1
    behaviour matches 5.2; methods that differ from 5.2 but are
    unverifiable here are left as base-class defaults and will surface
    CAPABILITY_UNAVAILABLE if called.
    """

    def create_compositor_tree(self, scene):
        # In 5.0/5.1 the compositor still uses scene.node_tree.
        tree = getattr(scene, 'node_tree', None)
        if tree is None:
            tree = self.bpy.data.node_groups.new('Codex Scene Compositor', 'CompositorNodeTree')
            tree.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
            scene.node_tree = tree
            if hasattr(scene, 'use_nodes'):
                scene.use_nodes = True
        return tree

    def configure_file_output(self, node, directory, base_name):
        # The only evidence (5.2.1 snapshot) shows directory+file_name, not
        # base_path+file_slots.  Use the same API until Task 4's matrix
        # captures a real 5.0/5.1 surface that proves otherwise.
        node.directory = str(directory)
        node.file_name = base_name + '_'
        if not any(getattr(s, 'name', '') == 'Image' for s in node.inputs):
            node.file_output_items.new('RGBA', 'Image')

    def configure_geometry_node_interface(self, modifier, socket_identifier, value):
        # In 5.0/5.1 the properties.inputs interface may be available.
        # Try the new interface first, fall back to dict-style.
        interface_inputs = getattr(getattr(modifier, 'properties', None), 'inputs', None)
        if interface_inputs is not None and hasattr(interface_inputs, socket_identifier):
            property_socket = getattr(interface_inputs, socket_identifier)
            property_socket.value = value
            return property_socket.value
        modifier[socket_identifier] = value
        return modifier[socket_identifier]

    def create_grease_pencil_data(self, bpy_module, name, layers):
        """Create a GreasePencil v3 object (5.0+ API)."""
        bpy_module.ops.object.grease_pencil_add(type='EMPTY')
        obj = bpy_module.context.object
        obj.name = name
        for existing in list(obj.data.layers):
            obj.data.layers.remove(existing)
        obj.data.materials.clear()
        for index, layer_name in enumerate(layers):
            obj.data.layers.new(layer_name, set_active=index == 0)
        return obj

    def configure_render_engine(self, scene, requested_engine, available_engines):
        # Pick whichever Eevee identifier the running Blender actually reports,
        # rather than hard-coding a preference order.  Task 4's matrix will
        # codify any real 5.0/5.1 difference if one exists.
        if requested_engine in {'EEVEE', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'}:
            engine = next(
                (v for v in available_engines if v in {'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'}),
                None,
            )
            if engine is None:
                raise HarnessError('CAPABILITY_UNAVAILABLE', 'Eevee is unavailable')
            return engine
        if requested_engine == 'CYCLES':
            return 'CYCLES'
        raise HarnessError('INVALID_ARGUMENT', 'unsupported render engine')
