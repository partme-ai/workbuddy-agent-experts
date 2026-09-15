"""Blender 5 Grease Pencil layers, materials, strokes and frames."""
from ..errors import HarnessError
from ..identity import ObjectResolver
from ..operation_context import OperationContext
from .validation import finite_number,require_name,vector3


class GreasePencilCommands:
    def __init__(self,bpy_module):self.bpy=bpy_module;self.objects=ObjectResolver(bpy_module);self.context=OperationContext(bpy_module)
    def create(self,args):
        name=require_name(args.get('name'));layers=args.get('layers',['Lines'])
        if self.bpy.data.objects.get(name):raise HarnessError('NAME_COLLISION',f'object already exists: {name}')
        if not isinstance(layers,list) or not layers or any(not isinstance(v,str) or not v for v in layers):raise HarnessError('INVALID_ARGUMENT','layers must contain names')
        in_front=args.get('inFront',True)
        if type(in_front) is not bool:raise HarnessError('INVALID_ARGUMENT','inFront must be boolean')
        result=self.bpy.ops.object.grease_pencil_add(type='EMPTY',use_in_front=in_front)
        if result!={'FINISHED'}:raise HarnessError('OPERATION_FAILED','Grease Pencil creation did not finish')
        obj=self.bpy.context.object;obj.name=name
        for existing in list(obj.data.layers):obj.data.layers.remove(existing)
        obj.data.materials.clear()
        for index,layer_name in enumerate(layers):obj.data.layers.new(layer_name,set_active=index==0)
        return {'changedObjects':[name],'result':self.objects.receipt(obj)|{'layers':layers}}
    def add_material(self,args):
        obj=self.objects.resolve(args,required_type={'GREASEPENCIL'});name=require_name(args.get('material'));color=args.get('color')
        if not isinstance(color,(list,tuple)) or len(color)!=4:raise HarnessError('INVALID_ARGUMENT','color requires RGBA')
        color=tuple(finite_number(value,'color',minimum=0) for value in color)
        if any(value>1 for value in color):raise HarnessError('INVALID_ARGUMENT','color values must be at most 1')
        material=self.bpy.data.materials.get(name) or self.bpy.data.materials.new(name)
        if not material.is_grease_pencil:self.bpy.data.materials.create_gpencil_data(material)
        material.grease_pencil.color=color
        if obj.data.materials.get(name) is None:obj.data.materials.append(material)
        return {'changedObjects':[obj.name],'result':{'object':self.objects.receipt(obj),'material':name,'index':obj.data.materials.find(name)}}
    def add_stroke(self,args):
        obj=self.objects.resolve(args,required_type={'GREASEPENCIL'});layer=obj.data.layers.get(require_name(args.get('layer')))
        if layer is None:raise HarnessError('INVALID_ARGUMENT','layer was not found')
        frame=args.get('frame');points=args.get('points');material=args.get('materialIndex',0);cyclic=args.get('cyclic',False)
        if type(frame) is not int or not isinstance(points,list) or len(points)<2:raise HarnessError('INVALID_ARGUMENT','frame and at least two points are required')
        if type(material) is not int or not 0<=material<len(obj.data.materials) or type(cyclic) is not bool:raise HarnessError('INVALID_ARGUMENT','materialIndex/cyclic is invalid')
        parsed=[]
        for point in points:
            if not isinstance(point,dict):raise HarnessError('INVALID_ARGUMENT','stroke point must be an object')
            parsed.append((vector3(point.get('position'),'position'),finite_number(point.get('radius',1),'radius',positive=True),
                           finite_number(point.get('opacity',1),'opacity',minimum=0)))
            if parsed[-1][2]>1:raise HarnessError('INVALID_ARGUMENT','opacity must be at most 1')
        gp_frame=next((item for item in layer.frames if item.frame_number==frame),None) or layer.frames.new(frame);drawing=gp_frame.drawing;before=len(drawing.strokes);drawing.add_strokes([len(parsed)]);stroke=drawing.strokes[before]
        stroke.cyclic=cyclic;stroke.material_index=material
        for target,(position,radius,opacity) in zip(stroke.points,parsed):target.position=position;target.radius=radius;target.opacity=opacity
        return {'changedObjects':[obj.name],'result':{'object':self.objects.receipt(obj),'layer':layer.name,'frame':frame,'strokeIndex':before,'points':len(parsed)}}
    def inspect(self,args):
        obj=self.objects.resolve(args,required_type={'GREASEPENCIL'});layers=[]
        for layer in obj.data.layers:
            layers.append({'name':layer.name,'frames':[{'frame':frame.frame_number,'strokes':len(frame.drawing.strokes),
              'points':sum(len(stroke.points) for stroke in frame.drawing.strokes)} for frame in layer.frames]})
        return {'changedObjects':[],'result':self.objects.receipt(obj)|{'layers':layers,'materials':[m.name for m in obj.data.materials]}}
