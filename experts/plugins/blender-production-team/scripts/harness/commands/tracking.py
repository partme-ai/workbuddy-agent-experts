"""Movie clip tracking data and foreground camera solve/setup."""
from ..errors import HarnessError
from .validation import finite_number,require_name


class TrackingCommands:
    def __init__(self,bpy_module,asset_policy=None):self.bpy=bpy_module;self.policy=asset_policy
    def _clip(self,name):
        clip=self.bpy.data.movieclips.get(require_name(name))
        if clip is None:raise HarnessError('CLIP_NOT_FOUND','movie clip was not found')
        return clip
    def load_clip(self,args):
        if self.policy is None:raise HarnessError('ASSET_NOT_AUTHORIZED','tracking media requires an approved asset root')
        path=self.policy.require_file(args.get('path'));name=require_name(args.get('name'))
        if self.bpy.data.movieclips.get(name):raise HarnessError('NAME_COLLISION','movie clip name exists')
        focal=args.get('focalLengthPixels')
        if focal is not None:focal=finite_number(focal,'focalLengthPixels',positive=True)
        clip=self.bpy.data.movieclips.load(str(path));clip.name=name
        if focal is not None:clip.tracking.camera.focal_length=focal
        return {'changedObjects':[],'result':{'name':clip.name,'path':str(path),'size':list(clip.size),'duration':clip.frame_duration}}
    def add_track(self,args):
        clip=self._clip(args.get('clip'));name=require_name(args.get('name'));markers=args.get('markers')
        if clip.tracking.tracks.get(name):raise HarnessError('NAME_COLLISION','track already exists')
        if not isinstance(markers,list) or len(markers)<1:raise HarnessError('INVALID_ARGUMENT','markers are required')
        parsed=[]
        for marker in markers:
            if not isinstance(marker,dict) or type(marker.get('frame')) is not int:raise HarnessError('INVALID_ARGUMENT','marker frame is invalid')
            co=marker.get('co')
            if not isinstance(co,(list,tuple)) or len(co)!=2:raise HarnessError('INVALID_ARGUMENT','marker co requires two values')
            co=[finite_number(v,'co') for v in co]
            if any(v<0 or v>1 for v in co):raise HarnessError('INVALID_ARGUMENT','marker co must be normalized')
            parsed.append((marker['frame'],co))
        track=clip.tracking.tracks.new(name=name)
        for frame,co in parsed:track.markers.insert_frame(frame,co=co)
        return {'changedObjects':[],'result':{'clip':clip.name,'track':track.name,'markers':len(parsed)}}
    def _context(self,clip):
        manager=getattr(self.bpy.context,'window_manager',None)
        for window in getattr(manager,'windows',()):
            for area in window.screen.areas:
                if area.type=='CLIP_EDITOR':
                    area.spaces.active.clip=clip
                    region=next((r for r in area.regions if r.type=='WINDOW'),None)
                    if region:return window,area,region
        raise HarnessError('FRONTEND_UNAVAILABLE','camera solve requires a foreground CLIP_EDITOR area')
    def solve_camera(self,args):
        clip=self._clip(args.get('clip'));key_a=args.get('keyframeA');key_b=args.get('keyframeB')
        if type(key_a) is not int or type(key_b) is not int or key_a>=key_b:raise HarnessError('INVALID_ARGUMENT','solve keyframes are invalid')
        tracking_object=clip.tracking.objects.active
        if hasattr(tracking_object,'keyframe_a'):
            tracking_object.keyframe_a=key_a;tracking_object.keyframe_b=key_b
        else:
            clip.tracking.settings.keyframe_a=key_a;clip.tracking.settings.keyframe_b=key_b
        window,area,region=self._context(clip)
        with self.bpy.context.temp_override(window=window,area=area,region=region,space_data=area.spaces.active):
            result=self.bpy.ops.clip.solve_camera()
        if result!={'FINISHED'}:raise HarnessError('SOLVE_FAILED','camera solve did not finish')
        error=getattr(clip.tracking.camera,'error',None)
        if error is None:error=clip.tracking.objects.active.reconstruction.average_error
        return {'changedObjects':[],'result':{'clip':clip.name,'reprojectionError':float(error),
          'keyframes':[key_a,key_b]}}
    def setup_scene(self,args):
        clip=self._clip(args.get('clip'));window,area,region=self._context(clip)
        with self.bpy.context.temp_override(window=window,area=area,region=region,space_data=area.spaces.active):result=self.bpy.ops.clip.setup_tracking_scene()
        if result!={'FINISHED'}:raise HarnessError('OPERATION_FAILED','tracking scene setup did not finish')
        return {'changedObjects':[],'result':{'clip':clip.name,'camera':getattr(self.bpy.context.scene.camera,'name',None)}}
    def inspect(self,args):
        clip=self._clip(args.get('clip'));tracks=[]
        for track in clip.tracking.tracks:
            tracks.append({'name':track.name,'markers':len(track.markers),'hasBundle':bool(track.has_bundle),'averageError':float(track.average_error)})
        error=getattr(clip.tracking.camera,'error',None)
        if error is None:error=clip.tracking.objects.active.reconstruction.average_error
        return {'changedObjects':[],'result':{'clip':clip.name,'size':list(clip.size),'duration':clip.frame_duration,
          'tracks':tracks,'cameraError':float(error)}}
