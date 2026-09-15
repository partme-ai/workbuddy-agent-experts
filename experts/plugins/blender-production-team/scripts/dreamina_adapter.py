#!/usr/bin/env python3
"""Receipt adapter consumed by codex-dreamina-3d after local preview validation."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import uuid
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from scripts.managed_launcher import load_descriptor
from scripts.harness.media_probe import probe_video
from scripts.harness.transport import Endpoint, send_request


def build_preview_receipt(artifact: dict, request: dict, media: dict) -> dict:
    codec = str(media.get("codec", "")).lower()
    if codec not in {"h264", "avc1"}:
        raise ValueError(f"preview codec must be h264, got {codec!r}")
    frame_range = dict(request["frame_range"])
    camera_name = str(request["camera_name"])
    return {
        "schema_version": "1.0.0",
        "producer_plugin": "codex-blender",
        "producer_version": "0.3.0",
        "artifact_id": str(request["artifact_id"]),
        "path": str(artifact["path"]),
        "sha256": str(artifact["sha256"]),
        "codec": "h264",
        "container": "mp4",
        "dimensions": {"width": int(media["width"]), "height": int(media["height"])},
        "fps": float(media["fps"]),
        "duration_seconds": float(media["duration_seconds"]),
        "bytes": int(artifact["bytes"]),
        "camera": {"name": camera_name},
        "frame_range": {"start": int(frame_range["start"]), "end": int(frame_range["end"])},
        "preview_mode": "camera_render",
        "restoration": {"status": "confirmed", "evidence": "export settings restored by Harness"},
    }


def export_preview(request: dict, *, output_path, send, probe) -> dict:
    artifact_id = str(request["artifact_id"])
    transaction_id = f"preview-{artifact_id}"

    def successful(response):
        if response.get("status") != "succeeded":
            raise RuntimeError(response.get("error") or "Harness command failed")
        return response

    successful(send("transaction.begin", {}, transaction_id=transaction_id))
    committed = successful(send("transaction.commit", {}, transaction_id=transaction_id))
    snapshot_id = committed["snapshotId"]
    export_request_id = f"export-{artifact_id}"
    authorization = successful(
        send(
            "session.authorize",
            {"action": "export.file", "requestId": export_request_id, "userConfirmed": True},
            transaction_id=transaction_id,
        )
    )["result"]["authorization"]
    frame_range = request["frame_range"]
    exported = successful(
        send(
            "export.file",
            {
                "path": str(output_path),
                "snapshotId": snapshot_id,
                "overwrite": False,
                "parameters": {"frameStart": int(frame_range["start"]), "frameEnd": int(frame_range["end"])},
            },
            transaction_id=transaction_id,
            request_id=export_request_id,
            authorization=authorization,
        )
    )
    artifact = exported["result"]["artifact"]
    media = probe(Path(artifact["path"]))
    return build_preview_receipt(artifact, request, media)


def _sender(descriptor: dict):
    address = descriptor["address"]
    if descriptor["transport"] == "tcp":
        address = (address[0], int(address[1]))
    endpoint = Endpoint(descriptor["transport"], address)

    def send(command, arguments, *, transaction_id, request_id=None, authorization=None):
        payload = {
            "protocolVersion": "codex-blender/v1",
            "sessionId": descriptor["sessionId"],
            "requestId": request_id or str(uuid.uuid4()),
            "transactionId": transaction_id,
            "command": command,
            "arguments": arguments,
        }
        if authorization:
            payload["authorization"] = authorization
        return send_request(endpoint, descriptor["token"], payload, timeout=120)

    return send


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="codex-dreamina-3d preview adapter for an active Blender Harness")
    parser.add_argument("--descriptor", default=os.environ.get("CODEX_BLENDER_DESCRIPTOR"))
    parser.add_argument("--request", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--output")
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args(argv)
    receipt_path = Path(args.receipt)
    try:
        if args.status:
            if receipt_path.is_file():
                return 0
            receipt_path.write_text(json.dumps({"status": "unknown"}))
            return 2
        if not args.descriptor:
            raise ValueError("--descriptor or CODEX_BLENDER_DESCRIPTOR is required")
        descriptor = load_descriptor(Path(args.descriptor))
        request = json.loads(Path(args.request).read_text())
        send = _sender(descriptor)
        if args.inspect:
            response = send("scene.inspect", {}, transaction_id="inspect")
            if response.get("status") != "succeeded":
                raise RuntimeError(response.get("error"))
            receipt = {"status": "ready", "scene": request.get("scene"), "details": response["result"]}
        else:
            if not args.output:
                raise ValueError("--output is required for preview export")
            ffprobe = os.environ.get("CODEX_BLENDER_FFPROBE") or shutil.which("ffprobe")
            if not ffprobe:
                raise FileNotFoundError("ffprobe is required for preview validation")
            receipt = export_preview(
                request,
                output_path=args.output,
                send=send,
                probe=lambda path: probe_video(path, Path(ffprobe)),
            )
        receipt_path.write_text(json.dumps(receipt))
        return 0
    except Exception as exc:
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps({"status": "failed", "error": str(exc)}))
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
