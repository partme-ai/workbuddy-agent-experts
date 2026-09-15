"""Build an installable Connector zip with the shared Harness core."""

from __future__ import annotations

import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONNECTOR = ROOT / "connector" / "codex_blender_connector"
HARNESS = ROOT / "scripts" / "harness"


def _source_files(root: Path):
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def package_connector(target: Path) -> Path:
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in _source_files(CONNECTOR):
            archive.write(path, "codex_blender_connector/" + str(path.relative_to(CONNECTOR)))
        for path in _source_files(HARNESS):
            archive.write(path, "codex_blender_connector/harness/" + str(path.relative_to(HARNESS)))
        archive.write(
            ROOT / "scripts" / "validate_model_in_blender.py",
            "codex_blender_connector/validate_model_in_blender.py",
        )
    return target


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    args = parser.parse_args()
    print(package_connector(Path(args.output)))
