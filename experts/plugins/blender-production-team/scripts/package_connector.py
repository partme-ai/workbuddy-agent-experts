"""Copy the pinned PartMe Blender MCP Add-on release artifact."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.partme_runtime import locked_artifact


def package_connector(target: Path) -> Path:
    source, _lock = locked_artifact(ROOT, "addon")
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    args = parser.parse_args()
    print(package_connector(Path(args.output)))
