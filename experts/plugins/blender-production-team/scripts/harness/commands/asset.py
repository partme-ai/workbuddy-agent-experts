"""Import only from caller-approved asset roots."""
from pathlib import Path
from ..errors import HarnessError
from ..identity import ObjectResolver
from ..dependencies import generate_manifest, package_project, validate_portability


class AssetCommands:
    def __init__(self, bpy_module, asset_policy=None, output_root=None):
        self.bpy=bpy_module; self.policy=asset_policy; self.objects=ObjectResolver(bpy_module)
        self.output_root=output_root

    def _path(self, value):
        if self.policy is None: raise HarnessError('ASSET_NOT_AUTHORIZED','no asset root was approved')
        return self.policy.require_file(value)

    def import_file(self, arguments):
        path=self._path(arguments.get('path')); suffix=path.suffix.lower()
        before=set(self.bpy.data.objects)
        try:
            if suffix in {'.glb','.gltf'}: result=self.bpy.ops.import_scene.gltf(filepath=str(path))
            elif suffix=='.fbx': result=self.bpy.ops.wm.fbx_import(filepath=str(path))
            elif suffix=='.obj': result=self.bpy.ops.wm.obj_import(filepath=str(path))
            else: raise HarnessError('INVALID_ARGUMENT','file must be GLB/GLTF, FBX or OBJ')
        except HarnessError: raise
        except Exception as exc: raise HarnessError('IMPORT_FAILED',f'Blender could not import {suffix}') from exc
        if result != {'FINISHED'}: raise HarnessError('IMPORT_FAILED','import operator did not finish')
        created=sorted((obj for obj in self.bpy.data.objects if obj not in before),key=lambda obj:obj.name)
        return {'changedObjects':[obj.name for obj in created], 'result':{'path':str(path),'objects':[self.objects.receipt(obj) for obj in created]}}

    def library(self, arguments):
        path=self._path(arguments.get('path'))
        if path.suffix.lower() != '.blend': raise HarnessError('INVALID_ARGUMENT','library path must be a .blend file')
        kind=str(arguments.get('dataType','OBJECT')).upper(); names=arguments.get('names'); link=arguments.get('link',False)
        if kind not in {'OBJECT','COLLECTION'} or not isinstance(names,list) or not names or any(not isinstance(n,str) or not n for n in names):
            raise HarnessError('INVALID_ARGUMENT','dataType and non-empty names are required')
        if type(link) is not bool: raise HarnessError('INVALID_ARGUMENT','link must be boolean')
        with self.bpy.data.libraries.load(str(path),link=link) as (source,target):
            available=source.objects if kind=='OBJECT' else source.collections
            missing=sorted(set(names)-set(available))
            if missing: raise HarnessError('ASSET_NOT_FOUND',f'library data not found: {missing}')
            if kind=='OBJECT': target.objects=list(names)
            else: target.collections=list(names)
        loaded=target.objects if kind=='OBJECT' else target.collections
        if kind=='OBJECT':
            for obj in loaded:
                if not obj.users_collection: self.bpy.context.scene.collection.objects.link(obj)
            receipts=[self.objects.receipt(obj) for obj in loaded]
        else:
            for collection in loaded:
                if not collection.users_scene: self.bpy.context.scene.collection.children.link(collection)
            receipts=[{'name':collection.name,'type':'COLLECTION'} for collection in loaded]
        return {'changedObjects':[item['name'] for item in receipts], 'result':{'path':str(path),'linked':link,'items':receipts}}

    def pack_resources(self,_arguments):
        result=self.bpy.ops.file.pack_all()
        if result!={'FINISHED'}:raise HarnessError('OPERATION_FAILED','resource packing did not finish')
        packed=sorted(image.name for image in self.bpy.data.images if getattr(image,'packed_file',None))
        return {'changedObjects':[],'result':{'packedImages':packed,'count':len(packed)}}

    def make_paths_relative(self,_arguments):
        result=self.bpy.ops.file.make_paths_relative()
        if result!={'FINISHED'}:raise HarnessError('OPERATION_FAILED','path conversion did not finish')
        return {'changedObjects':[],'result':{'relative':True}}

    def dependencies(self, arguments):
        """List all external file dependencies in the current project."""
        include_packed = bool(arguments.get('includePacked', False))
        # Determine project directory from the current blend file
        blend_path = Path(self.bpy.data.filepath) if self.bpy.data.filepath else Path.cwd()
        project_dir = blend_path.parent if blend_path.suffix == '.blend' else blend_path
        manifest = generate_manifest(self.bpy, project_dir)
        if not include_packed:
            # Filter out packed files (they don't need to be listed as external deps)
            manifest['dependencies'] = [
                d for d in manifest['dependencies']
                if d['accessible'] or d.get('warning')
            ]
            # Recompute summary
            by_kind = {}
            accessible = 0
            inaccessible = 0
            for dep in manifest['dependencies']:
                kind = dep['kind']
                by_kind[kind] = by_kind.get(kind, 0) + 1
                if dep['accessible']:
                    accessible += 1
                else:
                    inaccessible += 1
            manifest['summary'] = {
                'total': len(manifest['dependencies']),
                'byKind': by_kind,
                'accessible': accessible,
                'inaccessible': inaccessible,
            }
        return {'changedObjects': [], 'result': manifest}

    def validate_portability(self, arguments):
        """Validate that the project can be packaged to the target directory."""
        target_dir = arguments.get('targetDirectory')
        if not target_dir or not isinstance(target_dir, str):
            raise HarnessError('INVALID_ARGUMENT', 'targetDirectory must be a non-empty string')
        target = Path(target_dir)
        blend_path = Path(self.bpy.data.filepath) if self.bpy.data.filepath else Path.cwd()
        project_dir = blend_path.parent if blend_path.suffix == '.blend' else blend_path
        result = validate_portability(self.bpy, target, project_dir)
        return {'changedObjects': [], 'result': result}

    def package_project(self, arguments):
        """Package the project into a self-contained directory.

        Writes only into a new directory; never modifies the active project.
        Refuses to overwrite an existing directory.
        """
        target_dir = arguments.get('targetDirectory')
        if not target_dir or not isinstance(target_dir, str):
            raise HarnessError('INVALID_ARGUMENT', 'targetDirectory must be a non-empty string')
        include_caches = bool(arguments.get('includeCaches', False))
        include_proxies = bool(arguments.get('includeProxies', False))
        target = Path(target_dir)
        blend_path = Path(self.bpy.data.filepath) if self.bpy.data.filepath else Path.cwd()
        if blend_path.suffix != '.blend':
            raise HarnessError('INVALID_ARGUMENT', 'project must be saved as a .blend file before packaging')
        source_project = blend_path
        receipt = package_project(
            self.bpy,
            source_project,
            target,
            include_caches=include_caches,
            include_proxies=include_proxies,
        )
        return {'changedObjects': [], 'result': receipt}
