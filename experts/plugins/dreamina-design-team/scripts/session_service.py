"""Closed Dreamina Session CRUD automation."""
from __future__ import annotations
import re
from scripts.output_redactor import redact_text

SESSION_ID=re.compile(r'^[A-Za-z0-9_-]{1,128}$')
class SessionService:
    def __init__(self,adapter,approval_provider): self.adapter=adapter; self.approval_provider=approval_provider
    def execute(self,action:str,*,name:str|None=None,session_id:str|None=None,query:str|None=None)->dict[str,object]:
        if action == 'create': argv=['session','create',self._text(name,'name')]
        elif action == 'list': argv=['session','list']
        elif action == 'search': argv=['session','search',self._text(query,'query')]
        elif action == 'rename': argv=['session','rename',self._id(session_id),self._text(name,'name')]
        elif action == 'delete':
            sid=self._id(session_id)
            if sid=='0': raise ValueError('default Session 0 cannot be deleted')
            argv=['session','delete',sid]
        else: raise ValueError(f'unsupported session action: {action}')
        if action in {'create','rename','delete'}: self.approval_provider.confirm({'operation':'dreamina-session','action':action,'name':name,'session_id':session_id})
        result=self.adapter.run_text(argv)
        return {'action':action,'exit_code':result.exit_code,'success':result.exit_code==0,'output':redact_text(result.stdout+result.stderr,max_bytes=128*1024)}
    @staticmethod
    def _text(value,name):
        if not isinstance(value,str) or not 1<=len(value.encode('utf-8'))<=200: raise ValueError(f'{name} must be 1..200 UTF-8 bytes')
        return value
    @staticmethod
    def _id(value):
        if not isinstance(value,str) or not SESSION_ID.fullmatch(value): raise ValueError('unsafe session_id')
        return value
