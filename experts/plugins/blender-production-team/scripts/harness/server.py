"""Composition of transport, main-thread execution, and Harness session."""

from __future__ import annotations

import json
import os
import secrets
import sys
from dataclasses import dataclass
from pathlib import Path

from .main_thread import MainThreadExecutor
from .runtime import create_session
from .snapshot import BlenderCheckpointStore
from .transport import Endpoint, JsonLineServer, choose_endpoint
from .transaction import TransactionManager
from .errors import HarnessError


@dataclass
class HarnessRuntime:
    endpoint: Endpoint
    descriptor_path: Path
    transport: JsonLineServer
    executor: MainThreadExecutor
    bpy_module: object
    session: object
    frontend: object = None
    load_handler: object = None
    closed: bool = False
    executing: bool = False

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self.session.revoke()
        self.session.on_update = None
        self.executor.cancel_pending()
        self.transport.close()
        try:
            self.bpy_module.app.timers.unregister(self.executor.blender_timer_callback)
        except Exception:
            pass
        try:
            self.descriptor_path.unlink()
        except FileNotFoundError:
            pass
        if self.load_handler is not None:
            handlers = self.bpy_module.app.handlers.load_pre
            if self.load_handler in handlers:
                handlers.remove(self.load_handler)
        if self.frontend is not None:
            self.frontend.unregister()
            self.frontend = None


def start_harness(
    bpy_module,
    *,
    session_id: str,
    runtime_dir: Path,
    endpoint: Endpoint | None = None,
    approved_output_root: Path | None = None,
    approved_asset_roots=(),
    execution_policy=None,
    show_frontend: bool = True,
    runtime_mode: str = "managed",
) -> HarnessRuntime:
    runtime_dir = Path(runtime_dir)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(runtime_dir, 0o700)
    token = secrets.token_urlsafe(32)
    checkpoint_store = BlenderCheckpointStore(bpy_module, runtime_dir / "checkpoints")
    transactions = TransactionManager(
        capture=checkpoint_store.capture,
        restore=checkpoint_store.restore,
        journal_path=runtime_dir / "recovery.json",
    )
    session = create_session(
        bpy_module,
        session_id,
        runtime_mode=runtime_mode,
        approved_output_root=approved_output_root or runtime_dir / "outputs",
        approved_asset_roots=approved_asset_roots,
        transactions=transactions,
        execution_policy=execution_policy,
    )
    executor = MainThreadExecutor()
    session.on_pause = lambda: executor.cancel_pending("SESSION_PAUSED")
    holder = {}

    def handle(payload):
        epoch = session.control_epoch
        def execute():
            runtime = holder.get("runtime")
            if runtime is None or runtime.closed or session.revoked:
                raise HarnessError("SESSION_REVOKED", "runtime has closed")
            if epoch != session.control_epoch:
                raise HarnessError("SESSION_CONTROL_CHANGED", "command queued before user takeover/resume")
            runtime.executing = True
            try:
                return session.handle(payload)
            finally:
                runtime.executing = False
        return executor.submit(execute, timeout=30)
    selected = endpoint or choose_endpoint(sys.platform, session_id=session_id, runtime_dir=str(runtime_dir))
    transport = JsonLineServer(
        selected,
        token=token,
        handle=handle,
    )
    actual_endpoint = transport.start()
    bpy_module.app.timers.register(executor.blender_timer_callback, first_interval=0.01, persistent=True)

    descriptor_path = runtime_dir / f"{session_id}.json"
    address = list(actual_endpoint.address) if isinstance(actual_endpoint.address, tuple) else actual_endpoint.address
    descriptor_path.write_text(
        json.dumps(
            {
                "protocolVersion": "codex-blender/v1",
                "sessionId": session_id,
                "transport": actual_endpoint.kind,
                "address": address,
                "token": token,
                "pid": os.getpid(),
                "outputRoot": str((approved_output_root or runtime_dir / "outputs").resolve()),
                "assetRoots": [str(Path(value).resolve()) for value in approved_asset_roots],
                "executionPolicy": session.execution_policy.to_audit_dict(),
            },
            sort_keys=True,
        )
    )
    os.chmod(descriptor_path, 0o600)
    runtime = HarnessRuntime(actual_endpoint, descriptor_path, transport, executor, bpy_module, session)
    holder["runtime"] = runtime
    handlers = getattr(bpy_module.app, "handlers", None)
    if handlers is not None:
        def on_file_load(_unused):
            # A snapshot rollback is owned by the running command; external file loads revoke access.
            if not runtime.executing:
                runtime.close()
        runtime.load_handler = handlers.persistent(on_file_load)
        handlers.load_pre.append(runtime.load_handler)
    if show_frontend and hasattr(bpy_module, "types") and not getattr(bpy_module.app, "background", False):
        from .frontend import Frontend
        runtime.frontend = Frontend(bpy_module, runtime)
        try:
            runtime.frontend.register()
            session.on_update = runtime.frontend.redraw
        except Exception:
            runtime.frontend = None
            runtime.close()
            raise
    return runtime
