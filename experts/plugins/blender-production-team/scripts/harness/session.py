"""Session revision, idempotency, authorization, and audit boundary."""

from __future__ import annotations

import copy
from collections import OrderedDict
from collections.abc import Callable

from .authorization import AuthorizationManager
from .execution_policy import ExecutionMode, ExecutionPolicy
import math
from .errors import HarnessError
from .protocol import CommandRequest, PROTOCOL_VERSION


READ_ONLY_COMMANDS = {
    "session.capabilities", "session.status", "scene.inspect", "preview.capture", "export.file",
    "official_uploader.inspect", "official_uploader.status",
    "transaction.begin", "transaction.commit", "transaction.rollback", "session.authorize",
}
READ_ONLY_COMMANDS.update({'job.submit','job.status','job.cancel','job.recover'})
INSPECTION_COMMANDS = {
    "capability.list", "capability.describe",
    "animation.action_list", "validation.foot_drift", "validation.limb_length",
    "validation.floor_penetration", "validation.prop_handoff", "validation.camera_visibility",
    "validation.motion_discontinuity",
    "render.inspect", "compositor.inspect",
    "grease_pencil.inspect", "sequence.inspect", "tracking.inspect", "rig.rigify_status",
    "job.status", "job.cancel", "job.recover",
    "session.status", "session.capabilities", "session.pause", "session.set_progress",
    "scene.inspect", "preview.capture", "view.present", "view.set", "view.focus", "playback.set_frame", "playback.set",
    "official_uploader.inspect", "official_uploader.status",
}
READ_ONLY_COMMANDS.update(INSPECTION_COMMANDS | {"session.resume"})
GATED_COMMANDS = {
    "session.resume",
    "object.delete",
    "scene.new",
    "scene.open",
    "scene.save",
    "scene.save_as",
    "export.final",
    "export.file",
    "export.extended",
    "advanced.execute_python",
    "session.close",
    "official_uploader.render_and_link",
    "official_uploader.link_existing",
    "official_uploader.open_link",
}


