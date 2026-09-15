"""Blender version compatibility adapter layer.

Centralises version-dependent API differences so domain commands
do not branch on bpy.app.version themselves.
"""

from .base import BlenderCompatibilityAdapter, RuntimeIdentity
from .selector import select_adapter

__all__ = ['BlenderCompatibilityAdapter', 'RuntimeIdentity', 'select_adapter']
