"""Version-probed Geometry Nodes groups using socket identifiers, never UI positions."""
from ..errors import HarnessError
from ..identity import ObjectResolver
from .validation import require_name


SOCKET_TYPES={'FLOAT':'NodeSocketFloat','INT':'NodeSocketInt','VECTOR':'NodeSocketVector','BOOL':'NodeSocketBool'}
NODE_TYPES={'GeometryNodeDistributePointsOnFaces','GeometryNodeInstanceOnPoints','GeometryNodeMeshIcoSphere',
 'GeometryNodeRealizeInstances','GeometryNodeJoinGeometry','GeometryNodeTransform','GeometryNodeMeshCube',
 'GeometryNodeCurvePrimitiveArc','GeometryNodeCurveToMesh','GeometryNodeMeshLine','GeometryNodeSetMaterial'}


class GeometryNodeCommands:
    def __init__(self,bpy_module,adapter=None):self.bpy=bpy_module;self.objects=ObjectResolver(bpy_module);self.adapter=adapter
    def _group(self,name):
        group=self.bpy.data.node_groups.get(require_name(name))
        if group is None or group.bl_idname!='GeometryNodeTree':raise HarnessError('NODE_GROUP_NOT_FOUND','Geometry node group was not found')
        return group
    @staticmethod
    def _socket(sockets,key):
        matches=[socket for socket in sockets if getattr(socket,'identifier',None)==key or socket.name==key]
        if not matches:raise HarnessError('SOCKET_NOT_FOUND',f'socket not found: {key}')
        return matches[0]
    def create_group(self,arguments):
        obj=self.objects.resolve(arguments.get('object'),required_type={'MESH'}); group_name=require_name(arguments.get('groupName')); modifier_name=require_name(arguments.get('modifierName'))
        if self.bpy.data.node_groups.get(group_name):raise HarnessError('NAME_COLLISION',f'node group already exists: {group_name}')
        if obj.modifiers.get(modifier_name):raise HarnessError('NAME_COLLISION',f'modifier already exists: {modifier_name}')
        inputs=arguments.get('inputs',[])
        if not isinstance(inputs,list):raise HarnessError('INVALID_ARGUMENT','inputs must be a list')
        parsed=[];seen={'Geometry'}
        for spec in inputs:
            if not isinstance(spec,dict):raise HarnessError('INVALID_ARGUMENT','input must be an object')
            name=require_name(spec.get('name'));kind=str(spec.get('type','')).upper()
            if name in seen or kind not in SOCKET_TYPES:raise HarnessError('INVALID_ARGUMENT','input name/type is invalid')
            seen.add(name);parsed.append((name,kind,spec.get('default')))
        group=self.bpy.data.node_groups.new(group_name,'GeometryNodeTree')
        try:
            group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
            group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
            for name,kind,default in parsed:
                socket=group.interface.new_socket(name=name,in_out='INPUT',socket_type=SOCKET_TYPES[kind])
                if default is not None:socket.default_value=default
            input_node=group.nodes.new('NodeGroupInput');input_node.name='Group Input'
            output_node=group.nodes.new('NodeGroupOutput');output_node.name='Group Output'
            modifier=obj.modifiers.new(name=modifier_name,type='NODES');modifier.node_group=group
        except Exception:
            self.bpy.data.node_groups.remove(group);raise
        return {'changedObjects':[obj.name],'result':{'object':self.objects.receipt(obj),'groupName':group.name,
          'modifierName':modifier.name,'inputs':[{'name':item.name,'identifier':item.identifier,'socketType':item.socket_type}
          for item in group.interface.items_tree if item.item_type=='SOCKET' and item.in_out=='INPUT']}}
    def add_node(self,arguments):
        group=self._group(arguments.get('groupName'));node_type=require_name(arguments.get('nodeType'));name=require_name(arguments.get('name'))
        if node_type not in NODE_TYPES:raise HarnessError('INVALID_ARGUMENT','nodeType is outside the supported set')
        if group.nodes.get(name):raise HarnessError('NAME_COLLISION',f'node already exists: {name}')
        try:node=group.nodes.new(node_type);node.name=name;node.label=str(arguments.get('label',''))
        except Exception as exc:raise HarnessError('CAPABILITY_UNAVAILABLE',f'node type unavailable in Blender {self.bpy.app.version_string}') from exc
        return {'changedObjects':[],'result':{'groupName':group.name,'name':node.name,'nodeType':node.bl_idname,
         'inputs':[{'name':s.name,'identifier':s.identifier} for s in node.inputs],
         'outputs':[{'name':s.name,'identifier':s.identifier} for s in node.outputs]}}
    def connect(self,arguments):
        group=self._group(arguments.get('groupName'));source=group.nodes.get(require_name(arguments.get('fromNode')));target=group.nodes.get(require_name(arguments.get('toNode')))
        if source is None or target is None:raise HarnessError('NODE_NOT_FOUND','source or target node was not found')
        output=self._socket(source.outputs,require_name(arguments.get('fromSocket')));input_socket=self._socket(target.inputs,require_name(arguments.get('toSocket')))
        try:link=group.links.new(output,input_socket)
        except Exception as exc:raise HarnessError('OPERATION_FAILED','socket types are incompatible') from exc
        return {'changedObjects':[],'result':{'groupName':group.name,'from':f'{source.name}.{output.identifier}','to':f'{target.name}.{input_socket.identifier}'}}
    def set_node_input(self,arguments):
        group=self._group(arguments.get('groupName'));node=group.nodes.get(require_name(arguments.get('node')))
        if node is None:raise HarnessError('NODE_NOT_FOUND','node was not found')
        socket=self._socket(node.inputs,require_name(arguments.get('socket')))
        if not hasattr(socket,'default_value'):raise HarnessError('INVALID_ARGUMENT','socket has no editable default')
        try:socket.default_value=arguments.get('value')
        except Exception as exc:raise HarnessError('INVALID_ARGUMENT','value is incompatible with socket') from exc
        return {'changedObjects':[],'result':{'groupName':group.name,'node':node.name,'socket':socket.identifier}}
    def set_modifier_input(self,arguments):
        obj=self.objects.resolve(arguments.get('object'));modifier=obj.modifiers.get(require_name(arguments.get('modifierName')))
        if modifier is None or modifier.type!='NODES' or modifier.node_group is None:raise HarnessError('MODIFIER_NOT_FOUND','Geometry Nodes modifier was not found')
        key=require_name(arguments.get('socket'));sockets=[item for item in modifier.node_group.interface.items_tree if item.item_type=='SOCKET' and item.in_out=='INPUT']
        socket=next((item for item in sockets if item.identifier==key or item.name==key),None)
        if socket is None or socket.socket_type=='NodeSocketGeometry':raise HarnessError('SOCKET_NOT_FOUND','editable modifier input was not found')
        try:
            value=arguments.get('value')
            if self.adapter is not None:
                actual=self.adapter.configure_geometry_node_interface(modifier,socket.identifier,value)
            else:
                interface_inputs=getattr(getattr(modifier,'properties',None),'inputs',None)
                if interface_inputs is not None and hasattr(interface_inputs,socket.identifier):
                    property_socket=getattr(interface_inputs,socket.identifier);property_socket.value=value;actual=property_socket.value
                else:
                    modifier[socket.identifier]=value;actual=modifier[socket.identifier]
            self.bpy.context.view_layer.update()
        except Exception as exc:raise HarnessError('INVALID_ARGUMENT','value is incompatible with modifier input') from exc
        return {'changedObjects':[obj.name],'result':{'object':self.objects.receipt(obj),'modifierName':modifier.name,
          'socket':socket.identifier,'value':actual}}
    def inspect(self,arguments):
        group=self._group(arguments.get('groupName'))
        return {'changedObjects':[],'result':{'groupName':group.name,
          'interface':[{'name':item.name,'identifier':item.identifier,'inOut':item.in_out,'socketType':item.socket_type}
                       for item in group.interface.items_tree if item.item_type=='SOCKET'],
          'nodes':[{'name':node.name,'nodeType':node.bl_idname} for node in group.nodes],
          'links':[{'fromNode':link.from_node.name,'fromSocket':link.from_socket.identifier,
                    'toNode':link.to_node.name,'toSocket':link.to_socket.identifier} for link in group.links]}}
