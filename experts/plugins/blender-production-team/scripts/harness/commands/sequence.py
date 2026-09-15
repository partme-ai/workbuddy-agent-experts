"""Versioned VSE source, timing, transition, speed, audio and output controls."""

from pathlib import Path

from ..errors import HarnessError
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