class HarnessSession:
    def __init__(
        self,
        session_id: str,
        *,
        dispatch: Callable[[str, dict], dict],
        authorization: AuthorizationManager | None = None,
        transactions=None,
        replay_limit: int = 512,
        execution_policy: ExecutionPolicy | None = None,
    ):
        self.session_id = session_id
        self.scene_revision = 0
        self.dispatch = dispatch
        self.authorization = authorization or AuthorizationManager()
        self.transactions = transactions
        self._replay_limit = replay_limit
        self._responses: OrderedDict[str, dict] = OrderedDict()
        self._audit: list[dict] = []
        self._approved_snapshots: dict[str, int] = {}
        self.execution_policy = execution_policy or ExecutionPolicy.interactive()
        self.paused = False
        self.revoked = False
        self.control_epoch = 0
        self.needs_inspection = False
        self.on_pause = None
        self.on_update = None
        self._active_transactions = set()
        self._invalid_transactions = set()
        self._stage = "Ready"
        self._progress = None
        self._last_command = None
        self._changed_objects = []
        self._last_error = None

    def handle(self, payload: dict) -> dict:
        request_id = payload.get("requestId", "") if isinstance(payload, dict) else ""
        if request_id in self._responses:
            return copy.deepcopy(self._responses[request_id])
        try:
            request = CommandRequest.parse(payload)
            if request.session_id != self.session_id:
                raise HarnessError("SESSION_MISMATCH", "request session does not match active session")
            if self.revoked:
                raise HarnessError("SESSION_REVOKED", "session access has been revoked")
            if self.execution_policy.mode is ExecutionMode.REVIEW_ONLY and request.command not in INSPECTION_COMMANDS | {"session.resume"}:
                raise HarnessError("READ_ONLY_POLICY", "this session permits inspection only")
            if self.paused and request.command not in INSPECTION_COMMANDS | {"session.resume", "session.authorize"}:
                raise HarnessError("SESSION_PAUSED", "user has paused or taken over the session")
            if self.needs_inspection and request.command not in INSPECTION_COMMANDS | {"session.resume", "session.authorize"}:
                raise HarnessError("REINSPECTION_REQUIRED", "inspect the current scene after user takeover")
            if request.transaction_id in self._invalid_transactions and (
                request.command.startswith("transaction.") or request.command not in READ_ONLY_COMMANDS
            ):
                raise HarnessError("TRANSACTION_INVALIDATED", "begin a new transaction after user takeover")
            if request.command in {"session.status", "session.pause", "session.resume", "session.set_progress"}:
                response = self._handle_control(request)
                self._remember(request_id, response)
                self._record_audit(payload, response)
                return copy.deepcopy(response)
            if request.command.startswith("transaction."):
                response = self._handle_transaction(request)
                self._remember(request_id, response)
                self._record_audit(payload, response)
                return copy.deepcopy(response)
            if request.command == "session.authorize":
                response = self._handle_authorize(request)
                self._remember(request_id, response)
                self._record_audit(payload, response)
                return copy.deepcopy(response)
            mutation = request.command not in READ_ONLY_COMMANDS
            if mutation and request.expected_scene_revision != self.scene_revision:
                raise HarnessError(
                    "STALE_SCENE_REVISION",
                    f"expected scene revision {self.scene_revision}",
                    retryable=True,
                )
            automatic_export = request.command == "export.file" and self.execution_policy.permits_fresh_export(request.arguments)
            if request.command in GATED_COMMANDS and not automatic_export and not self.authorization.verify(
                request.authorization, request.request_id, request.command
            ):
                raise HarnessError("AUTHORIZATION_REQUIRED", f"authorization required for {request.command}")
            if automatic_export and self.transactions is None:
                raise HarnessError("MILESTONE_NOT_APPROVED", "automatic export requires a committed transaction")
            if request.command == "export.file" and self.transactions is not None:
                snapshot_id = request.arguments.get("snapshotId")
                if self._approved_snapshots.get(snapshot_id) != self.scene_revision:
                    raise HarnessError(
                        "MILESTONE_NOT_APPROVED",
                        "export snapshot is not committed at the current scene revision",
                    )
            if mutation and self.transactions is not None:
                result = self.transactions.execute(
                    request.transaction_id,
                    lambda: self.dispatch(request.command, request.arguments),
                ) or {}
            else:
                result = self.dispatch(request.command, request.arguments) or {}
            if mutation:
                self.scene_revision += 1
            if request.command == "scene.inspect":
                self.needs_inspection = False
            if mutation or request.command == "export.file":
                self._last_command = request.command
                self._changed_objects = list(result.get("changedObjects", []))
                self._last_error = None
            response = {
                "protocolVersion": PROTOCOL_VERSION,
                "requestId": request.request_id,
                "status": "succeeded",
                "sceneRevision": self.scene_revision,
                "changedObjects": list(result.get("changedObjects", [])),
                "warnings": list(result.get("warnings", [])),
            }
            if "snapshotId" in result:
                response["snapshotId"] = result["snapshotId"]
            if "result" in result:
                response["result"] = result["result"]
        except HarnessError as exc:
            self._sync_rolled_back_revision(payload)
            response = self._error_response(request_id, exc)
            self._last_error = {"code": exc.code, "message": str(exc)}
        except Exception as exc:
            self._sync_rolled_back_revision(payload)
            response = self._error_response(request_id, HarnessError("COMMAND_FAILED", str(exc)))
            self._last_error = {"code": "COMMAND_FAILED", "message": str(exc)}
        self._remember(request_id, response)
        self._record_audit(payload, response)
        return copy.deepcopy(response)

    def _error_response(self, request_id: str, error: HarnessError) -> dict:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "requestId": request_id,
            "status": "failed",
            "sceneRevision": self.scene_revision,
            "changedObjects": [],
            "warnings": [],
            "error": {"code": error.code, "message": str(error), "retryable": error.retryable},
        }

    def _sync_rolled_back_revision(self, payload) -> None:
        if self.transactions is None or not isinstance(payload, dict):
            return
        if payload.get("transactionId") in self._invalid_transactions:
            return
        try:
            transaction_status = self.transactions.status(payload.get("transactionId"))
            if transaction_status["state"] == "rolled_back":
                self.scene_revision = transaction_status["beginRevision"]
        except Exception:
            pass

    def _handle_transaction(self, request: CommandRequest) -> dict:
        if self.transactions is None:
            raise HarnessError("TRANSACTIONS_UNAVAILABLE", "transaction manager is unavailable")
        if request.arguments:
            raise HarnessError("INVALID_ARGUMENT", "transaction commands do not accept arguments")
        if request.command == "transaction.begin":
            result = self.transactions.begin(request.transaction_id, scene_revision=self.scene_revision)
            self._active_transactions.add(request.transaction_id)
        elif request.command == "transaction.commit":
            result = self.transactions.commit(request.transaction_id, scene_revision=self.scene_revision)
            self._approved_snapshots[result["snapshotId"]] = self.scene_revision
            self._active_transactions.discard(request.transaction_id)
        elif request.command == "transaction.rollback":
            result = self.transactions.rollback(request.transaction_id)
            self.scene_revision = result["beginRevision"]
            self._active_transactions.discard(request.transaction_id)
        else:
            raise HarnessError("UNKNOWN_COMMAND", f"unknown command: {request.command}")
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "requestId": request.request_id,
            "status": "succeeded",
            "sceneRevision": self.scene_revision,
            "changedObjects": [],
            "warnings": [],
            "snapshotId": result["snapshotId"],
            "result": result,
        }

    def pause(self, *, source="local_ui"):
        if not self.paused:
            self.control_epoch += 1
            self.paused = True
            self.needs_inspection = True
            self.scene_revision += 1
            self._invalid_transactions.update(self._active_transactions)
            self._active_transactions.clear()
            self._approved_snapshots.clear()
            if self.on_pause:
                self.on_pause()
            self._record_local_control("session.pause", source)
        self._notify()

    def resume_local(self, *, source="local_ui"):
        """Called only by the explicit local UI resume control or an authorized command."""
        if self.revoked:
            raise HarnessError("SESSION_REVOKED", "session access has been revoked")
        self.paused = False
        self.control_epoch += 1
        # Inspect again after resume: user edits may have occurred after an earlier inspection.
        self.needs_inspection = True
        self._record_local_control("session.resume", source)
        self._notify()

    def revoke(self):
        self.revoked = True
        self.pause(source="runtime")

    def status(self):
        return {"sessionId": self.session_id, "sceneRevision": self.scene_revision,
                "executionPolicy": self.execution_policy.to_audit_dict(), "paused": self.paused,
                "revoked": self.revoked, "needsInspection": self.needs_inspection,
                "stage": self._stage, "progress": self._progress,
                "lastCommand": self._last_command, "changedObjects": list(self._changed_objects),
                "lastError": copy.deepcopy(self._last_error)}

    def _handle_control(self, request):
        if request.command == "session.set_progress":
            args = request.arguments
            stage = args.get("stage")
            progress = args.get("progress")
            if set(args) - {"stage", "progress"} or not isinstance(stage, str) or not 1 <= len(stage) <= 80:
                raise HarnessError("INVALID_ARGUMENT", "progress requires a stage name of 1..80 characters")
            if progress is not None and (isinstance(progress, bool) or not isinstance(progress, (int, float))
                                         or not math.isfinite(progress) or not 0 <= progress <= 1):
                raise HarnessError("INVALID_ARGUMENT", "progress must be between zero and one")
            self._stage, self._progress = stage, progress
        else:
            if request.arguments:
                raise HarnessError("INVALID_ARGUMENT", "session control accepts no arguments")
            if request.command == "session.pause":
                self.pause(source="command")
            elif request.command == "session.resume":
                if not self.authorization.verify(request.authorization, request.request_id, request.command):
                    raise HarnessError("AUTHORIZATION_REQUIRED", "resume requires user authorization")
                self.resume_local(source="command")
        return {"protocolVersion": PROTOCOL_VERSION, "requestId": request.request_id, "status": "succeeded",
                "sceneRevision": self.scene_revision, "changedObjects": [], "warnings": [], "result": self.status()}

    def _notify(self):
        if self.on_update:
            self.on_update()

    def _record_local_control(self, command, source):
        if source != "command":
            self._audit.append({"command": command, "source": source, "status": "succeeded",
                                "sceneRevision": self.scene_revision,
                                "executionPolicy": self.execution_policy.to_audit_dict()})

    def _handle_authorize(self, request: CommandRequest) -> dict:
        arguments = request.arguments
        unknown = sorted(set(arguments) - {"action", "requestId", "userConfirmed", "ttlSeconds"})
        if unknown:
            raise HarnessError("INVALID_ARGUMENT", f"unknown authorization fields: {unknown}")
        if arguments.get("userConfirmed") is not True:
            raise HarnessError("USER_CONFIRMATION_REQUIRED", "explicit user confirmation is required")
        action = arguments.get("action")
        target_request_id = arguments.get("requestId")
        if action not in GATED_COMMANDS or not isinstance(target_request_id, str) or not target_request_id:
            raise HarnessError("INVALID_ARGUMENT", "authorization requires a gated action and target requestId")
        ttl = min(300, max(1, int(arguments.get("ttlSeconds", 60))))
        claim = self.authorization.issue(target_request_id, action, ttl_seconds=ttl)
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "requestId": request.request_id,
            "status": "succeeded",
            "sceneRevision": self.scene_revision,
            "changedObjects": [],
            "warnings": [],
            "result": {"authorization": claim, "action": action, "targetRequestId": target_request_id, "ttlSeconds": ttl},
        }

    def _remember(self, request_id: str, response: dict) -> None:
        if not request_id:
            return
        self._responses[request_id] = copy.deepcopy(response)
        self._responses.move_to_end(request_id)
        while len(self._responses) > self._replay_limit:
            self._responses.popitem(last=False)

    def _record_audit(self, payload: dict, response: dict) -> None:
        if isinstance(payload, dict) and str(payload.get("command", "")).startswith("official_uploader."):
            sanitized = {
                "command": payload.get("command"),
                "requestId": payload.get("requestId"),
                "status": response["status"],
                "sceneRevision": response["sceneRevision"],
                "executionPolicy": self.execution_policy.to_audit_dict(),
            }
            self._audit.append(sanitized)
            self._notify()
            return
        sanitized = dict(payload) if isinstance(payload, dict) else {"request": "invalid"}
        if "authorization" in sanitized:
            sanitized["authorization"] = "[REDACTED]"
        sanitized["status"] = response["status"]
        sanitized["sceneRevision"] = response["sceneRevision"]
        sanitized["executionPolicy"] = self.execution_policy.to_audit_dict()
        self._audit.append(sanitized)
        self._notify()

    def audit_entries(self) -> list[dict]:
        return copy.deepcopy(self._audit)
