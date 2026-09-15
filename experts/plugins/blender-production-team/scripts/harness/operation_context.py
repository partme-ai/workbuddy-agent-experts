"""Restore Blender mode, active object and selection around operator calls."""
from contextlib import contextmanager

from .errors import HarnessError


class OperationContext:
    def __init__(self, bpy_module):
        self.bpy = bpy_module

    @contextmanager
    def active_object(self, obj, *, mode='OBJECT'):
        with self.active_objects([obj], active=obj, mode=mode):
            yield

    @contextmanager
    def active_objects(self, objects, *, active, mode='OBJECT'):
        context = self.bpy.context
        view_layer = getattr(context, 'view_layer', None)
        if view_layer is None:
            raise HarnessError('CONTEXT_UNAVAILABLE', 'active view layer is unavailable')
        previous_active = view_layer.objects.active
        previous_selected = list(getattr(context, 'selected_objects', ()))
        previous_mode = getattr(context, 'mode', 'OBJECT')
        try:
            if previous_mode != 'OBJECT':
                self.bpy.ops.object.mode_set(mode='OBJECT')
            for selected in list(getattr(context, 'selected_objects', ())):
                selected.select_set(False)
            for obj in objects:
                obj.select_set(True)
            view_layer.objects.active = active
            if mode != 'OBJECT':
                self.bpy.ops.object.mode_set(mode=mode)
            yield
            view_layer.update()
        finally:
            try:
                if getattr(context, 'mode', 'OBJECT') != 'OBJECT':
                    self.bpy.ops.object.mode_set(mode='OBJECT')
                for selected in list(getattr(context, 'selected_objects', ())):
                    selected.select_set(False)
                for selected in previous_selected:
                    if selected.name in self.bpy.data.objects:
                        selected.select_set(True)
                if previous_active and previous_active.name in self.bpy.data.objects:
                    view_layer.objects.active = previous_active
                if previous_mode != 'OBJECT' and previous_active and previous_active.name in self.bpy.data.objects:
                    restore_mode = ('EDIT' if previous_mode.startswith('EDIT_') else
                                    {'PAINT_WEIGHT':'WEIGHT_PAINT','PAINT_VERTEX':'VERTEX_PAINT',
                                     'PAINT_TEXTURE':'TEXTURE_PAINT'}.get(previous_mode,previous_mode))
                    self.bpy.ops.object.mode_set(mode=restore_mode)
            except Exception:
                # Never replace the original operation error with best-effort UI restoration.
                pass
