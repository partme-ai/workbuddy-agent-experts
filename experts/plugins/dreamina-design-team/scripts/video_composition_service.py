"""Closed, descriptor-safe composition of approved media."""
from __future__ import annotations
import hashlib,json,math,os,shutil,stat,tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any,Mapping,Sequence
TRANSITIONS=frozenset({"cut","crossfade","dip_to_black"}); FPS_VALUES=frozenset({24,25,30}); LAYOUTS=frozenset({"scale_pad","scale_crop"}); CARD_STYLES=frozenset({"dark","light","brand"})
class CompositionPlanError(RuntimeError): pass
def _num(v:Any,name:str,zero:bool=False)->float:
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 or (v==0 and not zero): raise CompositionPlanError(f"{name} is invalid")
    return float(v)
def _open_verified(path:Path,digest:str,size:int)->int:
    fd=None
    try:
        fd=os.open(path,os.O_RDONLY|getattr(os,"O_NOFOLLOW",0)); before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_uid!=os.getuid() or stat.S_IMODE(before.st_mode) not in {0o400,0o600} or before.st_size!=size: raise CompositionPlanError("artifact metadata is unsafe")
        h=hashlib.sha256()
        while chunk:=os.read(fd,1048576): h.update(chunk)
        after=os.fstat(fd); current=os.lstat(path)
        if h.hexdigest()!=digest or (before.st_dev,before.st_ino,before.st_size)!=(after.st_dev,after.st_ino,after.st_size) or (after.st_dev,after.st_ino)!=(current.st_dev,current.st_ino): raise CompositionPlanError("artifact identity changed")
        os.lseek(fd,0,os.SEEK_SET); return fd
    except Exception:
        if fd is not None: os.close(fd)
        raise
@dataclass(frozen=True)
class Input: role:str; source_path:Path; staged_path:Path; sha256:str; size_bytes:int; duration_seconds:float|None=None; options:Mapping[str,Any]|None=None
@dataclass(frozen=True)
class Transition: kind:str; duration_seconds:float
@dataclass(frozen=True)
class Card: text_path:Path; duration_seconds:float; style:str
@dataclass(frozen=True)
class CompositionPlan:
    clips:tuple[Input,...]; transitions:tuple[Transition,...]; media_inputs:tuple[Input,...]; width:int; height:int; fps:int; target_duration_seconds:float; audio_plan:Mapping[str,Any]|None; subtitle_mode:str; output_path:Path; staging_dir:Path; layout_mode:str; title_card:Card|None; end_card:Card|None
