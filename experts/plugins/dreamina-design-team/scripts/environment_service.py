"""Dreamina CLI environment inspection and verified installation."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from scripts.output_redactor import redact_text


COMMANDS = frozenset({"login", "relogin", "logout", "user_credit", "text2image", "image2image", "image_upscale", "text2video", "image2video", "frames2video", "multiframe2video", "multimodal2video", "query_result", "list_task", "session", "version"})
INSTALLER_URL = "https://jimeng.jianying.com/cli"

class _Downloader:
    def fetch(self,url,max_bytes):
        with urllib.request.urlopen(url,timeout=30) as response:
            data=response.read(max_bytes+1)
            if len(data)>max_bytes: raise ValueError('Dreamina installer exceeds size limit')
            return data,response.geturl()

class _Runner:
    def run(self,path):
        env={key:os.environ[key] for key in ('HOME','TMPDIR','LANG','LC_ALL') if key in os.environ}; env['PATH']='/usr/bin:/bin:/usr/sbin:/sbin'
        result=subprocess.run(['/bin/bash',str(path)],capture_output=True,text=True,timeout=300,shell=False,env=env)
        return result.returncode,result.stdout,result.stderr


class EnvironmentService:
    def __init__(self, adapter, *, downloader=None, runner=None, trust_store=None):
        self.adapter = adapter; self.downloader=downloader or _Downloader(); self.runner=runner or _Runner(); self.trust_store=trust_store

    def status(self, *, command: str | None = None, detail: str = "summary") -> dict[str, object]:
        if detail not in {"summary", "full"}: raise ValueError("detail must be summary or full")
        if command is not None and command not in COMMANDS: raise ValueError(f"unsupported Dreamina command: {command}")
        snapshot = self.adapter.capability_snapshot()
        result: dict[str, object] = {"installed": True, "trusted": True, "cli_version": snapshot.get("cli_version"), "modes": snapshot.get("modes", []), "captured_at": snapshot.get("captured_at")}
        if command:
            help_result = self.adapter.run_text([command, "--help"] if command != "version" else ["version"])
            result.update({"command": command, "command_available": help_result.exit_code == 0})
            if detail == "full": result["help"] = redact_text(help_result.stdout + help_result.stderr, max_bytes=128 * 1024)
        elif detail == "full": result["capabilities"] = snapshot
        return result

    def install_or_upgrade(self,action:str,*,approval_provider)->dict[str,object]:
        if action not in {'install','upgrade'}: raise ValueError('action must be install or upgrade')
        data,final_url=self.downloader.fetch(INSTALLER_URL,2*1024*1024)
        parsed=urlparse(final_url)
        if parsed.scheme!='https' or parsed.hostname!='jimeng.jianying.com': raise ValueError('Dreamina installer redirected outside approved HTTPS host')
        if not data.startswith(b'#!') or b'\x00' in data: raise ValueError('Dreamina installer response is not a shell script')
        digest=hashlib.sha256(data).hexdigest()
        approval_provider.confirm({'operation':'dreamina-cli-installer','action':action,'url':INSTALLER_URL,'final_url':final_url,'sha256':digest})
        with tempfile.TemporaryDirectory(prefix='dreamina-installer-') as tmp:
            os.chmod(tmp,0o700); path=Path(tmp)/'installer.sh'; path.write_bytes(data); path.chmod(0o500)
            code,stdout,stderr=self.runner.run(path)
        if code!=0: raise RuntimeError(f'Dreamina installer failed (exit {code}): {redact_text(stderr,max_bytes=16384)}')
        candidate=Path.home()/'.local'/'bin'/'dreamina'
        resolved=candidate if candidate.is_file() else Path(shutil.which('dreamina') or '')
        if not resolved.is_file(): raise RuntimeError('installer finished but dreamina executable was not found')
        if self.trust_store is not None: self.trust_store.enroll(resolved,approval_provider=approval_provider)
        return {'action':action,'installed':True,'cli_path':str(resolved.resolve()),'installer_sha256':digest,'output':redact_text(stdout,max_bytes=32768)}
