"""Load the pinned PartMe Blender MCP release without maintaining a second runtime."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
import zipfile
from pathlib import Path


class RuntimeIntegrationError(RuntimeError):
    """Pinned runtime is missing, corrupt, or structurally unsafe."""


def _load_lock(plugin_root: Path) -> dict:
    path = plugin_root / "runtime.lock.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeIntegrationError("runtime.lock.json is missing or invalid") from error
    required = {"schemaVersion", "product", "version", "repository", "release", "artifacts"}
    if set(data) != required or data["schemaVersion"] != "1.0.0":
        raise RuntimeIntegrationError("runtime lock has an unsupported schema")
    if data["product"] != "PartMe Blender MCP" or data["repository"] != "https://github.com/partme-ai/blender-mcp":
        raise RuntimeIntegrationError("runtime lock points to an unexpected product")
    return data


def locked_artifact(plugin_root: Path, kind: str) -> tuple[Path, dict]:
    plugin_root = Path(plugin_root).resolve()
    data = _load_lock(plugin_root)
    artifact = data.get("artifacts", {}).get(kind)
    if not isinstance(artifact, dict) or set(artifact) != {"path", "url", "sha256"}:
        raise RuntimeIntegrationError(f"runtime lock has no valid {kind} artifact")
    candidate = plugin_root / artifact["path"]
    if candidate.is_symlink():
        raise RuntimeIntegrationError(f"pinned {kind} artifact is missing or unsafe")
    path = candidate.resolve()
    if not path.is_relative_to(plugin_root) or not path.is_file():
        raise RuntimeIntegrationError(f"pinned {kind} artifact is missing or unsafe")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != artifact["sha256"]:
        raise RuntimeIntegrationError(f"pinned {kind} artifact failed SHA-256 verification")
    return path, data


def activate_runtime(plugin_root: Path | None = None) -> dict:
    plugin_root = Path(plugin_root or Path(__file__).resolve().parents[1]).resolve()
    archive, lock = locked_artifact(plugin_root, "runtime")
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if "pyproject.toml" not in names or "src/partme_blender_mcp/__init__.py" not in names:
            raise RuntimeIntegrationError("pinned runtime archive is not an installable PartMe release")
        for name in names:
            path = Path(name)
            if path.is_absolute() or ".." in path.parts:
                raise RuntimeIntegrationError("pinned runtime archive contains an unsafe path")
    import_root = str(archive) + "/src"
    if import_root not in sys.path:
        sys.path.insert(0, import_root)
    module = importlib.import_module("partme_blender_mcp")
    if getattr(module, "__version__", None) != lock["version"]:
        raise RuntimeIntegrationError("pinned runtime version does not match runtime.lock.json")
    return {"version": lock["version"], "archive": str(archive), "importRoot": import_root}
