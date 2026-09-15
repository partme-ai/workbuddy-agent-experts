"""Explicit curve data creation, configuration and conversion."""
from ..errors import HarnessError
from ..identity import ObjectResolver
from ..operation_context import OperationContext
from .validation import finite_number, require_name, vector3


class CurveCommands:
    def __init__(self, bpy_module):
        self.bpy = bpy_module; self.objects = ObjectResolver(bpy_module); self.context = OperationContext(bpy_module)

    def create(self, arguments):
        name = require_name(arguments.get('name'))
        if self.bpy.data.objects.get(name): raise HarnessError('NAME_COLLISION', f'object already exists: {name}')
        points = arguments.get('points')
        if not isinstance(points, list) or len(points) < 2: raise HarnessError('INVALID_ARGUMENT', 'points requires at least two vectors')
        points = [vector3(point, 'points') for point in points]
        kind = str(arguments.get('splineType', 'POLY')).upper()
        if kind not in {'POLY', 'BEZIER'}: raise HarnessError('INVALID_ARGUMENT', 'splineType must be POLY or BEZIER')
        cyclic = arguments.get('cyclic', False)
        if type(cyclic) is not bool: raise HarnessError('INVALID_ARGUMENT', 'cyclic must be boolean')
        handle = str(arguments.get('handleType', 'AUTO')).upper()
        if handle not in {'AUTO', 'VECTOR', 'ALIGNED', 'FREE'}: raise HarnessError('INVALID_ARGUMENT', 'unsupported handleType')
        settings={}
        if 'bevelDepth' in arguments:settings['bevel_depth']=finite_number(arguments['bevelDepth'],'bevelDepth',minimum=0)
        if 'bevelResolution' in arguments:
            value=arguments['bevelResolution']
            if type(value) is not int or value<0:raise HarnessError('INVALID_ARGUMENT','bevelResolution must be nonnegative integer')
            settings['bevel_resolution']=value
        if 'resolution' in arguments:
            value=arguments['resolution']
            if type(value) is not int or value<1:raise HarnessError('INVALID_ARGUMENT','resolution must be positive integer')
            settings['resolution_u']=value
        curve = self.bpy.data.curves.new(name, 'CURVE'); curve.dimensions = '3D'
        spline = curve.splines.new(kind)
        if kind == 'BEZIER':
            spline.bezier_points.add(len(points)-1)
            for item, coordinate in zip(spline.bezier_points, points):
                item.co = coordinate; item.handle_left_type = handle; item.handle_right_type = handle
        else:
            spline.points.add(len(points)-1)
            for item, coordinate in zip(spline.points, points): item.co = (*coordinate, 1)
        spline.use_cyclic_u = cyclic
        obj = self.bpy.data.objects.new(name, curve); self.bpy.context.scene.collection.objects.link(obj)
        for key,value in settings.items():setattr(curve,key,value)
        return {'changedObjects':[name], 'result':self.objects.receipt(obj)}

    def configure(self, arguments):
        obj = self.objects.resolve(arguments, required_type={'CURVE'})
        data = obj.data
        values = {}
        if 'bevelDepth' in arguments: values['bevel_depth'] = finite_number(arguments['bevelDepth'],'bevelDepth',minimum=0)
        if 'bevelResolution' in arguments:
            value=arguments['bevelResolution']
            if type(value) is not int or value<0: raise HarnessError('INVALID_ARGUMENT','bevelResolution must be nonnegative integer')
            values['bevel_resolution']=value
        if 'resolution' in arguments:
            value=arguments['resolution']
            if type(value) is not int or value<1: raise HarnessError('INVALID_ARGUMENT','resolution must be positive integer')
            values['resolution_u']=value
        if not values: raise HarnessError('INVALID_ARGUMENT','curve configuration is empty')
        for key,value in values.items(): setattr(data,key,value)
        return {'changedObjects':[obj.name], 'result':self.objects.receipt(obj)}

    def to_mesh(self, arguments):
        obj = self.objects.resolve(arguments, required_type={'CURVE'})
        with self.context.active_object(obj):
            result=self.bpy.ops.object.convert(target='MESH')
            if result != {'FINISHED'}: raise HarnessError('OPERATION_FAILED','curve conversion did not finish')
        return {'changedObjects':[obj.name], 'result':self.objects.receipt(obj)}
