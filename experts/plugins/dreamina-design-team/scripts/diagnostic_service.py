"""Bounded redacted diagnostics for Dreamina CLI logs."""
from __future__ import annotations
import os, stat, time
from pathlib import Path
from scripts.output_redactor import redact_text

class DiagnosticService:
    def __init__(self,log_root:Path|None=None): self.log_root=(log_root or Path.home()/'.dreamina_cli'/'logs').resolve()
    def diagnose(self,*,command:str,error:str,submit_id:str|None=None,since_minutes:int=60,max_files:int=3)->dict[str,object]:
        if not 1<=since_minutes<=1440 or not 1<=max_files<=10: raise ValueError('diagnostic bounds invalid')
        excerpts=[]; cutoff=time.time()-since_minutes*60
        if self.log_root.is_dir():
            candidates=sorted((p for p in self.log_root.iterdir() if p.stat(follow_symlinks=False).st_mtime>=cutoff),key=lambda p:p.stat(follow_symlinks=False).st_mtime,reverse=True)
            for path in candidates:
                if len(excerpts)>=max_files or path.is_symlink(): continue
                try:
                    fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)); info=os.fstat(fd)
                    if not stat.S_ISREG(info.st_mode): os.close(fd); continue
                    with os.fdopen(fd,'rb') as handle: data=handle.read(65537)
                    excerpts.append({'file':path.name,'content':redact_text(data[:65536].decode('utf-8',errors='replace'),max_bytes=65536)})
                except OSError: continue
        return {'command':redact_text(command,max_bytes=4096),'error':redact_text(error,max_bytes=16384),'submit_id':submit_id,'log_root':str(self.log_root),'excerpts':excerpts}
