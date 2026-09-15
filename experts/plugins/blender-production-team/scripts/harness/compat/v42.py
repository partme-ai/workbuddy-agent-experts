"""Compatibility adapter for Blender 4.2.x.

Key API differences from later versions:
- Compositor uses scene.node_tree, CompositorNodeComposite.
- File output uses node.directory + node.file_name + node.file_output_items.
- Geometry Nodes modifier inputs use modifier[identifier] = value.
- Render engine EEVEE is BLENDER_EEVEE.
- Grease Pencil uses legacy GPencil data-blocks (not the 5.x rewrite).
- VSE effect strips use sequences.new_effect with seq1/seq2 kwargs.

Runtime-verified: NO.  Only Blender 5.2.1 is installed.  The adapter
here is based on changelog analysis and existing codebase patterns,
not live testing.
"""

from ..errors import HarnessError
from .base import BlenderCompatibilityAdapter


class Blender42Adapter(BlenderCompatibilityAdapter):
    """Adapter for Blender 4.2.x."""

    def create_compositor_tree(self, scene):
        tree = getattr(scene, 'node_tree', None)
        if tree is None:
            tree = self.bpy.data.node_groups.new('Codex Scene Compositor', 'CompositorNodeTree')
            tree.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
            scene.node_tree = tree
            if hasattr(scene, 'use_nodes'):
                scene.use_nodes = True
        return tree

    def configure_file_output(self, node, directory, base_name):
        node.directory = str(directory)
        node.file_name = base_name + '_'
        if not any(getattr(s, 'name', '') == 'Image' for s in node.inputs):
            node.file_output_items.new('RGBA', 'Image')

    def configure_geometry_node_interface(self, modifier, socket_identifier, value):
        modifier[socket_identifier] = value
        return modifier[socket_identifier]

    def create_grease_pencil_data(self, bpy_module, name, layers):
        gp_data = bpy_module.data.grease_pencil.new(name)
        obj = bpy_module.data.objects.new(name, gp_data)
        bpy_module.context.scene.collection.objects.link(obj)
        for existing in list(gp_data.layers):
            gp_data.layers.remove(existing)
        for index, layer_name in enumerate(layers):
            gp_data.layers.new(layer_name, set_active=index == 0)
        return obj

    def configure_render_engine(self, scene, requested_engine, available_engines):
        if requested_engine in {'EEVEE', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'}:
            engine = next(
                (v for v in ('BLENDER_EEVEE',) if v in available_engines), None
            )
            if engine is None:
                raise HarnessError('CAPABILITY_UNAVAILABLE', 'Eevee is unavailable')
            return engine
        if requested_engine == 'CYCLES':
            return 'CYCLES'
        raise HarnessError('INVALID_ARGUMENT', 'unsupported render engine')
