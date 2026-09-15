"""Closed Dreamina OAuth command automation."""
from __future__ import annotations
import re
import secrets
import time
from scripts.output_redactor import redact_text

class AuthFlowStore:
    def __init__(self,*,ttl_seconds:int=600,clock=time.monotonic): self.ttl_seconds=ttl_seconds; self.clock=clock; self._flows={}
    def issue(self,device_code:str)->str:
        if not device_code: raise ValueError('device_code is required from CLI output')
        flow_id=secrets.token_urlsafe(24); self._flows[flow_id]=(device_code,self.clock()+self.ttl_seconds); return flow_id
    def consume(self,flow_id:str|None)->str:
        if not flow_id or flow_id not in self._flows: raise ValueError('unknown or already-consumed flow_id')
        device_code,expires=self._flows.pop(flow_id)
        if self.clock()>expires: raise ValueError('flow_id expired')
        return device_code

class AuthService:
    def __init__(self,adapter,account_service,approval_provider,flow_store:AuthFlowStore): self.adapter=adapter; self.account_service=account_service; self.approval_provider=approval_provider; self.flow_store=flow_store
    def execute(self,action:str,*,flow_id:str|None=None,poll_seconds:int=0)->dict[str,object]:
        if not 0 <= poll_seconds <= 300: raise ValueError('poll_seconds must be between 0 and 300')
        if action in {'login','relogin'} and hasattr(self.adapter,'timeout_seconds'):
            self.adapter.timeout_seconds=max(int(self.adapter.timeout_seconds),310)
        elif action == 'check_login' and hasattr(self.adapter,'timeout_seconds'):
            self.adapter.timeout_seconds=max(int(self.adapter.timeout_seconds),poll_seconds+10)
        if action == 'check_login':
            device_code=self.flow_store.consume(flow_id)
            argv=['login','checklogin','--device_code',device_code,'--poll',str(poll_seconds)]
        else:
            mapping={'login':['login'],'login_headless':['login','--headless'],'relogin':['relogin'],'logout':['logout']}
            if action not in mapping: raise ValueError(f'unsupported auth action: {action}')
            argv=mapping[action]
        if action in {'relogin','logout'}: self.approval_provider.confirm({'operation':'dreamina-auth','action':action})
        result=self.adapter.run_text(argv)
        output=redact_text(result.stdout+result.stderr,max_bytes=128*1024)
        response={'action':action,'exit_code':result.exit_code,'output':output,'success':result.exit_code==0}
        if action in {'login','check_login','relogin'} and result.exit_code==0: response['account']=self.account_service.user_credit()
        if action == 'login_headless' and result.exit_code==0:
            raw=result.stdout+result.stderr
            device_match=re.search(r'(?im)^\s*device_code\s*[:=]\s*(\S+)',raw)
            if not device_match: raise ValueError('headless login returned no device_code')
            response['flow_id']=self.flow_store.issue(device_match.group(1))
            response['requires_user_action']=True
            for key in ('verification_uri','user_code'):
                match=re.search(rf'(?im)^\s*{key}\s*[:=]\s*(\S+)',raw)
                if match: response[key]=match.group(1)
        return response
