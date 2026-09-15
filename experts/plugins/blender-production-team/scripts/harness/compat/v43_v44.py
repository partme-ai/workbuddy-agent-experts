"""Compatibility adapter for Blender 4.3.x and 4.4.x.

This module shares the parent v42 adapter's behaviour.  The v4.3 release
introduced the extensions platform and simulation nodes; v4.4 continued
geometry-nodes improvements.  Neither changed the compositor tree API,
the file-output node API, the geometry-nodes modifier input API, the
Grease Pencil data-block API, or the render engine identifiers.

Runtime-verified: NO.  Only Blender 5.2.1 is installed.  The overrides
here are based on changelog analysis, not live testing.
"""

from .v42 import Blender42Adapter


class Blender4344Adapter(Blender42Adapter):
    """Adapter for Blender 4.3.x and 4.4.x.

    Inherits all behaviour from Blender42Adapter because no relevant
    API surface change was identified between 4.2 and 4.4 for the ten
    adapter methods.
    """
