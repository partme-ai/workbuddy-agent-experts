"""Compatibility adapter for Blender 4.5.x.

Blender 4.5 is the final 4.x LTS release.  The compositor tree API,
file-output node API, and geometry-nodes modifier input API are
unchanged from 4.2.  The render engine identifier for Eevee remains
BLENDER_EEVEE in 4.5.

Runtime-verified: NO.  Only Blender 5.2.1 is installed.  The adapter
here is based on changelog analysis, not live testing.
"""

from .v42 import Blender42Adapter


class Blender45Adapter(Blender42Adapter):
    """Adapter for Blender 4.5.x.

    Inherits all behaviour from Blender42Adapter because no relevant
    API surface change was identified for the ten adapter methods.
    """
