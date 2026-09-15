#!/usr/bin/env python3
"""Installed-plugin entry point for the local ProcessOn MCP proxy."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from processon_harness.mcp_proxy import main


if __name__ == "__main__":
    raise SystemExit(main())
