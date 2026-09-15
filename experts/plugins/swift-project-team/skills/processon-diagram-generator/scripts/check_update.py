#!/usr/bin/env python3
"""Explicitly compare the bundled ProcessOn skill version with a remote manifest."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
LOCAL_MANIFEST = SKILL_DIR / "version" / "github-version.json"
DEFAULT_REMOTE = (
    "https://raw.githubusercontent.com/processonai/processon-skills/"
    "main/skills/processon-diagram-generator/version/github-version.json"
)


def version_tuple(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in value.lstrip("v").split("."))
    except ValueError as exc:
        raise ValueError(f"invalid semantic version: {value!r}") from exc


def load_remote(url: str, timeout: float) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("PROCESSON_VERSION_URL", DEFAULT_REMOTE))
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()
    try:
        local = json.loads(LOCAL_MANIFEST.read_text(encoding="utf-8"))
        remote = load_remote(args.url, args.timeout)
        local_version = local["version"]
        remote_version = remote["version"]
        result = {
            "localVersion": local_version,
            "remoteVersion": remote_version,
            "updateAvailable": version_tuple(remote_version) > version_tuple(local_version),
            "changelog": remote.get("changelog", ""),
        }
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR    unable to check update: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
