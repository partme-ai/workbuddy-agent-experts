"""Deterministic, local-only measurement for staged reference videos."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import statistics
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.json_contracts import canonical_fingerprint
from scripts.media_adapter import MediaOutputError
from scripts.video_project_store import VideoProjectStore


SCENE_ROW = re.compile(r"pts_time[:=](?P<time>[0-9]+(?:\.[0-9]+)?)")
MOTION_TIME = re.compile(r"pts_time[:=](?P<time>[0-9]+(?:\.[0-9]+)?)")
MOTION_VALUE = re.compile(
    r"lavfi\.signalstats\.YAVG[=:](?P<value>[0-9]+(?:\.[0-9]+)?)"
)
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_ARTIFACT_BYTES = 256 * 1024 * 1024


@dataclass(frozen=True)
class MeasuredShot:
    """One machine-measured interval; semantic judgments deliberately live elsewhere."""

    id: str
    start_seconds: float
    end_seconds: float
    duration_seconds: float
    motion_median: float | None
    boundary_source: str


class ReferenceVideoService:
    """Build immutable deterministic analysis versions through a trusted media adapter."""

    def __init__(self, project_store: VideoProjectStore, media_adapter) -> None:
        self._store = project_store
        self._media = media_adapter

    def seed(
        self,
        project_id: str,
        *,
        scene_threshold: float,
        min_shot_seconds: float,
        track_hz: int,
    ) -> dict[str, Any]:
        self._bounded_number("scene_threshold", scene_threshold, 0.05, 0.80)
        self._bounded_number("min_shot_seconds", min_shot_seconds, 0.10, 5.00)
        if not isinstance(track_hz, int) or isinstance(track_hz, bool) or not 1 <= track_hz <= 10:
            raise ValueError("track_hz must be an integer from 1 to 10")
        source = self._latest_document(project_id, "source_receipt")
        source_path = Path(source["staged_path"])
        probe = self._media.probe_json(source_path)
        duration = self._probe_duration(probe)
        if round(duration, 2) != round(float(source["duration_seconds"]), 2):
            raise MediaOutputError("ffprobe duration no longer matches the source receipt")
        candidates = self._scene_candidates(source_path, scene_threshold)
        cuts = normalized_cuts(duration=duration, candidates=candidates, minimum=min_shot_seconds)
        track = self._motion_track(source_path, track_hz)
        parameters = {
            "scene_threshold": float(scene_threshold),
            "min_shot_seconds": float(min_shot_seconds),
            "track_hz": track_hz,
        }
        identity = canonical_fingerprint({"source": source, "parameters": parameters})
        analysis_id = "an_" + identity[:24]
        track_bytes = (json.dumps(track, sort_keys=True) + "\n").encode("utf-8")
        track_digest = hashlib.sha256(track_bytes).hexdigest()
        track_path = self._analysis_root(project_id, analysis_id) / "tracks" / track_digest / "track.json"
        self._publish_private_bytes(track_path, track_bytes)
        shots = self._measure_shots(cuts, track["values"], manual_cuts=set())
        payload = {
            "schema_version": "1.0",
            "analysis_id": analysis_id,
            "project_id": project_id,
            "source": source,
            "parameters": parameters,
            "cuts": cuts,
            "manual_cuts": [],
            "shots": shots,
            "track_path": str(track_path),
            "frame_checksums": {},
        }
        payload["machine_fingerprint"] = self._machine_fingerprint(payload)
        return self._store.write_version(
            project_id, "analysis", payload, schema_name="shot_analysis.schema.json"
        )

    def get_analysis(self, analysis_id: str) -> dict[str, Any]:
        matches: list[tuple[int, dict[str, Any]]] = []
        root = getattr(self._store, "_root")
        for path in root.glob("vp_*/analysis/v*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if payload.get("analysis_id") == analysis_id:
                matches.append((int(str(payload["version"])[1:]), payload))
        if not matches:
            raise KeyError(f"unknown analysis_id: {analysis_id}")
        return max(matches, key=lambda item: item[0])[1]

    def extract_frames(self, analysis_id: str, *, frame_width: int = 480) -> dict[str, Any]:
        if not isinstance(frame_width, int) or isinstance(frame_width, bool) or not 240 <= frame_width <= 960:
            raise ValueError("frame_width must be an integer from 240 to 960")
        analysis = self.get_analysis(analysis_id)
        boundary_fingerprint = self._boundary_fingerprint(analysis, frame_width)
        analysis_root = self._analysis_root(analysis["project_id"], analysis_id)
        result: dict[str, Any] = {}
        checksums: dict[str, str] = {}
        for shot in analysis["shots"]:
            measured = shot["measured"]
            start = float(measured["start_seconds"])
            duration = float(measured["duration_seconds"])
            result[shot["id"]] = {}
            for label, fraction in (("a", 0.15), ("b", 0.85)):
                at = round(start + duration * fraction, 2)
                staging_root = analysis_root / "frame_staging"
                staging_root.mkdir(mode=0o700, parents=True, exist_ok=True)
                temporary = self._temporary_path(staging_root, suffix=".png")
                try:
                    media_result = self._media.run(
                        "ffmpeg",
                        ["-hide_banner", "-nostdin", "-ss", f"{at:.2f}", "-i", analysis["source"]["staged_path"],
                         "-frames:v", "1", "-vf", f"scale={frame_width}:-2", "-y", str(temporary)],
                        timeout_seconds=30,
                    )
                    self._require_success(media_result, "frame extraction")
                    if not temporary.is_file():
                        raise MediaOutputError("ffmpeg did not create the requested frame")
                    checksum, target = self._publish_content_artifact(
                        temporary, analysis_root / "frames" / "content", suffix=".png"
                    )
                    manifest_input = {
                        "source_sha256": analysis["source"]["source_sha256"],
                        "boundary_fingerprint": boundary_fingerprint,
                        "shot_id": shot["id"],
                        "label": label,
                        "at_seconds": at,
                        "frame_width": frame_width,
                    }
                    self._write_artifact_manifest(
                        analysis_root / "frame_manifests",
                        manifest_input,
                        output_path=target,
                        output_sha256=checksum,
                    )
                finally:
                    temporary.unlink(missing_ok=True)
                checksums[f"{shot['id']}:{label}"] = {
                    "sha256": checksum,
                    "path": str(target),
                    "at_seconds": at,
                    "frame_width": frame_width,
                    "boundary_fingerprint": boundary_fingerprint,
                }
                result[shot["id"]][label] = {
                    "at_seconds": at, "path": str(target), "sha256": checksum
                }
        updated = {key: value for key, value in analysis.items() if key != "version"}
        updated["frame_checksums"] = checksums
        updated["machine_fingerprint"] = self._machine_fingerprint(updated)
        self._store.write_version(
            analysis["project_id"], "analysis", updated, schema_name="shot_analysis.schema.json"
        )
        return result

    def build_contact_sheets(
        self, analysis_id: str, *, cols: int, rows: int
    ) -> list[dict[str, Any]]:
        if (
            not isinstance(cols, int) or isinstance(cols, bool) or cols < 1
            or not isinstance(rows, int) or isinstance(rows, bool) or rows < 1
            or cols * rows > 25
        ):
            raise ValueError("contact sheet layout must contain 1 to 25 shots")
        analysis = self.get_analysis(analysis_id)
        if not self._frames_match_analysis(analysis):
            self.extract_frames(analysis_id)
            analysis = self.get_analysis(analysis_id)
        page_size = cols * rows
        pages: list[dict[str, Any]] = []
        for offset in range(0, len(analysis["shots"]), page_size):
            shots = analysis["shots"][offset : offset + page_size]
            page_number = len(pages) + 1
            sheet_input = {
                "source_sha256": analysis["source"]["source_sha256"],
                "boundary_fingerprint": self._boundary_fingerprint(
                    analysis,
                    next(iter(analysis["frame_checksums"].values()))["frame_width"],
                ),
                "layout": {"cols": cols, "rows": rows},
                "page": page_number,
                "frame_checksums": {
                    shot["id"]: analysis["frame_checksums"][f"{shot['id']}:a"]["sha256"]
                    for shot in shots
                },
                "shot_ids": [shot["id"] for shot in shots],
            }
            analysis_root = self._analysis_root(analysis["project_id"], analysis_id)
            # Validate any prior immutable result before producing another
            # deterministic observation for the same logical input.
            self._load_artifact_manifest(analysis_root / "sheet_manifests", sheet_input)
            inputs: list[str] = []
            for shot in shots:
                inputs.extend(["-i", analysis["frame_checksums"][f"{shot['id']}:a"]["path"]])
            layout = "|".join(f"{index % cols}*w0_{index // cols}*h0" for index in range(len(shots)))
            staging_root = analysis_root / "sheet_staging"
            staging_root.mkdir(mode=0o700, parents=True, exist_ok=True)
            temporary = self._temporary_path(staging_root, suffix=".png")
            try:
                filter_args = (
                    ["-filter_complex", f"xstack=inputs={len(shots)}:layout={layout}"]
                    if len(shots) > 1
                    else []
                )
                result = self._media.run(
                    "ffmpeg",
                    ["-hide_banner", "-nostdin", *inputs, *filter_args, "-frames:v", "1", "-y", str(temporary)],
                    timeout_seconds=60,
                )
                self._require_success(result, "contact sheet")
                if not temporary.is_file():
                    raise MediaOutputError("ffmpeg did not create the requested contact sheet")
                checksum, target = self._publish_content_artifact(
                    temporary, analysis_root / "sheets" / "content", suffix=".png"
                )
                self._write_artifact_manifest(
                    analysis_root / "sheet_manifests",
                    sheet_input,
                    output_path=target,
                    output_sha256=checksum,
                )
            finally:
                temporary.unlink(missing_ok=True)
            pages.append({
                "page": page_number,
                "shot_ids": [shot["id"] for shot in shots],
                "layout": {"cols": cols, "rows": rows},
                "path": str(target),
                "sha256": checksum,
            })
        return pages

    def recut(
        self, analysis_id: str, *, splits: Sequence[float], merges: Sequence[float]
    ) -> dict[str, Any]:
        if isinstance(splits, (str, bytes)) or isinstance(merges, (str, bytes)):
            raise TypeError("splits and merges must be numeric sequences")
        if len(splits) + len(merges) > 200:
            raise ValueError("recut accepts at most 200 operations")
        for value in [*splits, *merges]:
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
                raise TypeError("recut values must be finite numbers")
        analysis = self.get_analysis(analysis_id)
        duration = float(analysis["source"]["duration_seconds"])
        old_cuts = list(analysis["cuts"])
        merge_values = {round(float(value), 2) for value in merges}
        new_splits = {round(float(value), 2) for value in splits if 0 < float(value) < duration}
        cuts = [cut for cut in old_cuts if cut in (0.0, duration) or round(cut, 2) not in merge_values]
        cuts = sorted(set(cuts).union(new_splits))
        if len(cuts) < 2 or cuts[0] != 0.0 or cuts[-1] != round(duration, 2):
            raise ValueError("recut must retain source start and end")
        track = json.loads(Path(analysis["track_path"]).read_text(encoding="utf-8"))
        manual_cuts = (set(analysis["manual_cuts"]) - merge_values).union(new_splits)
        updated = {key: value for key, value in analysis.items() if key != "version"}
        updated["cuts"] = cuts
        updated["manual_cuts"] = sorted(manual_cuts)
        existing_semantics = {
            (shot["measured"]["start_seconds"], shot["measured"]["end_seconds"]): shot["semantic"]
            for shot in analysis["shots"]
        }
        updated["shots"] = self._measure_shots(
            cuts,
            track["values"],
            manual_cuts=manual_cuts,
            existing_semantics=existing_semantics,
        )
        updated["frame_checksums"] = {}
        updated["machine_fingerprint"] = self._machine_fingerprint(updated)
        return self._store.write_version(
            analysis["project_id"], "analysis", updated, schema_name="shot_analysis.schema.json"
        )

    def _scene_candidates(self, source: Path, threshold: float) -> list[float]:
        result = self._media.run(
            "ffmpeg",
            ["-hide_banner", "-nostdin", "-i", str(source), "-vf", f"select=gt(scene\\,{threshold:.2f}),showinfo", "-an", "-f", "null", "-"],
            timeout_seconds=120,
        )
        self._require_success(result, "scene detection")
        return [float(match.group("time")) for match in SCENE_ROW.finditer(result.stderr)]

    def _motion_track(self, source: Path, hz: int) -> dict[str, Any]:
        result = self._media.run(
            "ffmpeg",
            ["-hide_banner", "-nostdin", "-i", str(source), "-vf", f"fps={hz},format=gray,tmix=frames=2:weights='-1 1',signalstats,metadata=print", "-an", "-f", "null", "-"],
            timeout_seconds=120,
        )
        self._require_success(result, "motion measurement")
        values: list[dict[str, float]] = []
        current_time: float | None = None
        for line in result.stderr.splitlines():
            time_match = MOTION_TIME.search(line)
            if time_match is not None:
                current_time = float(time_match.group("time"))
            value_match = MOTION_VALUE.search(line)
            if value_match is not None and current_time is not None:
                values.append({
                    "at_seconds": round(current_time, 2),
                    "value": round(float(value_match.group("value")), 6),
                })
        return {"schema_version": "1.0", "hz": hz, "values": values}

    @staticmethod
    def _measure_shots(
        cuts,
        track_values,
        *,
        manual_cuts: set[float],
        existing_semantics: Mapping[tuple[float, float], Any] | None = None,
    ) -> list[dict[str, Any]]:
        shots = []
        semantics = existing_semantics or {}
        for index, (start, end) in enumerate(zip(cuts, cuts[1:]), 1):
            interior = [float(row["value"]) for row in track_values if start < float(row["at_seconds"]) < end]
            boundary = "source_start" if index == 1 else ("manual_split" if start in manual_cuts else "scene")
            measured = MeasuredShot(
                id=f"S{index:02d}", start_seconds=round(start, 2), end_seconds=round(end, 2),
                duration_seconds=round(end - start, 2),
                motion_median=round(statistics.median(interior), 6) if interior else None,
                boundary_source=boundary,
            )
            shots.append({
                "id": measured.id,
                "measured": {
                    "start_seconds": measured.start_seconds, "end_seconds": measured.end_seconds,
                    "duration_seconds": measured.duration_seconds, "motion_median": measured.motion_median,
                    "boundary_source": measured.boundary_source,
                },
                "semantic": semantics.get((round(start, 2), round(end, 2))),
            })
        return shots

    def _latest_document(self, project_id: str, family: str) -> dict[str, Any]:
        paths = sorted((self._store.project_root(project_id) / family).glob("v*.json"))
        if not paths:
            raise KeyError(f"project has no {family}")
        return json.loads(paths[-1].read_text(encoding="utf-8"))

    def _analysis_root(self, project_id: str, analysis_id: str) -> Path:
        if re.fullmatch(r"an_[a-f0-9]{24}", analysis_id) is None:
            raise KeyError(f"invalid analysis_id: {analysis_id}")
        root = self._store.project_root(project_id) / "analysis_artifacts" / analysis_id
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(root, 0o700)
        return root

    @staticmethod
    def _boundary_fingerprint(analysis: Mapping[str, Any], frame_width: int) -> str:
        return canonical_fingerprint({
            "source_sha256": analysis["source"]["source_sha256"],
            "cuts": analysis["cuts"],
            "measured_shots": [shot["measured"] for shot in analysis["shots"]],
            "frame_width": frame_width,
        })

    def _frames_match_analysis(self, analysis: Mapping[str, Any]) -> bool:
        checksums = analysis.get("frame_checksums")
        if not isinstance(checksums, Mapping) or not checksums:
            return False
        widths = {
            item.get("frame_width")
            for item in checksums.values()
            if isinstance(item, Mapping)
        }
        if len(widths) != 1:
            return False
        frame_width = next(iter(widths))
        if not isinstance(frame_width, int):
            return False
        expected_boundary = self._boundary_fingerprint(analysis, frame_width)
        for shot in analysis["shots"]:
            for label in ("a", "b"):
                item = checksums.get(f"{shot['id']}:{label}")
                if not isinstance(item, Mapping) or item.get("boundary_fingerprint") != expected_boundary:
                    return False
                path = Path(str(item.get("path", "")))
                if self._verified_sha256(path) != item.get("sha256"):
                    return False
        return True

    @classmethod
    def _publish_content_artifact(
        cls, temporary: Path, content_root: Path, *, suffix: str
    ) -> tuple[str, Path]:
        digest = cls._sha256(temporary)
        content_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        target = content_root / f"{digest}{suffix}"
        cls._publish_private_file(temporary, target)
        return digest, target

    @classmethod
    def _write_artifact_manifest(
        cls,
        manifest_root: Path,
        manifest_input: Mapping[str, Any],
        *,
        output_path: Path,
        output_sha256: str,
    ) -> None:
        input_fingerprint = canonical_fingerprint(manifest_input)
        payload = {
            "schema_version": "1.0",
            "input_fingerprint": input_fingerprint,
            "input": dict(manifest_input),
            "output_path": str(output_path),
            "output_sha256": output_sha256,
        }
        target = manifest_root / input_fingerprint / f"{output_sha256}.json"
        cls._publish_private_bytes(
            target, (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
        )
        loaded = cls._load_artifact_manifest(
            manifest_root,
            manifest_input,
            output_sha256=output_sha256,
        )
        if loaded != payload:
            raise MediaOutputError("artifact manifest did not round-trip exactly")

    @classmethod
    def _load_artifact_manifest(
        cls,
        manifest_root: Path,
        manifest_input: Mapping[str, Any],
        *,
        output_sha256: str | None = None,
    ) -> dict[str, Any] | None:
        input_fingerprint = canonical_fingerprint(manifest_input)
        fingerprint_root = manifest_root / input_fingerprint
        candidates = (
            [fingerprint_root / f"{output_sha256}.json"]
            if output_sha256 is not None
            else sorted(fingerprint_root.glob("*.json"))
        )
        candidates = [candidate for candidate in candidates if candidate.exists() or candidate.is_symlink()]
        if not candidates:
            return None
        selected: dict[str, Any] | None = None
        for candidate in candidates:
            try:
                manifest_bytes, _ = cls._read_verified_file(candidate)
                manifest = json.loads(manifest_bytes.decode("utf-8"))
            except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise MediaOutputError("artifact manifest is unreadable") from exc
            if manifest.get("input_fingerprint") != input_fingerprint:
                raise MediaOutputError("artifact manifest input fingerprint mismatch")
            output_path = Path(str(manifest.get("output_path", "")))
            manifest_output_sha256 = manifest.get("output_sha256")
            if (
                not isinstance(manifest_output_sha256, str)
                or candidate.stem != manifest_output_sha256
                or output_path.stem != manifest_output_sha256
                or cls._verified_sha256(output_path) != manifest_output_sha256
            ):
                raise MediaOutputError("content-addressed artifact failed checksum validation")
            if output_sha256 is not None:
                selected = manifest
        # Without an exact output digest, validation is permitted but selection
        # is not: lexicographic filenames do not express recency or preference.
        return selected

    @staticmethod
    def _machine_fingerprint(payload: Mapping[str, Any]) -> str:
        return canonical_fingerprint({
            "source": payload["source"], "parameters": payload["parameters"],
            "cuts": payload["cuts"],
            "measured_shots": [shot["measured"] for shot in payload["shots"]],
            "frame_checksums": payload["frame_checksums"],
        })

    @staticmethod
    def _probe_duration(probe: Mapping[str, Any]) -> float:
        try:
            duration = float(probe["format"]["duration"])
        except (KeyError, TypeError, ValueError) as exc:
            raise MediaOutputError("ffprobe returned no valid duration") from exc
        if not math.isfinite(duration) or duration <= 0:
            raise MediaOutputError("ffprobe duration must be positive")
        return duration

    @staticmethod
    def _bounded_number(name: str, value: float, low: float, high: float) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"{name} must be from {low} to {high}")

    @staticmethod
    def _require_success(result, operation: str) -> None:
        if result.exit_code != 0:
            raise MediaOutputError(f"{operation} failed with exit {result.exit_code}: {result.stderr.strip()}")

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _verified_sha256(path: Path) -> str:
        """Hash one regular, non-symlink file while holding its verified descriptor."""
        _, digest, _ = ReferenceVideoService._verify_stable_file(
            path,
            capture_bytes=False,
            max_bytes=MAX_ARTIFACT_BYTES,
        )
        return digest

    @staticmethod
    def _read_verified_file(path: Path) -> tuple[bytes, str]:
        """Read one file from a verified descriptor and prove its path stayed bound."""
        content, digest, _ = ReferenceVideoService._verify_stable_file(
            path,
            capture_bytes=True,
            max_bytes=MAX_MANIFEST_BYTES,
        )
        assert content is not None
        return content, digest

    @staticmethod
    def _verify_stable_file(
        path: Path, *, capture_bytes: bool, max_bytes: int
    ) -> tuple[bytes | None, str, tuple[int, int, int]]:
        try:
            before = path.lstat()
            if not stat.S_ISREG(before.st_mode):
                raise MediaOutputError("content-addressed artifact is not a regular file")
            descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        except MediaOutputError:
            raise
        except OSError as exc:
            raise MediaOutputError("content-addressed artifact cannot be opened safely") from exc
        digest = hashlib.sha256()
        chunks: list[bytes] | None = [] if capture_bytes else None
        try:
            opened = os.fstat(descriptor)
            if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                raise MediaOutputError("content-addressed artifact changed during open")
            if opened.st_size > max_bytes:
                raise MediaOutputError("verified file exceeds size limit")
            bytes_read = 0
            while chunk := os.read(descriptor, 1024 * 1024):
                bytes_read += len(chunk)
                if bytes_read > max_bytes:
                    raise MediaOutputError("verified file exceeds size limit")
                if chunks is not None:
                    chunks.append(chunk)
                digest.update(chunk)
            after = os.fstat(descriptor)
            if (
                (after.st_dev, after.st_ino, after.st_size)
                != (opened.st_dev, opened.st_ino, opened.st_size)
            ):
                raise MediaOutputError("content-addressed artifact changed during hashing")
        finally:
            os.close(descriptor)
        try:
            final_path = path.lstat()
        except OSError as exc:
            raise MediaOutputError("content-addressed artifact path disappeared") from exc
        if (
            not stat.S_ISREG(final_path.st_mode)
            or (final_path.st_dev, final_path.st_ino, final_path.st_size)
            != (opened.st_dev, opened.st_ino, opened.st_size)
        ):
            raise MediaOutputError("content-addressed artifact path changed during verification")
        identity = (opened.st_dev, opened.st_ino, opened.st_size)
        return (b"".join(chunks) if chunks is not None else None), digest.hexdigest(), identity

    @staticmethod
    def _temporary_path(parent: Path, *, suffix: str) -> Path:
        descriptor, name = tempfile.mkstemp(prefix=".pending-", suffix=suffix, dir=parent)
        os.close(descriptor)
        return Path(name)

    @classmethod
    def _publish_private_bytes(cls, path: Path, content: bytes) -> None:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = cls._temporary_path(path.parent, suffix=path.suffix)
        try:
            with temporary.open("wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            cls._publish_private_file(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _publish_private_file(temporary: Path, target: Path) -> None:
        os.chmod(temporary, 0o600)
        try:
            os.link(temporary, target, follow_symlinks=False)
        except FileExistsError:
            if (
                ReferenceVideoService._verified_sha256(temporary)
                != ReferenceVideoService._verified_sha256(target)
            ):
                raise MediaOutputError("content-addressed artifact collision")
        directory = os.open(target.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)


def normalized_cuts(*, duration: float, candidates: Sequence[float], minimum: float) -> list[float]:
    """Return a sorted, two-decimal, contiguous cut timeline with short seeds merged."""
    end = round(float(duration), 2)
    values = [0.0, *sorted({round(float(value), 2) for value in candidates if 0 < value < duration}), end]
    kept = [values[0]]
    for value in values[1:-1]:
        if value - kept[-1] >= minimum and end - value >= minimum:
            kept.append(value)
    kept.append(end)
    return kept


__all__ = ["MeasuredShot", "ReferenceVideoService", "normalized_cuts"]
