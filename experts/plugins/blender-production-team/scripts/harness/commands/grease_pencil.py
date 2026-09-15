"""Blender 5 Grease Pencil layers, materials, strokes, frames, modifiers and interpolation."""
from ..errors import HarnessError
from ..identity import ObjectResolver
from ..operation_context import OperationContext
from .validation import finite_number,require_name,vector3

# Easing functions for interpolation
_EASING_FUNCTIONS = {
    'LINEAR': lambda t: t,
    'EASE_IN': lambda t: t * t,
    'EASE_OUT': lambda t: 1.0 - (1.0 - t) * (1.0 - t),
    'EASE_IN_OUT': lambda t: 2.0 * t * t if t < 0.5 else 1.0 - 2.0 * (1.0 - t) * (1.0 - t),
    'BOUNCE': lambda t: _bounce_ease(t),
    'ELASTIC': lambda t: _elastic_ease(t),
}


def _bounce_ease(t):
    if t < 1 / 2.75:
        return 7.5625 * t * t
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375


def _elastic_ease(t):
    import math
    if t == 0 or t == 1:
        return t
    return -math.pow(2, 10 * (t - 1)) * math.sin((t - 1.1) * 5 * math.pi)


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

    def add_modifier(self, args):
        """Add a modifier to a Grease Pencil object.

        Parameters
        ----------
        objectId : str
            Object locator (type GREASEPENCIL).
        type : str
            The modifier type to add.  Validated at runtime against the
            modifier types Blender actually exposes for Grease Pencil
            objects.  Unknown types are rejected with INVALID_ARGUMENT.
        settings : dict, optional
            Initial modifier RNA properties to set after creation.

        Returns
        -------
        dict with the modifier name, type, and the list of valid types
        that were available at registration time.
        """
        oid = args.get('objectId')
        obj = self.objects.resolve(oid if isinstance(oid, dict) else {'objectId': oid}, required_type={'GREASEPENCIL'})
        mod_type = require_name(args.get('type'))

        # Discover valid GP modifier types at runtime from the
        # object.modifier_add operator's type enum (Blender 5.2 uses
        # the generic modifier_add, not a GP-specific operator).
        valid_types = set()
        try:
            op_rna = self.bpy.ops.object.modifier_add.get_rna_type()
            for prop in op_rna.properties:
                if prop.identifier == 'type':
                    for item in prop.enum_items_static:
                        if item.identifier.startswith('GREASE_PENCIL_'):
                            valid_types.add(item.identifier)
        except Exception:
            pass

        if not valid_types:
            raise HarnessError('OPERATION_FAILED', 'could not enumerate GP modifier types from Blender')

        # Accept both bare names (e.g. 'NOISE') and full identifiers
        # (e.g. 'GREASE_PENCIL_NOISE') for convenience.
        if mod_type in valid_types:
            resolved_type = mod_type
        elif f'GREASE_PENCIL_{mod_type}' in valid_types:
            resolved_type = f'GREASE_PENCIL_{mod_type}'
        else:
            raise HarnessError('INVALID_ARGUMENT',
                               f'GP modifier type {mod_type!r} is not valid; available: {sorted(valid_types)}')

        # Add the modifier
        with self.context.active_object(obj):
            result = self.bpy.ops.object.modifier_add(type=resolved_type)
            if result != {'FINISHED'}:
                raise HarnessError('OPERATION_FAILED', f'could not add GP modifier of type {resolved_type}')

        modifier = obj.modifiers[-1]

        # Apply settings if provided
        settings = args.get('settings')
        if settings is not None:
            if not isinstance(settings, dict):
                raise HarnessError('INVALID_ARGUMENT', 'settings must be an object')
            for key, value in settings.items():
                if not hasattr(modifier, key):
                    raise HarnessError('INVALID_ARGUMENT', f'modifier has no property {key!r}')
                setattr(modifier, key, value)

        return {'changedObjects': [obj.name], 'result': {
            'object': self.objects.receipt(obj),
            'modifierName': modifier.name,
            'modifierType': mod_type,
            'availableTypes': sorted(valid_types),
        }}

    def interpolate(self, args):
        """Fill frames between frameStart and frameEnd in a layer by interpolation.

        Parameters
        ----------
        objectId : str
            Object locator (type GREASEPENCIL).
        layer : str
            Name of the layer to interpolate.
        frameStart : int
            First frame of the interpolation range (inclusive).
        frameEnd : int
            Last frame of the interpolation range (inclusive).
        easing : str
            Easing function.  One of: LINEAR, EASE_IN, EASE_OUT,
            EASE_IN_OUT, BOUNCE, ELASTIC.

        The method finds the two keyframes that bracket or equal
        frameStart and frameEnd, then generates intermediate frames by
        blending the stroke point positions, radii, and opacities
        between the two bounding keyframes using the specified easing.

        Returns
        -------
        dict with:
            * ``layer`` (str) -- layer name
            * ``frameStart`` / ``frameEnd`` (int) -- the requested range
            * ``easing`` (str) -- easing used
            * ``createdFrames`` (list[int]) -- frame numbers that were
              newly created
            * ``interpolated`` (int) -- count of created frames
        """
        import math

        oid = args.get('objectId')
        obj = self.objects.resolve(oid if isinstance(oid, dict) else {'objectId': oid}, required_type={'GREASEPENCIL'})
        layer_name = require_name(args.get('layer'))
        layer = obj.data.layers.get(layer_name)
        if layer is None:
            raise HarnessError('INVALID_ARGUMENT', f'layer {layer_name!r} was not found')
        frame_start = args.get('frameStart')
        frame_end = args.get('frameEnd')
        if type(frame_start) is not int or type(frame_end) is not int or frame_start >= frame_end:
            raise HarnessError('INVALID_ARGUMENT', 'frameStart and frameEnd must be integers with frameStart < frameEnd')
        easing = str(args.get('easing', 'LINEAR')).upper()
        ease_fn = _EASING_FUNCTIONS.get(easing)
        if ease_fn is None:
            raise HarnessError('INVALID_ARGUMENT', f'easing must be one of {sorted(_EASING_FUNCTIONS)}')

        # Collect existing keyframes
        existing_frames = sorted(layer.frames, key=lambda f: f.frame_number)
        if len(existing_frames) < 2:
            raise HarnessError('INVALID_ARGUMENT', 'layer must have at least 2 keyframes for interpolation')

        # Find bounding keyframes for the range
        frame_numbers = [f.frame_number for f in existing_frames]
        # Find the keyframe at or before frame_start
        start_kf = None
        for kf in existing_frames:
            if kf.frame_number <= frame_start:
                start_kf = kf
        if start_kf is None:
            start_kf = existing_frames[0]

        # Find the keyframe at or after frame_end
        end_kf = None
        for kf in reversed(existing_frames):
            if kf.frame_number >= frame_end:
                end_kf = kf
        if end_kf is None:
            end_kf = existing_frames[-1]

        if start_kf is end_kf:
            raise HarnessError('INVALID_ARGUMENT', 'frameStart and frameEnd resolve to the same keyframe; need two distinct keyframes')

        start_frame_num = start_kf.frame_number
        end_frame_num = end_kf.frame_number
        start_drawing = start_kf.drawing
        end_drawing = end_kf.drawing

        # Read source data from start and end keyframes
        def read_strokes(drawing):
            strokes = []
            for stroke in drawing.strokes:
                pts = []
                for p in stroke.points:
                    pts.append({
                        'position': list(p.position),
                        'radius': float(p.radius),
                        'opacity': float(p.opacity),
                    })
                strokes.append({
                    'points': pts,
                    'cyclic': bool(stroke.cyclic),
                    'material_index': int(stroke.material_index),
                })
            return strokes

        start_strokes = read_strokes(start_drawing)
        end_strokes = read_strokes(end_drawing)

        # Create interpolated frames
        created_frames = []
        total_span = float(end_frame_num - start_frame_num)

        for target_frame in range(frame_start, frame_end + 1):
            if target_frame in frame_numbers:
                continue  # skip existing keyframes

            t = (target_frame - start_frame_num) / total_span
            t = max(0.0, min(1.0, t))
            eased_t = ease_fn(t)

            # Create new frame
            new_frame = layer.frames.new(target_frame)
            drawing = new_frame.drawing

            # Blend strokes -- use min stroke count between start and end
            num_strokes = min(len(start_strokes), len(end_strokes))
            if num_strokes > 0:
                drawing.add_strokes([min(len(start_strokes[s]['points']), len(end_strokes[s]['points']))
                                     for s in range(num_strokes)])

            for s_idx in range(num_strokes):
                stroke = drawing.strokes[s_idx]
                s_stroke = start_strokes[s_idx]
                e_stroke = end_strokes[s_idx]
                n_pts = min(len(s_stroke['points']), len(e_stroke['points']))
                stroke.cyclic = s_stroke['cyclic']
                stroke.material_index = s_stroke['material_index']
                for p_idx in range(n_pts):
                    sp = s_stroke['points'][p_idx]
                    ep = e_stroke['points'][p_idx]
                    blended_pos = [sp['position'][c] + (ep['position'][c] - sp['position'][c]) * eased_t
                                   for c in range(3)]
                    blended_radius = sp['radius'] + (ep['radius'] - sp['radius']) * eased_t
                    blended_opacity = sp['opacity'] + (ep['opacity'] - sp['opacity']) * eased_t
                    stroke.points[p_idx].position = blended_pos
                    stroke.points[p_idx].radius = blended_radius
                    stroke.points[p_idx].opacity = blended_opacity

            created_frames.append(target_frame)

        return {'changedObjects': [obj.name], 'result': {
            'object': self.objects.receipt(obj),
            'layer': layer_name,
            'frameStart': frame_start,
            'frameEnd': frame_end,
            'easing': easing,
            'createdFrames': created_frames,
            'interpolated': len(created_frames),
        }}

    def inspect(self,args):
        obj=self.objects.resolve(args,required_type={'GREASEPENCIL'});layers=[]
        for layer in obj.data.layers:
            layers.append({'name':layer.name,'frames':[{'frame':frame.frame_number,'strokes':len(frame.drawing.strokes),
              'points':sum(len(stroke.points) for stroke in frame.drawing.strokes)} for frame in layer.frames]})
        return {'changedObjects':[],'result':self.objects.receipt(obj)|{'layers':layers,'materials':[m.name for m in obj.data.materials]}}
