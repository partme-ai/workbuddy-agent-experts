"""PBR material creation and assignment."""

from __future__ import annotations
from pathlib import Path

from .validation import require_name
from ..errors import HarnessError
from ..identity import ObjectResolver
from ..operation_context import OperationContext


def _unit(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
        raise HarnessError("INVALID_ARGUMENT", f"{field} must be between 0 and 1")
    return float(value)


def _principled(nodes):
    node = nodes.get("Principled BSDF")
    if node is not None:
        return node
    return next((candidate for candidate in nodes if getattr(candidate, "type", None) == "BSDF_PRINCIPLED"), None)


class MaterialCommands:
    def __init__(self, bpy_module, *, asset_policy=None, output_root=None):
        self.bpy = bpy_module
        self.asset_policy = asset_policy
        self.output_root = Path(output_root).resolve() if output_root else None
        self.objects = ObjectResolver(bpy_module)
        self.context = OperationContext(bpy_module)

    def create_pbr(self, arguments: dict) -> dict:
        name = require_name(arguments.get("name"))
        if self.bpy.data.materials.get(name) is not None:
            raise HarnessError("NAME_COLLISION", f"material already exists: {name}")
        color = arguments.get("baseColor", [0.8, 0.8, 0.8, 1.0])
        if not isinstance(color, (list, tuple)) or len(color) != 4:
            raise HarnessError("INVALID_ARGUMENT", "baseColor must contain four numbers")
        color = tuple(_unit(item, "baseColor") for item in color)
        metallic = _unit(arguments.get('metallic', 0.0), 'metallic')
        roughness = _unit(arguments.get('roughness', 0.5), 'roughness')
        alpha = _unit(arguments.get('alpha', 1.0), 'alpha')
        material = self.bpy.data.materials.new(name=name)
        material.use_nodes = True
        principled = _principled(material.node_tree.nodes)
        if principled is None:
            raise HarnessError("MATERIAL_NODE_MISSING", "Principled BSDF node is unavailable")
        principled.inputs["Base Color"].default_value = color
        principled.inputs["Metallic"].default_value = metallic
        principled.inputs["Roughness"].default_value = roughness
        principled.inputs["Alpha"].default_value = alpha
        return {"changedObjects": [], "result": {"name": name}}

    def assign(self, arguments: dict) -> dict:
        object_name = require_name(arguments.get("object"))
        material_name = require_name(arguments.get("material"))
        obj = self.bpy.data.objects.get(object_name)
        material = self.bpy.data.materials.get(material_name)
        if obj is None:
            raise HarnessError("OBJECT_NOT_FOUND", f"object not found: {object_name}")
        if material is None:
            raise HarnessError("MATERIAL_NOT_FOUND", f"material not found: {material_name}")
        slots = obj.data.materials
        if len(slots):
            slots[0] = material
        else:
            slots.append(material)
        return {"changedObjects": [object_name]}

    def attach_image_texture(self, arguments: dict) -> dict:
        material_name = require_name(arguments.get("material"))
        if self.asset_policy is None:
            raise HarnessError("ASSET_NOT_AUTHORIZED", "no asset root was approved")
        path = self.asset_policy.require_file(arguments.get("path"))
        material = self.bpy.data.materials.get(material_name)
        if material is None:
            raise HarnessError("MATERIAL_NOT_FOUND", f"material not found: {material_name}")
        material.use_nodes = True
        principled = _principled(material.node_tree.nodes)
        if principled is None:
            raise HarnessError("MATERIAL_NODE_MISSING", "Principled BSDF node is unavailable")
        image = self.bpy.data.images.load(str(path), check_existing=True)
        texture = material.node_tree.nodes.new("ShaderNodeTexImage")
        texture.image = image
        material.node_tree.links.new(texture.outputs["Color"], principled.inputs["Base Color"])
        return {"changedObjects": [], "result": {"material": material_name, "path": str(path)}}

    def connect_image_texture(self,arguments):
        material_name=require_name(arguments.get('material')); usage=str(arguments.get('usage','')).upper()
        if usage not in {'BASE_COLOR','ROUGHNESS','METALLIC','NORMAL'}:
            raise HarnessError('INVALID_ARGUMENT','usage must be BASE_COLOR, ROUGHNESS, METALLIC or NORMAL')
        if self.asset_policy is None: raise HarnessError('ASSET_NOT_AUTHORIZED','no asset root was approved')
        path=self.asset_policy.require_file(arguments.get('path')); material=self.bpy.data.materials.get(material_name)
        if material is None: raise HarnessError('MATERIAL_NOT_FOUND',f'material not found: {material_name}')
        material.use_nodes=True; principled=_principled(material.node_tree.nodes)
        if principled is None: raise HarnessError('MATERIAL_NODE_MISSING','Principled BSDF node is unavailable')
        image=self.bpy.data.images.load(str(path),check_existing=True)
        image.colorspace_settings.name='sRGB' if usage=='BASE_COLOR' else 'Non-Color'
        texture=material.node_tree.nodes.new('ShaderNodeTexImage'); texture.image=image
        created=[texture]
        try:
            if usage=='NORMAL':
                normal=material.node_tree.nodes.new('ShaderNodeNormalMap'); created.append(normal)
                material.node_tree.links.new(texture.outputs['Color'],normal.inputs['Color'])
                material.node_tree.links.new(normal.outputs['Normal'],principled.inputs['Normal'])
            else:
                target={'BASE_COLOR':'Base Color','ROUGHNESS':'Roughness','METALLIC':'Metallic'}[usage]
                material.node_tree.links.new(texture.outputs['Color'],principled.inputs[target])
        except Exception as exc:
            for node in reversed(created): material.node_tree.nodes.remove(node)
            raise HarnessError('OPERATION_FAILED','material node connection failed') from exc
        return {'changedObjects':[],'result':{'material':material_name,'usage':usage,'path':str(path),
                'colorSpace':image.colorspace_settings.name,'nodes':[node.name for node in created]}}

    def inspect_nodes(self,arguments):
        name=require_name(arguments.get('material')); material=self.bpy.data.materials.get(name)
        if material is None: raise HarnessError('MATERIAL_NOT_FOUND',f'material not found: {name}')
        if not material.use_nodes or material.node_tree is None:
            return {'changedObjects':[],'result':{'material':name,'usesNodes':False,'nodes':[],'links':[]}}
        nodes=[{'name':node.name,'type':node.bl_idname,
                'image':getattr(getattr(node,'image',None),'filepath',None),
                'colorSpace':getattr(getattr(getattr(node,'image',None),'colorspace_settings',None),'name',None)}
               for node in material.node_tree.nodes]
        links=[{'fromNode':link.from_node.name,'fromSocket':link.from_socket.name,
                'toNode':link.to_node.name,'toSocket':link.to_socket.name} for link in material.node_tree.links]
        return {'changedObjects':[],'result':{'material':name,'usesNodes':True,'nodes':nodes,'links':links}}

    def create_node_group(self,arguments):
        material_name=require_name(arguments.get('material'));group_name=require_name(arguments.get('groupName'))
        material=self.bpy.data.materials.get(material_name)
        if material is None:raise HarnessError('MATERIAL_NOT_FOUND',f'material not found: {material_name}')
        if self.bpy.data.node_groups.get(group_name):raise HarnessError('NAME_COLLISION',f'node group already exists: {group_name}')
        color=arguments.get('baseColor',[.8,.8,.8,1]);roughness=_unit(arguments.get('roughness',.5),'roughness')
        if not isinstance(color,(list,tuple)) or len(color)!=4:raise HarnessError('INVALID_ARGUMENT','baseColor requires four numbers')
        color=tuple(_unit(value,'baseColor') for value in color)
        group=self.bpy.data.node_groups.new(group_name,'ShaderNodeTree')
        try:
            color_in=group.interface.new_socket(name='Base Color',in_out='INPUT',socket_type='NodeSocketColor');color_in.default_value=color
            rough_in=group.interface.new_socket(name='Roughness',in_out='INPUT',socket_type='NodeSocketFloat');rough_in.default_value=roughness
            group.interface.new_socket(name='Base Color',in_out='OUTPUT',socket_type='NodeSocketColor')
            group.interface.new_socket(name='Roughness',in_out='OUTPUT',socket_type='NodeSocketFloat')
            input_node=group.nodes.new('NodeGroupInput');output_node=group.nodes.new('NodeGroupOutput')
            group.links.new(input_node.outputs['Base Color'],output_node.inputs['Base Color']);group.links.new(input_node.outputs['Roughness'],output_node.inputs['Roughness'])
            material.use_nodes=True;principled=_principled(material.node_tree.nodes)
            node=material.node_tree.nodes.new('ShaderNodeGroup');node.name=group_name;node.node_tree=group
            material.node_tree.links.new(node.outputs['Base Color'],principled.inputs['Base Color']);material.node_tree.links.new(node.outputs['Roughness'],principled.inputs['Roughness'])
        except Exception:
            self.bpy.data.node_groups.remove(group);raise
        return {'changedObjects':[],'result':{'material':material_name,'groupName':group.name,
          'inputs':[{'name':item.name,'identifier':item.identifier} for item in group.interface.items_tree if item.item_type=='SOCKET' and item.in_out=='INPUT']}}

    def bake(self,arguments):
        obj=self.objects.resolve(arguments.get('object'),required_type={'MESH'});kind=str(arguments.get('bakeType','ROUGHNESS')).upper()
        if kind not in {'ROUGHNESS','NORMAL','AO','EMIT'}:raise HarnessError('INVALID_ARGUMENT','unsupported bakeType')
        if self.output_root is None:raise HarnessError('OUTPUT_NOT_AUTHORIZED','material baking requires an approved output root')
        path=(self.output_root/require_name(arguments.get('relativePath'))).resolve()
        if not path.is_relative_to(self.output_root) or path.suffix.lower()!='.png':raise HarnessError('OUTPUT_NOT_AUTHORIZED','bake path must be a PNG below output root')
        if path.exists():raise HarnessError('OVERWRITE_AUTHORIZATION_REQUIRED','bake output already exists')
        width=arguments.get('width',256);height=arguments.get('height',256);margin=arguments.get('margin',8)
        if any(type(v) is not int or v<1 for v in (width,height,margin)):raise HarnessError('INVALID_ARGUMENT','bake dimensions/margin must be positive integers')
        material=obj.active_material
        if material is None or not material.use_nodes:raise HarnessError('MATERIAL_NOT_FOUND','active node material is required')
        if obj.data.uv_layers.active is None:raise HarnessError('UV_REQUIRED','active UV layer is required')
        image=self.bpy.data.images.new(path.stem,width=width,height=height,alpha=False);image.filepath_raw=str(path);image.file_format='PNG'
        node=material.node_tree.nodes.new('ShaderNodeTexImage');node.name='Codex Bake Target '+path.stem;node.image=image
        for candidate in material.node_tree.nodes:candidate.select=False
        node.select=True;material.node_tree.nodes.active=node
        try:
            path.parent.mkdir(parents=True,exist_ok=True)
            with self.context.active_object(obj):
                result=self.bpy.ops.object.bake(type=kind,margin=margin)
                if result!={'FINISHED'}:raise RuntimeError('bake did not finish')
            image.save()
        except Exception as exc:
            material.node_tree.nodes.remove(node);self.bpy.data.images.remove(image)
            raise HarnessError('OPERATION_FAILED','material bake failed') from exc
        return {'changedObjects':[],'result':{'object':self.objects.receipt(obj),'material':material.name,'bakeType':kind,
          'path':str(path),'width':width,'height':height}}
