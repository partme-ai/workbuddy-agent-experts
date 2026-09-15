#!/usr/bin/env python3
"""Launch the Stitch Design local stdio MCP proxy."""

from __future__ import annotations

import sys
from pathlib import Path


def require_supported_python(version_info=sys.version_info) -> bool:
    """Reject interpreters that cannot run the supported proxy implementation."""

    if tuple(version_info[:2]) < (3, 11):
        print("Stitch Design MCP requires Python 3.11 or newer on PATH.", file=sys.stderr)
        return False
    return True


if not require_supported_python():
    raise SystemExit(1)


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from stitch_harness.mcp_proxy import serve_stdio  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(serve_stdio())
