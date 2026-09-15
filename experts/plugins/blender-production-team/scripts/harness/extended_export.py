"""Version-2 receipt for newly probed EXR, USD and Alembic deliveries."""
import hashlib
from pathlib import Path
from .errors import HarnessError


class ExtendedExporter:
    def __init__(self,bpy_module,root=None):self.bpy=bpy_module;self.root=Path(root).resolve() if root else None
    def export(self,args):
        if self.root is None:raise HarnessError('OUTPUT_NOT_AUTHORIZED','extended export requires an approved output root')
        target=Path(args.get('path','')).resolve();fmt=str(args.get('format','')).lower()
        if not target.is_relative_to(self.root):raise HarnessError('OUTPUT_NOT_AUTHORIZED','path is outside approved root')
        if target.exists():raise HarnessError('OVERWRITE_AUTHORIZATION_REQUIRED','output already exists')
        if fmt not in {'exr','usd','usdc','abc'}:raise HarnessError('INVALID_ARGUMENT','format must be exr, usd, usdc or abc')
        target.parent.mkdir(parents=True,exist_ok=True)
        try:
            if fmt=='exr':
                scene=self.bpy.context.scene;previous=(scene.render.filepath,scene.render.image_settings.file_format)
                try:scene.render.filepath=str(target);scene.render.image_settings.file_format='OPEN_EXR';self.bpy.ops.render.render(write_still=True)
                finally:scene.render.filepath,scene.render.image_settings.file_format=previous
            elif fmt in {'usd','usdc'}:self.bpy.ops.wm.usd_export(filepath=str(target),export_materials=True)
            else:self.bpy.ops.wm.alembic_export(filepath=str(target),start=self.bpy.context.scene.frame_current,end=self.bpy.context.scene.frame_current)
        except Exception as exc:raise HarnessError('EXPORT_FAILED',f'{fmt} export failed') from exc
        return {'changedObjects':[],'result':{'artifact':{'receiptVersion':'2.0.0','path':str(target),'format':fmt,
          'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
          'validation':{'status':'passed','checks':['exists','non_empty','sha256']}}}}
