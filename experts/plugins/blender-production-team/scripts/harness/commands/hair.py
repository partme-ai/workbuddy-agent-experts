"""Native Blender Hair Curves creation and inspection."""
from ..errors import HarnessError
from ..identity import ObjectResolver
from ..operation_context import OperationContext
from .validation import finite_number,require_name,vector3


class HairCommands:
    def __init__(self,bpy_module):self.bpy=bpy_module;self.objects=ObjectResolver(bpy_module);self.context=OperationContext(bpy_module)
    def create_curves(self,args):
        surface=self.objects.resolve(args.get('surface'),required_type={'MESH'});name=require_name(args.get('name'));strands=args.get('strands')
        if self.bpy.data.objects.get(name):raise HarnessError('NAME_COLLISION',f'object already exists: {name}')
        if not isinstance(strands,list) or not strands:raise HarnessError('INVALID_ARGUMENT','strands must be a non-empty list')
        parsed=[]
        for strand in strands:
            if not isinstance(strand,list) or len(strand)<2:raise HarnessError('INVALID_ARGUMENT','each strand requires at least two points')
            parsed.append([vector3(point,'strand point') for point in strand])
        radius=finite_number(args.get('radius',.005),'radius',positive=True)
        with self.context.active_object(surface):
            result=self.bpy.ops.object.curves_empty_hair_add()
            if result!={'FINISHED'}:raise HarnessError('OPERATION_FAILED','hair creation did not finish')
            hair=self.bpy.context.object;hair.name=name
            hair.data.add_curves([len(strand) for strand in parsed])
            flattened=[value for strand in parsed for point in strand for value in point]
            hair.data.attributes['position'].data.foreach_set('vector',flattened)
            radius_attr=hair.data.attributes.get('radius') or hair.data.attributes.new('radius','FLOAT','POINT')
            for item in radius_attr.data:item.value=radius
            hair.data.surface=surface
        return {'changedObjects':[name],'result':self.objects.receipt(hair)|{'surface':self.objects.receipt(surface),'strands':len(parsed),'points':sum(map(len,parsed))}}
    def inspect(self,args):
        obj=self.objects.resolve(args,required_type={'CURVES'});data=obj.data
        return {'changedObjects':[],'result':self.objects.receipt(obj)|{'strands':len(data.curves),'points':len(data.points),
          'surface':self.objects.receipt(data.surface) if data.surface else None}}
