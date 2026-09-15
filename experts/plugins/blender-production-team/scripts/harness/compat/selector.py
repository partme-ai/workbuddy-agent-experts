"""Adapter selector: maps a RuntimeIdentity to the correct adapter class."""

from __future__ import annotations

from ..errors import HarnessError
from ..production_profile import RuntimeIdentity
from .base import BlenderCompatibilityAdapter

# Lazy imports to avoid circular dependency and keep startup fast.
_ADAPTER_MAP: dict[tuple[int, int], type[BlenderCompatibilityAdapter]] | None = None


def _get_adapter_map() -> dict[tuple[int, int], type[BlenderCompatibilityAdapter]]:
    global _ADAPTER_MAP
    if _ADAPTER_MAP is not None:
        return _ADAPTER_MAP
    from .v42 import Blender42Adapter
    from .v43_v44 import Blender4344Adapter
    from .v45 import Blender45Adapter
    from .v50_v51 import Blender5051Adapter
    from .v52 import Blender52Adapter

    _ADAPTER_MAP = {
        (4, 2): Blender42Adapter,
        (4, 3): Blender4344Adapter,
        (4, 4): Blender4344Adapter,
        (4, 5): Blender45Adapter,
        (5, 0): Blender5051Adapter,
        (5, 1): Blender5051Adapter,
        (5, 2): Blender52Adapter,
    }
    return _ADAPTER_MAP


def select_adapter(identity: RuntimeIdentity, bpy_module=None) -> BlenderCompatibilityAdapter:
    """Return an adapter instance for the given *identity*.

    If *bpy_module* is provided, the adapter is bound to it immediately.
    If omitted, the caller must later call ``adapter.bind(bpy_module)``
    before invoking any adapter method that touches Blender state.

    Raises HarnessError('CAPABILITY_UNAVAILABLE', ...) if the version
    is outside the supported range (4.2–5.2).
    """
    major, minor, _ = identity.blender_version
    adapter_map = _get_adapter_map()
    adapter_cls = adapter_map.get((major, minor))
    if adapter_cls is None:
        raise HarnessError(
            'CAPABILITY_UNAVAILABLE',
            f'Blender {major}.{minor} is not in the supported range (4.2–5.2)',
        )
    if bpy_module is not None:
        return adapter_cls(bpy_module)
    return _DeferredAdapter(adapter_cls, identity)


class _DeferredAdapter:
    """Stores the adapter class and identity; binds bpy on first use.

    This lets the selector be called early (before bpy is available)
    and the adapter be used later when bpy is loaded.
    """

    def __init__(self, adapter_cls: type[BlenderCompatibilityAdapter],
                 identity: RuntimeIdentity):
        self._cls = adapter_cls
        self._identity = identity
        self._bound: BlenderCompatibilityAdapter | None = None

    def bind(self, bpy_module) -> BlenderCompatibilityAdapter:
        """Create and cache a concrete adapter bound to *bpy_module*."""
        if self._bound is None:
            self._bound = self._cls(bpy_module)
        return self._bound

    @property
    def identity(self) -> RuntimeIdentity:
        return self._identity

    @property
    def adapter_class(self) -> type[BlenderCompatibilityAdapter]:
        return self._cls

    def __repr__(self) -> str:
        return f'<DeferredAdapter {self._cls.__name__} for {self._identity.blender_version}>'
