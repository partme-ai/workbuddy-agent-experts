"""Render engine/device, output, pass and color-management configuration."""
from ..errors import HarnessError
from .validation import finite_number


PASS_PROPERTIES={'Z':'use_pass_z','NORMAL':'use_pass_normal','DIFFUSE_COLOR':'use_pass_diffuse_color',
 'EMISSION':'use_pass_emit','MIST':'use_pass_mist','CRYPTO_OBJECT':'use_pass_cryptomatte_object'}


class RenderCommands:
    def __init__(self,bpy_module):self.bpy=bpy_module
    def _devices(self):
        devices=[]
        try:
            addon=self.bpy.context.preferences.addons.get('cycles')
            if addon:
                addon.preferences.get_devices()
                for group in addon.preferences.get_devices():
                    for device in group:
                        devices.append({'name':device.name,'type':device.type,'available':bool(device.use)})
        except Exception:pass
        return devices
    def configure(self,args):
        scene=self.bpy.context.scene;requested=str(args.get('engine','EEVEE')).upper()
        available={item.identifier for item in scene.render.bl_rna.properties['engine'].enum_items}
        if requested in {'EEVEE','BLENDER_EEVEE','BLENDER_EEVEE_NEXT'}:
            engine=next((value for value in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE') if value in available),None)
            if engine is None:raise HarnessError('CAPABILITY_UNAVAILABLE','Eevee is unavailable')
        elif requested=='CYCLES':engine='CYCLES'
        else:raise HarnessError('INVALID_ARGUMENT','unsupported render engine')
        width=args.get('width',scene.render.resolution_x);height=args.get('height',scene.render.resolution_y);samples=args.get('samples',64)
        if any(type(v) is not int or v<1 for v in (width,height,samples)) or width>16384 or height>16384 or samples>4096:raise HarnessError('INVALID_ARGUMENT','render dimensions/samples exceed safe bounds')
        transparent=args.get('transparent',False);fallback=args.get('allowCpuFallback',True)
        if type(transparent) is not bool or type(fallback) is not bool:raise HarnessError('INVALID_ARGUMENT','render flags must be boolean')
        device=str(args.get('device','AUTO')).upper();devices=self._devices();gpu=any(d['type']!='CPU' and d['available'] for d in devices)
        if device not in {'AUTO','CPU','GPU'}:raise HarnessError('INVALID_ARGUMENT','device must be AUTO, CPU or GPU')
        if device=='GPU' and not gpu:
            if not fallback:raise HarnessError('CAPABILITY_UNAVAILABLE','no enabled Cycles GPU device')
            device='CPU'
        scene.render.engine=engine;scene.render.resolution_x=width;scene.render.resolution_y=height;scene.render.resolution_percentage=100;scene.render.film_transparent=transparent
        if engine=='CYCLES':scene.cycles.samples=samples;scene.cycles.device='GPU' if device=='GPU' or (device=='AUTO' and gpu) else 'CPU'
        else:scene.render.engine=engine
        scene.view_settings.look=str(args.get('look',scene.view_settings.look));scene.view_settings.exposure=finite_number(args.get('exposure',scene.view_settings.exposure),'exposure')
        return {'changedObjects':[],'result':{'engine':scene.render.engine,'device':scene.cycles.device if engine=='CYCLES' else 'GPU/CPU managed by Eevee',
          'devices':devices,'resolution':[width,height],'samples':samples,'transparent':transparent,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure}}
    def configure_passes(self,args):
        layer_name=args.get('viewLayer',self.bpy.context.view_layer.name);layer=self.bpy.context.scene.view_layers.get(layer_name)
        if layer is None:raise HarnessError('INVALID_ARGUMENT','view layer was not found')
        passes=args.get('passes')
        if not isinstance(passes,list) or any(str(name).upper() not in PASS_PROPERTIES for name in passes):raise HarnessError('INVALID_ARGUMENT','passes contain unsupported names')
        enabled={str(name).upper() for name in passes}
        for name,prop in PASS_PROPERTIES.items():setattr(layer,prop,name in enabled)
        return {'changedObjects':[],'result':{'viewLayer':layer.name,'passes':sorted(enabled)}}
    def create_view_layer(self,args):
        name=args.get('name')
        if not isinstance(name,str) or not name:raise HarnessError('INVALID_ARGUMENT','view layer name is required')
        if self.bpy.context.scene.view_layers.get(name):raise HarnessError('NAME_COLLISION','view layer already exists')
        layer=self.bpy.context.scene.view_layers.new(name)
        return {'changedObjects':[],'result':{'name':layer.name}}
    def inspect(self,_args):
        scene=self.bpy.context.scene;layer=self.bpy.context.view_layer
        return {'changedObjects':[],'result':{'engine':scene.render.engine,'resolution':[scene.render.resolution_x,scene.render.resolution_y],
          'transparent':scene.render.film_transparent,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,
          'passes':[name for name,prop in PASS_PROPERTIES.items() if getattr(layer,prop)],'devices':self._devices()}}
