"""Versioned VSE source, timing, transition, speed, audio, output and post-production controls."""

from pathlib import Path

from ..errors import HarnessError
from ..path_policy import PathPolicy
from .validation import finite_number, require_name


class SequenceCommands:
    TRANSITIONS = {"CROSS", "GAMMA_CROSS", "WIPE", "SOUND_CROSSFADE"}

    def __init__(self, bpy_module, asset_policy=None):
        self.bpy = bpy_module
        self.policy = asset_policy

    def _editor(self):
        return self.bpy.context.scene.sequence_editor or self.bpy.context.scene.sequence_editor_create()

    def _strip(self, name):
        strip = self._editor().strips.get(require_name(name))
        if strip is None:
            raise HarnessError("STRIP_NOT_FOUND", "sequence strip was not found")
        return strip

    def _path(self, value):
        if self.policy is None:
            raise HarnessError("ASSET_NOT_AUTHORIZED", "sequence media requires an approved asset root")
        return self.policy.require_file(value)

    def _effect(self, name, effect_type, channel, start, end, input1=None, input2=None):
        editor = self._editor()
        parameters = {item.identifier for item in editor.strips.bl_rna.functions["new_effect"].parameters}
        if "length" in parameters:
            kwargs = {"name": name, "type": effect_type, "channel": channel,
                      "frame_start": start, "length": end - start}
            if input1 is not None:
                kwargs["input1"] = input1
            if input2 is not None:
                kwargs["input2"] = input2
            return editor.strips.new_effect(**kwargs)
        return editor.sequences.new_effect(name, effect_type, channel, start, end, seq1=input1, seq2=input2)

    @staticmethod
    def _receipt(strip, **extra):
        return {"name": strip.name, "type": strip.type, "channel": strip.channel,
                "frameStart": strip.frame_final_start, "frameEnd": strip.frame_final_end} | extra

    def add(self, args):
        editor = self._editor()
        kind = str(args.get("type", "")).upper()
        name = require_name(args.get("name"))
        channel, start = args.get("channel"), args.get("frameStart")
        if editor.strips.get(name):
            raise HarnessError("NAME_COLLISION", "strip already exists")
        if type(channel) is not int or channel < 1 or type(start) is not int:
            raise HarnessError("INVALID_ARGUMENT", "channel/frameStart is invalid")
        extra = {}
        if kind == "MOVIE":
            strip = editor.strips.new_movie(name, str(self._path(args.get("path"))), channel, start)
        elif kind == "SOUND":
            strip = editor.strips.new_sound(name, str(self._path(args.get("path"))), channel, start)
        elif kind == "IMAGE":
            strip = editor.strips.new_image(name, str(self._path(args.get("path"))), channel, start)
        elif kind == "IMAGE_SEQUENCE":
            values = args.get("paths")
            if not isinstance(values, list) or not values:
                raise HarnessError("INVALID_ARGUMENT", "paths must contain at least one image")
            paths = [self._path(value) for value in values]
            if len({path.parent for path in paths}) != 1:
                raise HarnessError("INVALID_ARGUMENT", "image sequence files must share one directory")
            strip = editor.strips.new_image(name, str(paths[0]), channel, start)
            for path in paths[1:]:
                strip.elements.append(path.name)
            strip.frame_final_duration = len(paths)
            extra["elements"] = len(paths)
        elif kind == "SCENE":
            scene_name = require_name(args.get("scene"))
            scene = self.bpy.data.scenes.get(scene_name)
            if scene is None:
                raise HarnessError("SCENE_NOT_FOUND", "source scene was not found")
            strip = editor.strips.new_scene(name, scene, channel, start)
            extra["scene"] = scene.name if hasattr(scene, "name") else scene_name
        elif kind == "TEXT":
            text = args.get("text")
            duration = args.get("duration")
            if not isinstance(text, str) or not text or type(duration) is not int or duration < 1:
                raise HarnessError("INVALID_ARGUMENT", "TEXT requires non-empty text and positive duration")
            strip = self._effect(name, "TEXT", channel, start, start + duration)
            strip.text = text
            if "fontSize" in args:
                strip.font_size = finite_number(args["fontSize"], "fontSize", positive=True)
            extra["text"] = text
        else:
            raise HarnessError("INVALID_ARGUMENT", "unsupported sequence source type")
        duration = args.get("duration")
        if duration is not None and kind != "TEXT":
            if type(duration) is not int or duration < 1:
                editor.strips.remove(strip)
                raise HarnessError("INVALID_ARGUMENT", "duration must be positive")
            strip.frame_final_duration = duration
        return {"changedObjects": [], "result": self._receipt(strip, **extra)}

    def trim(self, args):
        strip = self._strip(args.get("name"))
        start = args.get("frameStart", strip.frame_final_start)
        end = args.get("frameEnd", strip.frame_final_end)
        if type(start) is not int or type(end) is not int or start >= end:
            raise HarnessError("INVALID_ARGUMENT", "trim range is invalid")
        strip.frame_final_start = start
        strip.frame_final_end = end
        return {"changedObjects": [], "result": self._receipt(strip)}

    def move(self, args):
        strip = self._strip(args.get("name"))
        start, channel = args.get("frameStart"), args.get("channel", strip.channel)
        if type(start) is not int or type(channel) is not int or channel < 1:
            raise HarnessError("INVALID_ARGUMENT", "move frame/channel is invalid")
        strip.frame_start += start - strip.frame_final_start
        strip.channel = channel
        return {"changedObjects": [], "result": self._receipt(strip)}

    def transition(self, args):
        first, second = self._strip(args.get("first")), self._strip(args.get("second"))
        name, channel = require_name(args.get("name")), args.get("channel")
        transition_type = str(args.get("transitionType", "CROSS")).upper()
        start, end = max(first.frame_final_start, second.frame_final_start), min(first.frame_final_end, second.frame_final_end)
        if start >= end or type(channel) is not int or channel < 1:
            raise HarnessError("INVALID_ARGUMENT", "strips must overlap and channel is required")
        if transition_type not in self.TRANSITIONS:
            raise HarnessError("INVALID_ARGUMENT", "unsupported transitionType")
        if self._editor().strips.get(name):
            raise HarnessError("NAME_COLLISION", "strip already exists")
        if transition_type == "SOUND_CROSSFADE" and {first.type, second.type} != {"SOUND"}:
            raise HarnessError("INVALID_ARGUMENT", "SOUND_CROSSFADE requires two sound strips")
        if transition_type == "SOUND_CROSSFADE":
            first_volume, second_volume = first.volume, second.volume
            first.volume = first_volume
            first.keyframe_insert(data_path="volume", frame=start)
            first.volume = 0
            first.keyframe_insert(data_path="volume", frame=end)
            second.volume = 0
            second.keyframe_insert(data_path="volume", frame=start)
            second.volume = second_volume
            second.keyframe_insert(data_path="volume", frame=end)
            return {"changedObjects": [], "result": {"name": name, "type": transition_type,
                    "frameStart": start, "frameEnd": end, "first": first.name, "second": second.name,
                    "createsStrip": False}}
        strip = self._effect(name, transition_type, channel, start, end, first, second)
        return {"changedObjects": [], "result": self._receipt(strip)}

    def set_speed(self, args):
        source = self._strip(args.get("source"))
        name, channel = require_name(args.get("name")), args.get("channel")
        factor = finite_number(args.get("factor"), "factor", positive=True)
        if type(channel) is not int or channel < 1 or factor > 100:
            raise HarnessError("INVALID_ARGUMENT", "speed channel/factor is invalid")
        if self._editor().strips.get(name):
            raise HarnessError("NAME_COLLISION", "strip already exists")
        strip = self._effect(name, "SPEED", channel, source.frame_final_start, source.frame_final_end, source)
        if hasattr(strip, "speed_control"):
            strip.speed_control = "MULTIPLY"
        strip.speed_factor = factor
        if hasattr(strip, "use_frame_interpolate"):
            strip.use_frame_interpolate = bool(args.get("interpolate", False))
        return {"changedObjects": [], "result": self._receipt(strip, source=source.name, factor=factor)}

    def set_volume(self, args):
        strip = self._strip(args.get("name"))
        volume = finite_number(args.get("volume"), "volume", minimum=0)
        if not hasattr(strip, "volume"):
            raise HarnessError("INVALID_ARGUMENT", "strip has no volume")
        strip.volume = volume
        return {"changedObjects": [], "result": {"name": strip.name, "volume": strip.volume}}

    def keyframe_volume(self, args):
        strip = self._strip(args.get("name"))
        frame, volume = args.get("frame"), finite_number(args.get("volume"), "volume", minimum=0)
        if type(frame) is not int or not hasattr(strip, "volume"):
            raise HarnessError("INVALID_ARGUMENT", "sound volume keyframe is invalid")
        strip.volume = volume
        strip.keyframe_insert(data_path="volume", frame=frame)
        return {"changedObjects": [], "result": {"name": strip.name, "frame": frame, "volume": volume}}

    def add_compositor_modifier(self,args):
        strip=self._strip(args.get('strip'));name=require_name(args.get('name'));group_name=require_name(args.get('groupName'))
        group=self.bpy.data.node_groups.get(group_name)
        if group is None or getattr(group,'bl_idname',None)!='CompositorNodeTree':
            raise HarnessError('NODE_NOT_FOUND','compositor node group was not found')
        if strip.modifiers.get(name):raise HarnessError('NAME_COLLISION','strip modifier already exists')
        modifier=strip.modifiers.new(name,'COMPOSITOR');modifier.node_group=group
        return {'changedObjects':[],'result':{'strip':strip.name,'name':modifier.name,'type':modifier.type,'groupName':group.name}}

    def configure_output(self, args):
        scene = self.bpy.context.scene
        start, end = args.get("frameStart"), args.get("frameEnd")
        width, height, fps = args.get("width", 1280), args.get("height", 720), args.get("fps", 24)
        if any(type(value) is not int for value in (start, end, width, height, fps)) or start > end or min(width, height, fps) < 1:
            raise HarnessError("INVALID_ARGUMENT", "output settings are invalid")
        scene.frame_start, scene.frame_end = start, end
        scene.render.resolution_x, scene.render.resolution_y = width, height
        scene.render.resolution_percentage, scene.render.fps = 100, fps
        return {"changedObjects": [], "result": {"frameStart": start, "frameEnd": end,
                "resolution": [width, height], "fps": fps}}

    def inspect(self, _args):
        editor = self.bpy.context.scene.sequence_editor
        strips = [] if editor is None else [self._receipt(strip) for strip in editor.strips]
        return {"changedObjects": [], "result": {"strips": strips}}

    # -------------------------------------------------------------------
    # Post-production: split, proxy, modifier, color grade
    # -------------------------------------------------------------------

    # VSE modifier types: derived from Blender 5.2.1 live enum at
    # StripModifiers.new(type=...) which accepts:
    # BRIGHT_CONTRAST, COLOR_BALANCE, COMPOSITOR, CURVES, HUE_CORRECT,
    # MASK, TONEMAP, WHITE_BALANCE, SOUND_EQUALIZER, PITCH, ECHO
    _MODIFIER_WHITELIST: dict[str, str] = {
        'Color Balance': 'COLOR_BALANCE',
        'Brightness/Contrast': 'BRIGHT_CONTRAST',
        'Hue Correct': 'HUE_CORRECT',
        'Mask': 'MASK',
        'White Balance': 'WHITE_BALANCE',
        'Tonemap': 'TONEMAP',
        'Curves': 'CURVES',
    }


    def _resolve_modifier_type(self, name: str) -> str:
        """Resolve a plan-level modifier type name to a Blender enum value."""
        if name in self._MODIFIER_WHITELIST:
            return self._MODIFIER_WHITELIST[name]
        # Allow direct Blender enum if it matches the live set
        allowed = {'BRIGHT_CONTRAST', 'COLOR_BALANCE', 'COMPOSITOR', 'CURVES',
                    'HUE_CORRECT', 'MASK', 'TONEMAP', 'WHITE_BALANCE',
                    'SOUND_EQUALIZER', 'PITCH', 'ECHO'}
        if name in allowed:
            return name
        raise HarnessError('INVALID_ARGUMENT', f'modifier type is not whitelisted: {name}')

    def split(self, args):
        """Split a strip at a frame into left and right strips.

        The original strip becomes the left strip (renamed to leftName).
        A new strip is created for the right portion.
        """
        name = require_name(args.get('name'))
        frame = args.get('frame')
        left_name = require_name(args.get('leftName'))
        right_name = require_name(args.get('rightName'))
        if type(frame) is not int:
            raise HarnessError('INVALID_ARGUMENT', 'frame must be an integer')
        strip = self._strip(name)
        if frame <= strip.frame_final_start or frame >= strip.frame_final_end:
            raise HarnessError('INVALID_ARGUMENT',
                               'frame must be strictly inside the strip range')
        editor = self._editor()
        if editor.strips.get(left_name) and left_name != name:
            raise HarnessError('NAME_COLLISION', f'left strip name already exists: {left_name}')
        if editor.strips.get(right_name):
            raise HarnessError('NAME_COLLISION', f'right strip name already exists: {right_name}')
        # Compute the split
        orig_start = strip.frame_final_start
        orig_end = strip.frame_final_end
        # Create the right strip based on strip type
        right_strip = None
        strip_type = strip.type
        if strip_type == 'MOVIE':
            filepath = strip.filepath
            channel = strip.channel
            right_strip = editor.strips.new_movie(right_name, filepath, channel, frame)
            right_strip.frame_final_start = frame
            right_strip.frame_final_end = orig_end
        elif strip_type == 'SOUND':
            filepath = strip.filepath
            channel = strip.channel
            right_strip = editor.strips.new_sound(right_name, filepath, channel, frame)
            right_strip.frame_final_start = frame
            right_strip.frame_final_end = orig_end
        elif strip_type == 'IMAGE':
            filepath = strip.directory
            channel = strip.channel
            right_strip = editor.strips.new_image(right_name, filepath, channel, frame)
            # Copy elements
            for elem in strip.elements[1:]:
                right_strip.elements.append(elem.filename)
            right_strip.frame_final_start = frame
            right_strip.frame_final_end = orig_end
        elif strip_type == 'SCENE':
            channel = strip.channel
            right_strip = editor.strips.new_scene(right_name, strip.scene, channel, frame)
            right_strip.frame_final_start = frame
            right_strip.frame_final_end = orig_end
        else:
            # For effect strips and other types, use frame offset approach:
            # Trim original to [start, frame), use frame_offset on right copy
            raise HarnessError('INVALID_ARGUMENT',
                               f'split is not supported for strip type: {strip_type}')
        # Trim the original (left) strip
        strip.frame_final_start = orig_start
        strip.frame_final_end = frame
        # Rename left strip if needed
        if left_name != name:
            strip.name = left_name
        return {'changedObjects': [], 'result': {
            'left': self._receipt(strip),
            'right': self._receipt(right_strip),
        }}

    def configure_proxy(self, args):
        """Configure proxy settings for a strip.

        Parameters
        ----------
        name : str
            Strip name.
        sizes : list[int]
            Proxy resolution sizes (subset of [25, 50, 75, 100]).
        directory : str
            Directory to store proxy files.  Must be inside an authorized root.
        """
        name = require_name(args.get('name'))
        sizes = args.get('sizes')
        directory = args.get('directory')
        if not isinstance(sizes, list) or not sizes:
            raise HarnessError('INVALID_ARGUMENT', 'sizes must be a non-empty list')
        allowed_sizes = {25, 50, 75, 100}
        for s in sizes:
            if type(s) is not int or s not in allowed_sizes:
                raise HarnessError('INVALID_ARGUMENT',
                                   f'invalid proxy size {s}; allowed: {sorted(allowed_sizes)}')
        # Validate directory against authorized roots (reuse compositor pattern)
        if self.policy is None:
            raise HarnessError('OUTPUT_NOT_AUTHORIZED',
                               'proxy configuration requires an approved output root')
        dir_path = Path(directory)
        if dir_path.is_symlink():
            raise HarnessError('OUTPUT_NOT_AUTHORIZED', 'proxy directory must not be a symlink')
        resolved = dir_path.resolve()
        # Check against policy roots (same as compositor._output_directory)
        approved = False
        for root in self.policy.roots:
            try:
                resolved.relative_to(root)
                approved = True
                break
            except ValueError:
                continue
        if not approved:
            raise HarnessError('OUTPUT_NOT_AUTHORIZED',
                               f'proxy directory is outside authorized roots: {resolved}')
        # Create directory
        resolved.mkdir(parents=True, exist_ok=True)
        strip = self._strip(name)
        strip.use_proxy = True
        proxy = strip.proxy
        proxy.directory = str(resolved)
        proxy.use_proxy_custom_directory = True
        for s in (25, 50, 75, 100):
            attr = f'build_{s}'
            setattr(proxy, attr, s in sizes)
        return {'changedObjects': [], 'result': {
            'name': strip.name, 'directory': str(resolved),
            'sizes': sorted(sizes),
        }}

    def add_modifier(self, args):
        """Add a VSE modifier to a strip.

        Parameters
        ----------
        name : str
            Strip name.
        modifierType : str
            Whitelisted modifier type name.
        settings : dict, optional
            Additional settings to apply to the modifier.
        """
        name = require_name(args.get('name'))
        modifier_type_input = require_name(args.get('modifierType'))
        settings = args.get('settings', {})
        mod_type = self._resolve_modifier_type(modifier_type_input)
        strip = self._strip(name)
        mod_name = modifier_type_input
        if strip.modifiers.get(mod_name):
            raise HarnessError('NAME_COLLISION', f'modifier already exists: {mod_name}')
        modifier = strip.modifiers.new(mod_name, mod_type)
        # Apply settings if provided
        if isinstance(settings, dict):
            for key, value in settings.items():
                if hasattr(modifier, key):
                    setattr(modifier, key, value)
        return {'changedObjects': [], 'result': {
            'strip': strip.name, 'modifierName': modifier.name,
            'modifierType': modifier.type,
        }}

    def color_grade(self, args):
        """Apply color grading via a Color Balance modifier.

        Parameters
        ----------
        name : str
            Strip name.
        lift : list[float]
            RGB lift values (default [1, 1, 1] = identity).
        gamma : list[float]
            RGB gamma values (default [1, 1, 1] = identity).
        gain : list[float]
            RGB gain values (default [1, 1, 1] = identity).
        """
        name = require_name(args.get('name'))
        lift = args.get('lift', [1.0, 1.0, 1.0])
        gamma = args.get('gamma', [1.0, 1.0, 1.0])
        gain = args.get('gain', [1.0, 1.0, 1.0])
        for label, values in (('lift', lift), ('gamma', gamma), ('gain', gain)):
            if not isinstance(values, (list, tuple)) or len(values) != 3:
                raise HarnessError('INVALID_ARGUMENT', f'{label} must contain three numbers')
            for v in values:
                if isinstance(v, bool) or not isinstance(v, (int, float)):
                    raise HarnessError('INVALID_ARGUMENT', f'{label} values must be numbers')
        strip = self._strip(name)
        # Find or create color balance modifier
        mod = None
        for m in strip.modifiers:
            if m.type == 'COLOR_BALANCE':
                mod = m
                break
        if mod is None:
            mod = strip.modifiers.new('Color Grade', 'COLOR_BALANCE')
        mod.color_balance.correction_method = 'LIFT_GAMMA_GAIN'
        mod.color_balance.lift = tuple(float(v) for v in lift)
        mod.color_balance.gamma = tuple(float(v) for v in gamma)
        mod.color_balance.gain = tuple(float(v) for v in gain)
        return {'changedObjects': [], 'result': {
            'strip': strip.name, 'modifierName': mod.name,
            'lift': list(mod.color_balance.lift),
            'gamma': list(mod.color_balance.gamma),
            'gain': list(mod.color_balance.gain),
        }}

    def set_transform(self, args):
        """Set transform properties on a VSE strip.

        Transform is a strip property (strip.transform.*), not a modifier
        or effect type.  This is the whitelisted operation for positional,
        scale and rotation adjustments in the VSE.

        Parameters
        ----------
        name : str
            Strip name.
        offset_x : float, optional
            Horizontal offset in pixels (default 0).
        offset_y : float, optional
            Vertical offset in pixels (default 0).
        scale_x : float, optional
            Horizontal scale factor (default 1.0).
        scale_y : float, optional
            Vertical scale factor (default 1.0).
        rotation : float, optional
            Rotation in radians (default 0).
        """
        name = require_name(args.get('name'))
        strip = self._strip(name)
        if not hasattr(strip, 'transform'):
            raise HarnessError('INVALID_ARGUMENT',
                               'strip does not support transform properties')
        xform = strip.transform
        offset_x = args.get('offset_x', 0.0)
        offset_y = args.get('offset_y', 0.0)
        scale_x = args.get('scale_x', 1.0)
        scale_y = args.get('scale_y', 1.0)
        rotation = args.get('rotation', 0.0)
        for label, value in (('offset_x', offset_x), ('offset_y', offset_y),
                             ('scale_x', scale_x), ('scale_y', scale_y),
                             ('rotation', rotation)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise HarnessError('INVALID_ARGUMENT', f'{label} must be a number')
        xform.offset_x = float(offset_x)
        xform.offset_y = float(offset_y)
        xform.scale_x = float(scale_x)
        xform.scale_y = float(scale_y)
        xform.rotation = float(rotation)
        return {'changedObjects': [], 'result': {
            'strip': strip.name,
            'offset_x': xform.offset_x, 'offset_y': xform.offset_y,
            'scale_x': xform.scale_x, 'scale_y': xform.scale_y,
            'rotation': xform.rotation,
        }}

    def set_crop(self, args):
        """Set crop properties on a VSE strip.

        Crop is a strip property (strip.crop.*), not a modifier
        or effect type.  This is the whitelisted operation for
        adjusting the visible region of a VSE strip.

        Parameters
        ----------
        name : str
            Strip name.
        min_x : int, optional
            Pixels to crop from the left (default 0).
        max_x : int, optional
            Pixels to crop from the right (default 0).
        min_y : int, optional
            Pixels to crop from the bottom (default 0).
        max_y : int, optional
            Pixels to crop from the top (default 0).
        """
        name = require_name(args.get('name'))
        strip = self._strip(name)
        if not hasattr(strip, 'crop'):
            raise HarnessError('INVALID_ARGUMENT',
                               'strip does not support crop properties')
        min_x = args.get('min_x', 0)
        max_x = args.get('max_x', 0)
        min_y = args.get('min_y', 0)
        max_y = args.get('max_y', 0)
        for label, value in (('min_x', min_x), ('max_x', max_x),
                             ('min_y', min_y), ('max_y', max_y)):
            if type(value) is not int or value < 0:
                raise HarnessError('INVALID_ARGUMENT', f'{label} must be a non-negative integer')
        crop = strip.crop
        crop.min_x = min_x
        crop.max_x = max_x
        crop.min_y = min_y
        crop.max_y = max_y
        return {'changedObjects': [], 'result': {
            'strip': strip.name,
            'min_x': crop.min_x, 'max_x': crop.max_x,
            'min_y': crop.min_y, 'max_y': crop.max_y,
        }}