class VideoCompositionService:
    def __init__(self,media_adapter:Any,audio_plan_service:Any,private_render_root:Path,*,timeout_seconds:int=900)->None:
        self._adapter=media_adapter; self._audio=audio_plan_service; self._root=Path(private_render_root); self._timeout=timeout_seconds; s=self._root.lstat()
        if not stat.S_ISDIR(s.st_mode) or self._root.is_symlink() or s.st_uid!=os.getuid() or stat.S_IMODE(s.st_mode)!=0o700: raise CompositionPlanError("render root must be owned mode 0700")
    def _stage(self,raw:Mapping[str,Any],target:Path,role:str,duration:float|None=None)->Input:
        source=Path(str(raw.get("path",""))); fd=_open_verified(source,str(raw.get("sha256","")),raw.get("size_bytes"))
        try:
            out=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0),0o600)
            try:
                while chunk:=os.read(fd,1048576): os.write(out,chunk)
                os.fsync(out)
            finally: os.close(out)
        finally: os.close(fd)
        options={k:raw[k] for k in ("intent","at_seconds","duration_seconds") if k in raw}
        return Input(role,source,target,raw["sha256"],raw["size_bytes"],duration,options)
    def build_plan(self,*,required_shots:Sequence[str],clips:Sequence[Mapping[str,Any]],transitions:Sequence[Mapping[str,Any]],width:int,height:int,fps:int,target_duration_seconds:float,audio_plan:Mapping[str,Any]|None,subtitle:Mapping[str,Any]|None,subtitle_mode:str,output_path:Path,layout_mode:str="scale_pad",title_card:Mapping[str,Any]|None=None,end_card:Mapping[str,Any]|None=None,**forbidden:Any)->CompositionPlan:
        if forbidden or layout_mode not in LAYOUTS: raise CompositionPlanError("composition options are not closed")
        if not required_shots or list(required_shots)!=[x.get("shot_id") for x in clips] or len(set(required_shots))!=len(required_shots): raise CompositionPlanError("shots are not exact and ordered")
        if any(set(x)!={"shot_id","path","sha256","size_bytes","duration_seconds","accepted"} or x["accepted"] is not True for x in clips): raise CompositionPlanError("clip receipt invalid")
        durations=[_num(x["duration_seconds"],"clip duration") for x in clips]; parsed=[]
        if len(transitions)!=len(clips)-1: raise CompositionPlanError("transition count invalid")
        for i,x in enumerate(transitions):
            if set(x)!={"kind","duration_seconds"} or x["kind"] not in TRANSITIONS: raise CompositionPlanError("transition invalid")
            d=_num(x["duration_seconds"],"transition",x["kind"]=="cut")
            if (x["kind"]=="cut")!=(d==0) or d>=durations[i] or d>=durations[i+1]: raise CompositionPlanError("transition exceeds adjacent clip")
            parsed.append(Transition(x["kind"],d))
        for i,duration in enumerate(durations):
            occupied=(parsed[i-1].duration_seconds if i else 0)+(parsed[i].duration_seconds if i<len(parsed) else 0)
            if occupied>=duration: raise CompositionPlanError("adjacent transitions consume the effective clip")
        def parse_card(raw):
            if raw is None:return None
            if set(raw)!={"text","duration_seconds","style"} or not isinstance(raw["text"],str) or not 1<=len(raw["text"])<=500 or "\0" in raw["text"] or raw["style"] not in CARD_STYLES: raise CompositionPlanError("card invalid")
            return raw["text"],_num(raw["duration_seconds"],"card duration"),raw["style"]
        tc,ec=parse_card(title_card),parse_card(end_card); target=_num(target_duration_seconds,"target duration")
        if not math.isclose(target,sum(durations)-sum(x.duration_seconds for x in parsed)+sum(x[1] for x in (tc,ec) if x),abs_tol=1/fps): raise CompositionPlanError("duration mismatch")
        if isinstance(width,bool) or isinstance(height,bool) or not all(isinstance(v,int) for v in (width,height)) or width%2 or height%2 or not 360<=width<=3840 or not 360<=height<=3840 or fps not in FPS_VALUES: raise CompositionPlanError("dimensions or fps invalid")
        if subtitle_mode not in {"none","mux","burn"}: raise CompositionPlanError("subtitle mode invalid")
        verified=self._audio.verify_for_use(audio_plan) if audio_plan is not None else None; signed=list(verified.get("subtitles",[])) if verified else []
        if subtitle_mode=="none":
            if subtitle is not None: raise CompositionPlanError("subtitle not allowed")
        elif subtitle is None or subtitle not in signed: raise CompositionPlanError("subtitle is not verified plan receipt")
        output=Path(output_path)
        if not output.is_absolute() or output.suffix.lower()!=".mp4" or output.exists() or output.is_symlink(): raise CompositionPlanError("output invalid")
        stage=Path(tempfile.mkdtemp(prefix="composition-",dir=self._root)); os.chmod(stage,0o700)
        try:
            cs=tuple(self._stage(x,stage/f"clip-{i:03d}{Path(x['path']).suffix.lower()}",x["shot_id"],durations[i-1]) for i,x in enumerate(clips,1)); artifacts=[]
            if verified:
                if verified.get("narration"): artifacts.append(verified["narration"])
                if verified.get("music"): artifacts.append(verified["music"])
                artifacts.extend(verified.get("effects",[])); artifacts.extend(verified.get("ambience",[]))
            if subtitle is not None: artifacts.append(subtitle)
            media=tuple(self._stage(x,stage/f"media-{i:03d}{Path(x['path']).suffix.lower()}",x["artifact_role"]) for i,x in enumerate(artifacts,1)); cards=[]
            for name,value in (("title",tc),("end",ec)):
                if value:
                    p=stage/f"{name}.txt"; p.write_text(value[0],encoding="utf-8"); os.chmod(p,0o600); cards.append(Card(p,value[1],value[2]))
                else: cards.append(None)
            manifest={"clips":[[x.role,x.sha256,x.size_bytes] for x in cs],"media":[[x.role,x.sha256,x.size_bytes] for x in media]}; p=stage/"manifest.json"; p.write_text(json.dumps(manifest,sort_keys=True,separators=(",",":")),encoding="utf-8"); os.chmod(p,0o600)
            return CompositionPlan(cs,tuple(parsed),media,width,height,fps,target,verified,subtitle_mode,output,stage,layout_mode,cards[0],cards[1])
        except Exception: shutil.rmtree(stage,ignore_errors=True); raise
    def build_ffmpeg_argv(self,plan:CompositionPlan,*,output_path:Path|None=None)->list[str]:
        argv=["-hide_banner","-nostdin","-y"]
        for x in plan.clips: argv += ["-i",str(x.staged_path)]
        for x in plan.media_inputs:
            if x.role=="music" and x.options and x.options.get("intent",{}).get("loop"): argv += ["-stream_loop","-1"]
            argv += ["-i",str(x.staged_path)]
        fit="decrease" if plan.layout_mode=="scale_pad" else "increase"; tail=f",pad={plan.width}:{plan.height}:(ow-iw)/2:(oh-ih)/2" if fit=="decrease" else f",crop={plan.width}:{plan.height}"; filters=[]; video=[]
        def add_card(c,label):
            if c:
                bg="black" if c.style=="dark" else "white"; fg="white" if c.style=="dark" else "black"; filters.append(f"color=c={bg}:s={plan.width}x{plan.height}:r={plan.fps}:d={c.duration_seconds:g},drawtext=textfile={c.text_path}:fontcolor={fg}:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2[{label}]"); video.append((label,c.duration_seconds,True))
        add_card(plan.title_card,"card0")
        for i,x in enumerate(plan.clips): filters.append(f"[{i}:v]fps={plan.fps},scale={plan.width}:{plan.height}:force_original_aspect_ratio={fit}{tail},setsar=1,format=yuv420p,setpts=PTS-STARTPTS[v{i}]"); video.append((f"v{i}",x.duration_seconds,False))
        add_card(plan.end_card,"card1"); current,elapsed,_=video[0]; trans=iter(plan.transitions)
        for i,(label,duration,is_card) in enumerate(video[1:],1):
            t=Transition("cut",0) if is_card or current.startswith("card") else next(trans); out=f"vx{i}"
            filters.append(f"[{current}][{label}]concat=n=2:v=1:a=0[{out}]" if t.kind=="cut" else f"[{current}][{label}]xfade=transition={'fade' if t.kind=='crossfade' else 'fadeblack'}:duration={t.duration_seconds:g}:offset={elapsed-t.duration_seconds:g}[{out}]"); elapsed+=duration-t.duration_seconds; current=out
        base=len(plan.clips); subtitle_idx=None; audio=[]
        for i,x in enumerate(plan.media_inputs,base):
            if x.role.startswith("subtitle_"): subtitle_idx=i; continue
            label=f"a{len(audio)}"; volume={"music":"0.25","effect":"0.7","ambience":"0.35"}.get(x.role,"1.0"); option=x.options or {}; chain=""
            if x.role=="music":
                intent=option.get("intent",{}); trim=intent.get("trim_to_seconds")
                if trim is not None: chain+=f"atrim=0:{trim:g},"
                if intent.get("loop"): chain+=f"aloop=loop=-1:size={int(trim*48000)},atrim=0:{plan.target_duration_seconds:g},"
                elif intent.get("use_full_track"): chain+=f"atrim=0:{plan.target_duration_seconds:g},"
            elif x.role in {"effect","ambience"}:
                at=option.get("at_seconds",0); duration=option.get("duration_seconds",plan.target_duration_seconds); chain+=f"atrim=0:{duration:g},adelay={int(at*1000)}:all=1,"
            else: chain+=f"atrim=0:{plan.target_duration_seconds:g},"
            filters.append(f"[{i}:a]{chain}asetpts=PTS-STARTPTS,volume={volume}[{label}]"); audio.append((label,x.role))
        if plan.subtitle_mode=="burn" and subtitle_idx is not None: filters.append(f"[{current}]subtitles={plan.media_inputs[subtitle_idx-base].staged_path}[vout]"); current="vout"
        alabel=None
        if audio and plan.audio_plan and plan.audio_plan["audio_policy"]!="silent":
            speech=[x for x,r in audio if r in {"new_narration","existing_voice","existing_dialogue","existing_voice_dialogue"}]; beds=[x for x,r in audio if r in {"music","ambience"}]
            if speech and beds:
                filters.append(f"[{beds[0]}][{speech[0]}]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=250[ducked]"); audio=[("ducked","bed")]+[(x,r) for x,r in audio if x!=beds[0]]
            filters.append("".join(f"[{x}]" for x,_ in audio)+f"amix=inputs={len(audio)}:duration=longest:normalize=0,loudnorm=I=-16:LRA=11:TP=-1.5,afade=t=in:st=0:d=.1,afade=t=out:st={max(0,plan.target_duration_seconds-.25):g}:d=.25[aout]"); alabel="aout"
        argv += ["-filter_complex",";".join(filters),"-map",f"[{current}]"]
        argv += ["-map",f"[{alabel}]","-c:a","aac","-profile:a","aac_low","-ar","48000"] if alabel else ["-an"]
        if plan.subtitle_mode=="mux" and subtitle_idx is not None: argv += ["-map",f"{subtitle_idx}:0","-c:s","mov_text"]
        return argv+["-r",str(plan.fps),"-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart","-t",f"{plan.target_duration_seconds:g}",str(output_path or plan.output_path)]
    def compose(self,plan:CompositionPlan)->Path:
        temp=None
        try:
            if plan.output_path.exists(): raise CompositionPlanError("output exists")
            if plan.audio_plan is not None:self._audio.verify_for_use(plan.audio_plan)
            for x in (*plan.clips,*plan.media_inputs):
                for p in (x.staged_path,x.source_path): fd=_open_verified(p,x.sha256,x.size_bytes); os.close(fd)
            fd,name=tempfile.mkstemp(prefix=".composition-",suffix=".mp4",dir=plan.output_path.parent); os.fchmod(fd,0o600); os.close(fd); temp=Path(name); result=self._adapter.run("ffmpeg",self.build_ffmpeg_argv(plan,output_path=temp),timeout_seconds=self._timeout)
            if result.exit_code or not temp.is_file() or temp.is_symlink() or temp.stat().st_size<=0: raise CompositionPlanError("ffmpeg failed")
            fd=os.open(temp,os.O_RDONLY|os.O_NOFOLLOW); os.fsync(fd); os.close(fd); os.link(temp,plan.output_path); temp.unlink(); os.chmod(plan.output_path,0o600); d=os.open(plan.output_path.parent,os.O_RDONLY|getattr(os,"O_DIRECTORY",0)); os.fsync(d); os.close(d); return plan.output_path
        finally:
            if temp: temp.unlink(missing_ok=True)
            shutil.rmtree(plan.staging_dir,ignore_errors=True)
__all__=["CompositionPlan","CompositionPlanError","FPS_VALUES","TRANSITIONS","VideoCompositionService"]
