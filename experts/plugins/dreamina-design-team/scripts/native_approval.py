"""Fail-closed native confirmation for paid requests and local trust enrollment."""

from __future__ import annotations

import json
import os
import platform
import subprocess
from typing import Any, Mapping


class ApprovalDeniedError(PermissionError):
    """The human denied, timed out, or could not receive the approval dialog."""


class NativeApprovalProvider:
    """Require a native macOS confirmation dialog for the exact guarded action."""

    def confirm(self, request: Mapping[str, Any]) -> str:
        summary = json.dumps(dict(request), ensure_ascii=False, sort_keys=True, indent=2)
        self._confirm_dialog("Dreamina 付费生成请求\n\n" + summary, "批准一次")
        return "native-user-confirmed"

    def confirm_cli_enrollment(self, *, path: str, owner_uid: int, sha256: str) -> str:
        summary = json.dumps(
            {"action": "trust-dreamina-cli", "path": path, "owner_uid": owner_uid, "sha256": sha256},
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        self._confirm_dialog("注册可信 Dreamina CLI\n\n" + summary, "信任此文件")
        return "native-cli-trust-confirmed"

    def confirm_media_tool_enrollment(
        self, *, kind: str, path: str, owner_uid: int, sha256: str
    ) -> str:
        """Confirm the exact kind, canonical path, owner, and digest being trusted."""
        summary = json.dumps(
            {
                "action": "trust-media-tool",
                "kind": kind,
                "path": path,
                "owner_uid": owner_uid,
                "sha256": sha256,
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        self._confirm_dialog("注册可信本地媒体工具\n\n" + summary, "信任此文件")
        return "native-media-tool-trust-confirmed"

    def confirm_video_rights(self, request: Mapping[str, Any]) -> str:
        """Confirm the exact user assertion, source, project, mode, and design candidate."""
        summary = json.dumps(dict(request), ensure_ascii=False, sort_keys=True, indent=2)
        self._confirm_dialog(
            "确认视频复刻权利声明（仅记录用户声明，不验证所有权且不构成法律建议）\n\n"
            + summary,
            "确认声明",
        )
        return "native-video-rights-confirmed"

    def confirm_video_batch(self, request: Mapping[str, Any]) -> str:
        """Confirm one exact, non-expandable batch and its literal credit ceiling."""
        summary = json.dumps(dict(request), ensure_ascii=False, sort_keys=True, indent=2)
        self._confirm_dialog(
            "批准不可扩展的 Dreamina 整批额度（每个镜头与重试均已固定）\n\n" + summary,
            "批准整批",
        )
        return "native-video-batch-confirmed"

    def confirm_video_export(self, request: Mapping[str, Any]) -> str:
        """Confirm the exact destination, checksum, and rights basis before export.

        The destination is the one place a finished project leaves the private
        runtime area, so the user confirms the literal path and the verified
        checksum rather than a summary of them.
        """
        for field in ("destination", "sha256", "composition_version", "rights_basis"):
            if not str(request.get(field) or "").strip():
                raise ApprovalDeniedError(f"video export confirmation requires {field}")
        summary = json.dumps(dict(request), ensure_ascii=False, sort_keys=True, indent=2)
        self._confirm_dialog(
            "确认导出最终视频到该路径（含校验和与权利依据）\n\n" + summary,
            "确认导出",
        )
        return "native-video-export-confirmed"

    def confirm_audio_receipt_key_initialization(
        self, *, key_store_path: str, action: str, new_key_id: str, purpose: str, impact: str
    ) -> str:
        """Confirm one exact first bootstrap or destructive identity replacement."""
        if action not in {"first_bootstrap", "rebootstrap"}:
            raise ApprovalDeniedError("audio receipt key action is invalid")
        request = {
            "action": action,
            "impact": impact,
            "key_store_path": key_store_path,
            "new_key_id": new_key_id,
            "purpose": purpose,
        }
        summary = json.dumps(request, ensure_ascii=False, sort_keys=True, indent=2)
        title = "重新生成音频凭据签名密钥" if action == "rebootstrap" else "初始化音频凭据签名密钥"
        button = "确认重新生成密钥" if action == "rebootstrap" else "确认初始化密钥"
        self._confirm_dialog(title + "\n\n" + summary, button)
        return "native-audio-receipt-key-confirmed"

    @staticmethod
    def _confirm_dialog(message: str, approve_button: str) -> None:
        if platform.system() != "Darwin":
            raise ApprovalDeniedError(
                "native confirmation is unavailable on this platform; refusing guarded action"
            )
        script = (
            "on run argv\n"
            "set requestText to item 1 of argv\n"
            "set approveText to item 2 of argv\n"
            "tell application \"Finder\"\n"
            "activate\n"
            "set dialogResult to display dialog requestText buttons {\"取消\", approveText} "
            "default button \"取消\" cancel button \"取消\" with icon caution giving up after 300\n"
            "return \"button returned:\" & (button returned of dialogResult)\n"
            "end tell\n"
            "end run"
        )
        env = {
            key: os.environ[key]
            for key in ("HOME", "TMPDIR", "LANG", "LC_ALL")
            if key in os.environ
        }
        try:
            result = subprocess.run(
                ["/usr/bin/osascript", "-e", script, "--", message, approve_button],
                capture_output=True,
                text=True,
                timeout=310,
                shell=False,
                check=False,
                env=env,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ApprovalDeniedError("native approval dialog failed or timed out") from exc
        if result.returncode != 0 or f"button returned:{approve_button}" not in result.stdout:
            raise ApprovalDeniedError("native approval was not granted")


__all__ = ["ApprovalDeniedError", "NativeApprovalProvider"]
