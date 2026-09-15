"""Deterministic SRT/ASS rendering from approved script timing."""

from __future__ import annotations

import hashlib
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


class SubtitleTimelineError(ValueError):
    """Subtitle content or timing is unsafe or inconsistent."""


class SubtitleService:
    def __init__(self, *, max_text_length: int = 500, key_store: Any | None = None) -> None:
        if not isinstance(max_text_length, int) or max_text_length <= 0:
            raise ValueError("max text length must be positive")
        self._max_text_length = max_text_length
        from scripts.narration_service import FileAudioReceiptKeyStore
        self._key_store = key_store or FileAudioReceiptKeyStore()

    def from_source(self, cues: Sequence[Mapping[str, Any]], *, source: str) -> list[dict[str, Any]]:
        if source not in {"rewritten_script", "narration_timing"}:
            raise SubtitleTimelineError("subtitles require approved rewritten script or narration timing")
        return [dict(cue) for cue in cues]

    def render_srt(self, cues: Sequence[Mapping[str, Any]], *, target_duration_seconds: float | None = None) -> str:
        normalized = self._validate(cues, target_duration_seconds)
        lines = []
        for index, cue in enumerate(normalized, 1):
            if round(cue["start"] * 1000) >= round(cue["end"] * 1000):
                raise SubtitleTimelineError("cue collapses after SRT timestamp rounding")
            text = cue["text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            lines.extend([str(index), f"{self._srt_time(cue['start'])} --> {self._srt_time(cue['end'])}", text, ""])
        return "\n".join(lines)

    def render_ass(self, cues: Sequence[Mapping[str, Any]], *, target_duration_seconds: float | None = None) -> str:
        normalized = self._validate(cues, target_duration_seconds)
        header = "[Script Info]\nScriptType: v4.00+\n[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,Alignment\nStyle: Default,Arial,48,&H00FFFFFF,2\n[Events]\nFormat: Layer,Start,End,Style,Text\n"
        lines = []
        for cue in normalized:
            if round(cue["start"] * 100) >= round(cue["end"] * 100):
                raise SubtitleTimelineError("cue collapses after ASS timestamp rounding")
            safe = cue["text"].replace("\\", "＼").replace("{", "｛").replace("}", "｝")
            lines.append(f"Dialogue: 0,{self._ass_time(cue['start'])},{self._ass_time(cue['end'])},Default,{safe}")
        return header + "\n".join(lines) + ("\n" if lines else "")

    def write_srt(self, cues: Sequence[Mapping[str, Any]], output_path: Path, *, target_duration_seconds: float, source: str = "rewritten_script") -> dict[str, Any]:
        return self._write(self.render_srt(cues, target_duration_seconds=target_duration_seconds), output_path, "srt", source)

    def write_ass(self, cues: Sequence[Mapping[str, Any]], output_path: Path, *, target_duration_seconds: float, source: str = "rewritten_script") -> dict[str, Any]:
        return self._write(self.render_ass(cues, target_duration_seconds=target_duration_seconds), output_path, "ass", source)

    def _validate(self, cues: Sequence[Mapping[str, Any]], target: float | None) -> list[dict[str, Any]]:
        if target is not None and (isinstance(target, bool) or not isinstance(target, (int, float)) or not math.isfinite(target) or target <= 0):
            raise SubtitleTimelineError("target duration must be positive and finite")
        result = []
        previous_end = 0.0
        for cue in cues:
            start, end, text = cue.get("start"), cue.get("end"), cue.get("text")
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (start, end)):
                raise SubtitleTimelineError("cue timestamps must be finite numbers")
            clean = " ".join(text.split()) if isinstance(text, str) else ""
            if start < 0 or end <= start or start < previous_end or (target is not None and end > target) or not clean or len(clean) > self._max_text_length or "\x00" in clean:
                raise SubtitleTimelineError("cue timeline or text is invalid")
            result.append({"start": float(start), "end": float(end), "text": clean})
            previous_end = float(end)
        return result

    @staticmethod
    def _srt_time(value: float) -> str:
        millis = round(value * 1000); hours, rem = divmod(millis, 3600000); minutes, rem = divmod(rem, 60000); seconds, ms = divmod(rem, 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"

    @staticmethod
    def _ass_time(value: float) -> str:
        centis = round(value * 100); hours, rem = divmod(centis, 360000); minutes, rem = divmod(rem, 6000); seconds, cs = divmod(rem, 100)
        return f"{hours}:{minutes:02d}:{seconds:02d}.{cs:02d}"

    def _write(self, content: str, output_path: Path, format_name: str, source: str) -> dict[str, Any]:
        if source not in {"rewritten_script", "narration_timing"}:
            raise SubtitleTimelineError("subtitle receipt source is not approved")
        output = Path(output_path)
        if (not output.is_absolute() or output.exists() or output.is_symlink()
                or not output.parent.is_dir() or output.parent.is_symlink()
                or output.parent.stat().st_uid != os.getuid()
                or output.parent.stat().st_mode & 0o077):
            raise SubtitleTimelineError("subtitle output must be in an existing absolute directory")
        payload = content.encode("utf-8")
        descriptor, temporary = tempfile.mkstemp(prefix=".subtitle-", dir=output.parent)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload); handle.flush(); os.fsync(handle.fileno())
            try:
                os.link(temporary, output, follow_symlinks=False)
            except FileExistsError as exc:
                raise SubtitleTimelineError("subtitle output already exists") from exc
            os.chmod(output, 0o600)
            directory = os.open(output.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            Path(temporary).unlink(missing_ok=True)
        from scripts.narration_service import _artifact_receipt
        return _artifact_receipt(provider="subtitle-service", path=output,
            mime_type="application/x-subrip" if format_name == "srt" else "text/x-ssa",
            artifact_role="subtitle_srt" if format_name == "srt" else "subtitle_ass",
            kind="generated_subtitle", rights_declared=["subtitles"], approved_root=None,
            source=source, voice=None, model=None, key_store=self._key_store)


__all__ = ["SubtitleService", "SubtitleTimelineError"]
