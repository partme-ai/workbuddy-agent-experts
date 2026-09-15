#!/usr/bin/env python3
"""Start the pinned PartMe Blender MCP runtime bundled with the Codex plugin."""

from __future__ import annotations

import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from scripts.partme_runtime import activate_runtime

activate_runtime(PLUGIN_ROOT)

from partme_blender_mcp.__main__ import main


if __name__ == "__main__":
    raise SystemExit(main())
