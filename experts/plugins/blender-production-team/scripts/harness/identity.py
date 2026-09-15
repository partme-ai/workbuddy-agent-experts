"""Stable object identity in addition to compatibility name lookup."""
from uuid import uuid4

from .errors import HarnessError


OBJECT_ID_KEY = 'codex_blender_object_id'


class ObjectResolver:
    def __init__(self, bpy_module):
        self.bpy = bpy_module
        self._fallback = {}

    def ensure_id(self, obj):
        current = obj.get(OBJECT_ID_KEY) if hasattr(obj, 'get') else self._fallback.get(id(obj))
        collisions = sorted((other for other in self.bpy.data.objects
                             if other is not obj and getattr(other, 'get', lambda *_: None)(OBJECT_ID_KEY) == current),
                            key=lambda other: other.name)
        if not isinstance(current, str) or not current.startswith('obj_') or collisions:
            # The alphabetic first owner retains an imported duplicate ID.
            owners = sorted([obj, *collisions], key=lambda other: other.name)
            if current and owners[0] is obj:
                return current
            current = 'obj_' + uuid4().hex
            if hasattr(obj, '__setitem__'):
                obj[OBJECT_ID_KEY] = current
            else:
                self._fallback[id(obj)] = current
        return current

    def assign_new_id(self,obj):
        current='obj_'+uuid4().hex
        if hasattr(obj,'__setitem__'): obj[OBJECT_ID_KEY]=current
        else:self._fallback[id(obj)]=current
        return current

    def resolve(self, locator, *, required_type=None):
        if not isinstance(locator, dict):
            raise HarnessError('INVALID_ARGUMENT', 'object locator must be an object')
        name, stable_id = locator.get('name'), locator.get('objectId')
        if not name and not stable_id:
            raise HarnessError('INVALID_ARGUMENT', 'name or objectId is required')
        by_name = self.bpy.data.objects.get(name) if isinstance(name, str) else None
        matches = [obj for obj in self.bpy.data.objects if stable_id and
                   (getattr(obj, 'get', lambda *_: None)(OBJECT_ID_KEY) == stable_id
                    or self._fallback.get(id(obj)) == stable_id)]
        if len(matches) > 1:
            matches.sort(key=lambda obj: obj.name)
            for duplicate in matches[1:]:
                self.ensure_id(duplicate)
            matches = matches[:1]
        by_id = matches[0] if matches else None
        if name and stable_id and by_name is not by_id:
            raise HarnessError('OBJECT_ID_MISMATCH', 'name and objectId identify different objects')
        obj = by_name or by_id
        if obj is None:
            raise HarnessError('OBJECT_NOT_FOUND', 'object locator did not match an object')
        if required_type and obj.type not in required_type:
            raise HarnessError('OBJECT_TYPE_MISMATCH', f'object type must be one of {sorted(required_type)}')
        self.ensure_id(obj)
        return obj

    def receipt(self, obj):
        return {'name': obj.name, 'objectId': self.ensure_id(obj), 'type': obj.type}
