#!/usr/bin/env python3
"""CLI client for an active managed or Connector Harness session."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from scripts.managed_launcher import load_descriptor
from scripts.harness.transport import Endpoint, send_request


def _endpoint(descriptor):
    address = descriptor["address"]
    if descriptor["transport"] == "tcp":
        address = (address[0], int(address[1]))
    return Endpoint(descriptor["transport"], address)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Send a JSON command to Codex Blender Harness")
    parser.add_argument("--descriptor", required=True)
    parser.add_argument("--request", required=True, help="request JSON file")
    args = parser.parse_args(argv)
    try:
        descriptor = load_descriptor(Path(args.descriptor))
        request = json.loads(Path(args.request).read_text())
        response = send_request(_endpoint(descriptor), descriptor["token"], request)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": {"code": "CLIENT_ERROR", "message": str(exc)}}), file=sys.stderr)
        return 1
    print(json.dumps(response))
    return 0 if response.get("status") != "failed" and "error" not in response else 1


if __name__ == "__main__":
    raise SystemExit(main())
