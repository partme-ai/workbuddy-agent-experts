"""Non-destructive named compositor chain and inspection."""
from pathlib import Path

from ..errors import HarnessError
from .validation import finite_number


class CompositorCommands:
    def __init__(self,bpy_module,output_root=None):
        self.bpy=bpy_module;self.output_root=Path(output_root).resolve() if output_root else None
    def _tree(self,create=False):
        scene=self.bpy.context.scene;tree=getattr(scene,'node_tree',None) or getattr(scene,'compositing_node_group',None)
        if tree is None and create:
            tree=self.bpy.data.node_groups.new('Codex Scene Compositor','CompositorNodeTree')
            tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
            scene.compositing_node_group=tree
            if hasattr(scene,'use_nodes'):scene.use_nodes=True
        return tree
    def configure(self,args):
        scene=self.bpy.context.scene;tree=self._tree(True);exposure=finite_number(args.get('exposure',0),'exposure');glare=args.get('glare',False)
        if type(glare) is not bool:raise HarnessError('INVALID_ARGUMENT','glare must be boolean')
        def node(node_type,name):
            existing=tree.nodes.get(name)
            if existing and existing.bl_idname!=node_type:tree.nodes.remove(existing);existing=None
            item=existing or tree.nodes.new(node_type);item.name=name;return item
        render=node('CompositorNodeRLayers','Codex Render Layers');expose=node('CompositorNodeExposure','Codex Exposure');expose.inputs['Exposure'].default_value=exposure
        balance=node('CompositorNodeColorBalance','Codex Color Balance')
        composite=node('CompositorNodeComposite','Codex Composite') if hasattr(self.bpy.types,'CompositorNodeComposite') else node('NodeGroupOutput','Codex Composite')
        chain=[render,expose,balance]
        if glare:
            glare_node=node('CompositorNodeGlare','Codex Glare')
            if hasattr(glare_node,'glare_type'):glare_node.glare_type='FOG_GLOW'
            chain.append(glare_node)
        chain.append(composite)
        for source,target in zip(chain,chain[1:]):tree.links.new(source.outputs['Image'],target.inputs['Image'])
        return {'changedObjects':[],'result':{'nodes':[item.name for item in chain],'exposure':exposure,'glare':glare}}
    def inspect(self,_args):
        scene=self.bpy.context.scene;tree=self._tree(False)
        if tree is None:return {'changedObjects':[],'result':{'enabled':False,'nodes':[],'links':[]}}
        return {'changedObjects':[],'result':{'enabled':True,'nodes':[{'name':n.name,'type':n.bl_idname} for n in tree.nodes],
          'links':[{'from':f'{l.from_node.name}.{l.from_socket.name}','to':f'{l.to_node.name}.{l.to_socket.name}'} for l in tree.links]}}

    def add_tracking_mask(self,args):
        clip=self.bpy.data.movieclips.get(args.get('clip'));name=args.get('maskName');points=args.get('points')
        if clip is None:raise HarnessError('CLIP_NOT_FOUND','movie clip was not found')
        if not isinstance(name,str) or not name or self.bpy.data.masks.get(name):raise HarnessError('INVALID_ARGUMENT','maskName is invalid or exists')
        if not isinstance(points,list) or len(points)<3:raise HarnessError('INVALID_ARGUMENT','mask requires at least three points')
        parsed=[]
        for point in points:
            if not isinstance(point,(list,tuple)) or len(point)!=2:raise HarnessError('INVALID_ARGUMENT','mask points require two values')
            values=[finite_number(v,'mask point') for v in point]
            if any(v<0 or v>1 for v in values):raise HarnessError('INVALID_ARGUMENT','mask points must be normalized')
            parsed.append(values)
        mask=self.bpy.data.masks.new(name);layer=mask.layers.new(name='Tracked Mask');spline=layer.splines.new();spline.points.add(len(parsed)-1);spline.use_cyclic=True
        for target,co in zip(spline.points,parsed):target.co=co;target.handle_type='AUTO'
        tree=self._tree(True);movie=tree.nodes.new('CompositorNodeMovieClip');movie.name='Codex Tracking Clip';movie.clip=clip
        mask_node=tree.nodes.new('CompositorNodeMask');mask_node.name='Codex Tracking Mask';mask_node.mask=mask
        alpha=tree.nodes.new('CompositorNodeAlphaOver');alpha.name='Codex Tracking Composite'
        output=tree.nodes.get('Codex Composite')
        if output is None:raise HarnessError('NODE_NOT_FOUND','configure the compositor before adding a tracking mask')
        existing=next((link for link in tree.links if link.to_node.name==output.name),None)
        if existing is None:raise HarnessError('NODE_NOT_FOUND','compositor output has no image source')
        foreground=existing.from_socket;output_socket=existing.to_socket;tree.links.remove(existing)
        background=alpha.inputs.get('Background') or alpha.inputs[1];front=alpha.inputs.get('Foreground') or alpha.inputs[2];factor=alpha.inputs.get('Factor') or alpha.inputs[0]
        tree.links.new(movie.outputs['Image'],background);tree.links.new(foreground,front);tree.links.new(mask_node.outputs['Mask'],factor);tree.links.new(alpha.outputs['Image'],output_socket)
        return {'changedObjects':[],'result':{'clip':clip.name,'mask':mask.name,'points':len(parsed),
          'nodes':[movie.name,mask_node.name,alpha.name]}}

    def _output_directory(self,value,create=True):
        if self.output_root is None:raise HarnessError('OUTPUT_NOT_AUTHORIZED','compositor output requires an approved output root')
        path=Path(value)
        if path.is_symlink():raise HarnessError('OUTPUT_NOT_AUTHORIZED','compositor output must not be a symlink')
        resolved=path.resolve()
        if not resolved.is_relative_to(self.output_root):raise HarnessError('OUTPUT_NOT_AUTHORIZED','compositor output escaped approved root')
        if create:resolved.mkdir(parents=True,exist_ok=True)
        return resolved

    def add_file_output(self,args):
        name=args.get('name');base_name=args.get('baseName');format_name=str(args.get('format','PNG')).upper()
        if not isinstance(name,str) or not name or not isinstance(base_name,str) or not base_name:
            raise HarnessError('INVALID_ARGUMENT','name and baseName are required')
        if format_name not in {'PNG','OPEN_EXR_MULTILAYER'}:raise HarnessError('INVALID_ARGUMENT','format must be PNG or OPEN_EXR_MULTILAYER')
        depth=str(args.get('colorDepth','16'));allowed={'8','16'} if format_name=='PNG' else {'16','32'}
        if depth not in allowed:raise HarnessError('INVALID_ARGUMENT','unsupported colorDepth for compositor output')
        directory=self._output_directory(args.get('outputDir'),create=False);tree=self._tree(False)
        if tree is None:raise HarnessError('NODE_NOT_FOUND','configure the compositor before adding file output')
        composite=tree.nodes.get('Codex Composite');incoming=next((link for link in tree.links if link.to_node==composite),None)
        if incoming is None:raise HarnessError('NODE_NOT_FOUND','configure the compositor before adding file output')
        directory.mkdir(parents=True,exist_ok=True);existing=tree.nodes.get(name)
        if existing and existing.bl_idname!='CompositorNodeOutputFile':raise HarnessError('NAME_COLLISION','node name is already used')
        node=existing or tree.nodes.new('CompositorNodeOutputFile');node.name=name
        node.format.file_format=format_name;node.format.color_depth=depth
        if hasattr(node,'directory'):
            node.directory=str(directory);node.file_name=base_name+'_'
            if not any(getattr(socket,'name','')=='Image' for socket in node.inputs):
                node.file_output_items.new('RGBA','Image')
        else:
            node.base_path=str(directory)
            slots=getattr(node,'file_slots',None) or getattr(node,'layer_slots',None)
            if slots and len(slots):slots[0].path=base_name+'_'
        target_input=node.inputs.get('Image') or next((socket for socket in node.inputs if socket.bl_idname!='NodeSocketVirtual'),None)
        if target_input is None:raise HarnessError('NODE_NOT_FOUND','file output has no image input')
        tree.links.new(incoming.from_socket,target_input)
        return {'changedObjects':[],'result':{'name':node.name,'outputDir':str(directory),'baseName':base_name,
          'format':format_name,'colorDepth':depth}}

    def create_strip_group(self,args):
        name=args.get('name');exposure=finite_number(args.get('exposure',0),'exposure')
        if not isinstance(name,str) or not name or self.bpy.data.node_groups.get(name):raise HarnessError('INVALID_ARGUMENT','group name is invalid or already exists')
        tree=self.bpy.data.node_groups.new(name,'CompositorNodeTree')
        tree.interface.new_socket(name='Image',in_out='INPUT',socket_type='NodeSocketColor')
        tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
        group_input=tree.nodes.new('NodeGroupInput');group_input.name='Input'
        expose=tree.nodes.new('CompositorNodeExposure');expose.name='Exposure';expose.inputs['Exposure'].default_value=exposure
        group_output=tree.nodes.new('NodeGroupOutput');group_output.name='Output'
        tree.links.new(group_input.outputs['Image'],expose.inputs['Image']);tree.links.new(expose.outputs['Image'],group_output.inputs['Image'])
        return {'changedObjects':[],'result':{'name':tree.name,'exposure':exposure,'nodes':['Input','Exposure','Output']}}
