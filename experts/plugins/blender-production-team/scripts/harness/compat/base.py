"""Base compatibility adapter for Blender versions.

Provides the BlenderCompatibilityAdapter interface and re-exports
RuntimeIdentity from production_profile so callers can import from
either location.
"""

from __future__ import annotations

from ..errors import HarnessError
from ..production_profile import RuntimeIdentity

# Re-export so callers can use: from scripts.harness.compat.base import RuntimeIdentity
__all__ = ['BlenderCompatibilityAdapter', 'RuntimeIdentity']


class BlenderCompatibilityAdapter:
    """Abstract base for version-specific Blender API adapters.

    Every adapter must provide the ten methods listed below.  The default
    implementations raise CAPABILITY_UNAVAILABLE because a capability
    that no version module overrides is, by definition, unavailable.
    """

    def __init__(self, bpy_module):
        self.bpy = bpy_module

    # ------------------------------------------------------------------
    # Compositor
    # ------------------------------------------------------------------

    def create_compositor_tree(self, scene):
        """Ensure *scene* has a compositor node tree and return it.

        Returns the node tree object.
        """
        raise HarnessError(
            'CAPABILITY_UNAVAILABLE',
            f'create_compositor_tree is not supported in this Blender version',
        )

    def configure_file_output(self, node, directory, base_name):
        """Configure a CompositorNodeOutputFile for the current version.

        All known versions use node.directory + node.file_name (evidence:
        5.2.1 snapshot).  The six unverified versions may differ; Task 4's
        matrix will surface any such difference.
        """
        raise HarnessError(
            'CAPABILITY_UNAVAILABLE',
            'configure_file_output is not supported in this Blender version',
        )

    # ------------------------------------------------------------------
    # Sequence / VSE
    # ------------------------------------------------------------------

    def create_sequence_strip(self, editor, name, kind, channel, start, **kwargs):
        """Create a VSE strip of *kind* in *editor*.

        Returns the newly created strip.
        """
        raise HarnessError(
            'CAPABILITY_UNAVAILABLE',
            f'create_sequence_strip({kind}) is not supported in this Blender version',
        )

    def create_sequence_effect(self, editor, name, effect_type, channel, start,
                               end, input1=None, input2=None, **kwargs):
        """Create a VSE effect strip.

        Returns the newly created strip.
        """
        raise HarnessError(
            'CAPABILITY_UNAVAILABLE',
            f'create_sequence_effect({effect_type}) is not supported in this Blender version',
        )

    # ------------------------------------------------------------------
    # Geometry Nodes
    # ------------------------------------------------------------------

    def configure_geometry_node_interface(self, modifier, socket_identifier, value):
        """Set *socket_identifier* on a Geometry Nodes *modifier* to *value*.

        Returns the actual value that was written.
        """
        raise HarnessError(
            'CAPABILITY_UNAVAILABLE',
            'configure_geometry_node_interface is not supported in this Blender version',
        )

    # ------------------------------------------------------------------
    # Grease Pencil
    # ------------------------------------------------------------------

    def create_grease_pencil_data(self, bpy_module, name, layers):
        """Create a Grease Pencil object with the given *layers*.

        Returns the created object.
        """
        raise HarnessError(
            'CAPABILITY_UNAVAILABLE',
            'create_grease_pencil_data is not supported in this Blender version',
        )

    # ------------------------------------------------------------------
    # Hair / Curves
    # ------------------------------------------------------------------

    def configure_hair_curves(self, hair_object, surface, radius):
        """Configure hair curves data on *hair_object*.

        Version differences in the attribute API are unverified; no version
        module overrides this yet.  Task 4's matrix may surface differences.
        """
        raise HarnessError(
            'CAPABILITY_UNAVAILABLE',
            'configure_hair_curves is not supported in this Blender version',
        )

    # ------------------------------------------------------------------
    # Rigging
    # ------------------------------------------------------------------

    def enable_rigify(self, bpy_module):
        """Return a dict describing Rigify availability for this version.

        Keys: installed, bundledAvailable, enabled, operatorAvailable,
        blenderVersion.

        This implementation is version-independent: it probes addon_utils,
        the preferences addon list, and the rigify_generate operator.  All
        concrete adapters inherit it unchanged.
        """
        try:
            import addon_utils
            bundled = any(m.__name__ == 'rigify' for m in addon_utils.modules())
        except (ImportError, AttributeError):
            bundled = False
        addons = bpy_module.context.preferences.addons
        modules = [item if isinstance(item, str) else str(getattr(item, 'module', '')) for item in addons]
        enabled = addons.get('rigify') is not None or any(
            m == 'rigify' or m.endswith('.rigify') for m in modules
        )
        operator = hasattr(bpy_module.ops.pose, 'rigify_generate')
        return {
            'installed': bundled or enabled,
            'bundledAvailable': bundled,
            'enabled': enabled,
            'operatorAvailable': operator and enabled,
            'blenderVersion': bpy_module.app.version_string,
        }

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def configure_render_engine(self, scene, requested_engine, available_engines):
        """Return the correct engine identifier for *requested_engine*.

        The 5.2.1 snapshot reports only BLENDER_EEVEE (no BLENDER_EEVEE_NEXT).
        The six unverified versions may differ; Task 4's matrix will confirm.
        """
        raise HarnessError(
            'CAPABILITY_UNAVAILABLE',
            f'configure_render_engine({requested_engine}) is not supported',
        )

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_asset(self, bpy_module, path, fmt, **kwargs):
        """Export the current scene to *path* in format *fmt*.

        Returns a result dict with export details.
        """
        raise HarnessError(
            'CAPABILITY_UNAVAILABLE',
            f'export_asset({fmt}) is not supported in this Blender version',
        )
