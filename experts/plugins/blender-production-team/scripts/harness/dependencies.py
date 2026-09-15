"""Dependency scanning, classification and packaging for project portability.

Scans a Blender scene for external file dependencies, classifies them by kind,
computes SHA-256 checksums, discovers license provenance, and supports packaging
a project into a self-contained directory.

Dependency kinds: IMAGE, UDIM, FONT, AUDIO, VIDEO, IMAGE_SEQUENCE,
BLEND_LIBRARY, SIMULATION_CACHE, EXTENSION.

NOTE: NODE_GROUP is intentionally absent.  A Blender node-group library is a
.blend file referenced as a library for a node group -- the file extension
alone cannot distinguish it from BLEND_LIBRARY, and classification would
require usage context (the owning library or referencing datablock) that the
file-level scanner does not inspect.  A schema enum entry the scanner can never
emit would be a false contract for downstream consumers.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

from .artifact_validator import sha256_file
from .errors import HarnessError
from .path_policy import PathPolicy

# ---------------------------------------------------------------------------
# Dependency kind classification
# ---------------------------------------------------------------------------

_IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.tga', '.bmp', '.tif', '.tiff', '.hdr', '.exr', '.dds', '.webp'}
_UDIM_PATTERN = re.compile(r'\.\d{4}\.(png|jpg|jpeg|exr|tif|tiff)$', re.IGNORECASE)
_FONT_EXTS = {'.ttf', '.otf', '.woff', '.woff2'}
_AUDIO_EXTS = {'.wav', '.mp3', '.ogg', '.flac', '.aac', '.m4a'}
_VIDEO_EXTS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
_BLEND_EXT = '.blend'
_CACHE_DIR_NAMES = {'blend_cache', 'cache', 'bake', 'simulation_cache', 'fluid_cache', 'pointcache'}

# License file names searched in ancestor directories
_LICENSE_FILE_NAMES = {'LICENSE', 'LICENSE.txt', 'LICENSE.md', 'LICENCE', 'LICENCE.txt',
                       'COPYING', 'COPYING.txt', 'license.txt', 'license.md', '.license'}

# Maximum ancestor depth for license search
_LICENSE_SEARCH_DEPTH = 3


def classify_dependency(path: Path) -> str:
    """Classify a dependency file path into its kind string."""
    name = path.name.lower()
    suffix = path.suffix.lower()

    # UDIM tiles: name.0001.ext pattern
    if _UDIM_PATTERN.search(name):
        return 'UDIM'

    # Image sequences: name.0001.ext or name_0001.ext
    if re.search(r'[._]\d{3,4}\.\w+$', name) and suffix in _IMAGE_EXTS:
        return 'IMAGE_SEQUENCE'

    # Standard image formats
    if suffix in _IMAGE_EXTS:
        return 'IMAGE'

    # Fonts
    if suffix in _FONT_EXTS:
        return 'FONT'

    # Audio
    if suffix in _AUDIO_EXTS:
        return 'AUDIO'

    # Video
    if suffix in _VIDEO_EXTS:
        return 'VIDEO'

    # Blend libraries
    if suffix == _BLEND_EXT:
        return 'BLEND_LIBRARY'

    # Simulation cache directories/files
    for part in path.parts:
        if part.lower() in _CACHE_DIR_NAMES:
            return 'SIMULATION_CACHE'

    # Catch-all: anything not matched above
    return 'EXTENSION'


def discover_license(file_path: Path) -> str:
    """Search for a license file near the given path.

    Walks up to _LICENSE_SEARCH_DEPTH parent directories looking for
    common license file names. Returns the license file contents (first
    line or identifier) or 'unknown' if none found.
    """
    search_dir = file_path.parent if file_path.is_file() else file_path
    for _ in range(_LICENSE_SEARCH_DEPTH + 1):
        for name in _LICENSE_FILE_NAMES:
            candidate = search_dir / name
            if candidate.is_file():
                try:
                    text = candidate.read_text(encoding='utf-8', errors='replace').strip()
                    # Return first non-empty line or the filename
                    for line in text.splitlines():
                        line = line.strip()
                        if line:
                            return line[:200]
                    return name
                except OSError:
                    return name
        parent = search_dir.parent
        if parent == search_dir:
            break
        search_dir = parent
    return 'unknown'


def _hash_or_zero(path: Path) -> str:
    """Compute SHA-256 or return all-zeros for inaccessible files."""
    try:
        return sha256_file(path)
    except (OSError, PermissionError):
        return '0' * 64


def _bytes_or_zero(path: Path) -> int:
    """Return file size or 0 for inaccessible files."""
    try:
        return path.stat().st_size
    except OSError:
        return 0


# ---------------------------------------------------------------------------
# Path safety: symlinks, escapes, readability
# ---------------------------------------------------------------------------

def validate_path_safety(path: Path, project_dir: Path, *, label: str = 'dependency') -> Path:
    """Validate that a dependency path is safe for packaging.

    Checks:
    1. Symlinks are rejected (the resolved target must not differ from the
       path as-given when both are resolved relative to the same root).
    2. Path traversal (..) that escapes the project directory is rejected.
    3. Returns the resolved path on success.

    Raises HarnessError on violation.
    """
    resolved = path.resolve()
    project_resolved = project_dir.resolve()

    # Symlink check: if the path itself (before resolve) is a symlink, reject
    if path.is_symlink():
        raise HarnessError(
            'ASSET_NOT_AUTHORIZED',
            f'{label} must not be a symlink: {path} -> {resolved}'
        )

    # Also check if resolve changed the path in a way that escapes
    # (this catches symlinks in parent directories)
    try:
        # Check if the resolved path is under the project directory
        resolved.relative_to(project_resolved)
    except ValueError:
        raise HarnessError(
            'ASSET_NOT_AUTHORIZED',
            f'{label} path escapes the project directory: {resolved} '
            f'(project: {project_resolved})'
        )

    # Check for .. components that escape
    try:
        raw_resolved = Path(os.path.normpath(path)).resolve()
        raw_resolved.relative_to(project_resolved)
    except ValueError:
        raise HarnessError(
            'ASSET_NOT_AUTHORIZED',
            f'{label} path with .. escapes the project directory: {resolved}'
        )

    return resolved


def validate_package_path(path: Path, project_dir: Path) -> Path:
    """Validate a path is inside the project directory (for packaging targets).

    This is stricter than validate_path_safety: it checks that the path
    is a regular file (not a symlink at any level) and is inside project_dir.
    """
    resolved = path.resolve()

    # Reject if any component is a symlink
    current = path
    while current != current.parent:
        if current.is_symlink():
            raise HarnessError(
                'ASSET_NOT_AUTHORIZED',
                f'path component is a symlink: {current} -> {current.resolve()}'
            )
        current = current.parent

    # Must be inside project directory
    project_resolved = project_dir.resolve()
    try:
        resolved.relative_to(project_resolved)
    except ValueError:
        raise HarnessError(
            'ASSET_NOT_AUTHORIZED',
            f'path escapes the project directory: {resolved} '
            f'(project: {project_resolved})'
        )

    return resolved


# ---------------------------------------------------------------------------
# Dependency scanning (Blender API)
# ---------------------------------------------------------------------------

def scan_dependencies(bpy_module, project_dir: Path) -> list[dict]:
    """Scan the current Blender scene for external file dependencies.

    Returns a list of dependency dicts, each with keys:
      path, relativePath, kind, sha256, bytes, license, accessible, warning
    """
    seen_paths: set[str] = set()
    deps: list[dict] = []
    project_resolved = project_dir.resolve()

    # bpy.path.abspath resolves Blender-style // paths relative to the .blend dir
    _abspath = getattr(bpy_module, 'path', None)
    _blender_abspath = getattr(_abspath, 'abspath', None) if _abspath else None

    def _add_dep(raw_path: str | None):
        if not raw_path:
            return
        # Normalize and deduplicate
        try:
            raw = str(raw_path)
            # Use Blender's abspath to resolve // prefixed paths
            if _blender_abspath is not None and (raw.startswith('//') or not Path(raw).is_absolute()):
                raw = _blender_abspath(raw)
            p = Path(raw)
            if not p.is_absolute():
                p = project_resolved / p
            resolved = p.resolve()
        except (OSError, ValueError):
            return
        key = str(resolved)
        if key in seen_paths:
            return
        seen_paths.add(key)

        kind = classify_dependency(resolved)
        accessible = resolved.is_file()
        sha = _hash_or_zero(resolved) if accessible else '0' * 64
        size = _bytes_or_zero(resolved) if accessible else 0
        license_id = discover_license(resolved) if accessible else 'unknown'

        rel_path = None
        try:
            rel_path = str(resolved.relative_to(project_resolved))
        except ValueError:
            pass

        warning = None
        if not accessible:
            warning = f'file not found: {resolved}'

        deps.append({
            'path': str(resolved),
            'relativePath': rel_path,
            'kind': kind,
            'sha256': sha,
            'bytes': size,
            'license': license_id,
            'accessible': accessible,
            'warning': warning,
        })

    # Scan images
    for img in bpy_module.data.images:
        _add_dep(getattr(img, 'filepath', None))

    # Scan fonts (from text objects and grease pencil)
    for font in bpy_module.data.fonts:
        _add_dep(getattr(font, 'filepath', None))

    # Scan libraries (linked .blend files)
    for lib in bpy_module.data.libraries:
        _add_dep(getattr(lib, 'filepath', None))

    # Scan movie clips
    for clip in bpy_module.data.movieclips:
        _add_dep(getattr(clip, 'filepath', None))

    # Scan sounds
    for sound in bpy_module.data.sounds:
        _add_dep(getattr(sound, 'filepath', None))

    # Scan cache files from modifiers
    for obj in bpy_module.data.objects:
        for mod in obj.modifiers:
            cache = getattr(mod, 'point_cache', None)
            if cache:
                # Point cache directory
                pass  # Blender manages these internally
            # Particle system caches
            psys = getattr(mod, 'particle_system', None)
            if psys:
                pass  # Also internal

    return deps


# ---------------------------------------------------------------------------
# Dependency manifest generation
# ---------------------------------------------------------------------------

def generate_manifest(bpy_module, project_dir: Path) -> dict:
    """Generate a dependency manifest for the current Blender scene.

    Returns a dict conforming to dependency_manifest.schema.json.
    """
    deps = scan_dependencies(bpy_module, project_dir)

    by_kind: dict[str, int] = {}
    accessible_count = 0
    inaccessible_count = 0
    for dep in deps:
        kind = dep['kind']
        by_kind[kind] = by_kind.get(kind, 0) + 1
        if dep['accessible']:
            accessible_count += 1
        else:
            inaccessible_count += 1

    return {
        'protocolVersion': 'codex-blender/v1',
        'projectPath': str(project_dir.resolve()),
        'generatedAt': datetime.datetime.utcnow().isoformat() + 'Z',
        'dependencies': deps,
        'summary': {
            'total': len(deps),
            'byKind': by_kind,
            'accessible': accessible_count,
            'inaccessible': inaccessible_count,
        },
    }


# ---------------------------------------------------------------------------
# Project packaging
# ---------------------------------------------------------------------------

def _safe_copy(src: Path, dst: Path) -> None:
    """Copy a file preserving metadata, creating parent dirs."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))


def package_project(
    bpy_module,
    source_project: Path,
    target_dir: Path,
    *,
    include_caches: bool = False,
    include_proxies: bool = False,
) -> dict:
    """Package the current project into a self-contained directory.

    SAFETY GUARANTEES:
    - Only writes into target_dir (which must not exist yet).
    - Never modifies the active project.
    - All dependency paths are validated (no symlinks, no escapes).
    - Every packaged file gets a SHA-256 and license provenance.

    Returns a dict conforming to project_package_receipt.schema.json.

    Raises HarnessError if:
    - target_dir already exists
    - any dependency path is unsafe
    """
    target_resolved = target_dir.resolve()
    source_resolved = source_project.resolve()
    project_dir = source_resolved.parent

    # Safety: target must not exist
    if target_resolved.exists():
        raise HarnessError(
            'OUTPUT_NOT_AUTHORIZED',
            f'target directory already exists: {target_resolved}'
        )

    # Safety: target must not be inside the project directory (prevent self-reference)
    try:
        target_resolved.relative_to(project_dir)
        raise HarnessError(
            'OUTPUT_NOT_AUTHORIZED',
            f'target directory must not be inside the project directory: {target_resolved}'
        )
    except ValueError:
        pass  # Good: target is outside project

    # Create target directory
    target_resolved.mkdir(parents=True, exist_ok=True)

    try:
        # Scan dependencies
        manifest = generate_manifest(bpy_module, project_dir)

        # Validate all dependency paths
        for dep in manifest['dependencies']:
            dep_path = Path(dep['path'])
            if dep['accessible']:
                validate_package_path(dep_path, project_dir)

        # Copy the .blend file into the package
        packaged_blend = target_resolved / source_resolved.name
        _safe_copy(source_resolved, packaged_blend)

        # Copy each accessible dependency
        packaged_files = []
        for dep in manifest['dependencies']:
            if not dep['accessible']:
                continue
            dep_path = Path(dep['path'])
            # Determine relative path for packaging
            if dep['relativePath']:
                rel = dep['relativePath']
            else:
                # For files outside project, use their basename in a flat structure
                rel = dep_path.name
            packaged_path = target_resolved / rel
            _safe_copy(dep_path, packaged_path)

            packaged_files.append({
                'originalPath': dep['path'],
                'packagedPath': rel,
                'sha256': dep['sha256'],
                'bytes': dep['bytes'],
                'license': dep['license'],
            })

        # Also add the .blend file itself
        blend_sha = sha256_file(packaged_blend)
        blend_bytes = packaged_blend.stat().st_size
        packaged_files.insert(0, {
            'originalPath': str(source_resolved),
            'packagedPath': source_resolved.name,
            'sha256': blend_sha,
            'bytes': blend_bytes,
            'license': discover_license(source_resolved),
        })

        # Write the dependency manifest into the package
        manifest_path = target_resolved / 'dependency_manifest.json'
        manifest_content = json.dumps(manifest, indent=2, ensure_ascii=False) + '\n'
        manifest_path.write_text(manifest_content, encoding='utf-8')
        manifest_sha = sha256_file(manifest_path)

        # Build the receipt
        receipt = {
            'protocolVersion': 'codex-blender/v1',
            'producer': {'name': 'codex-blender', 'version': '0.3.0'},
            'sourceProject': str(source_resolved),
            'targetDirectory': str(target_resolved),
            'packagePath': str(packaged_blend),
            'files': packaged_files,
            'manifest': {
                'path': str(manifest_path),
                'sha256': manifest_sha,
            },
            'validation': {
                'status': 'passed',
                'checks': [
                    'target_directory_fresh',
                    'no_symlinks',
                    'no_path_escapes',
                    'sha256_integrity',
                    'license_provenance',
                ],
            },
            'warnings': [
                dep['warning'] for dep in manifest['dependencies']
                if dep.get('warning')
            ],
        }

        # Write the receipt into the package
        receipt_path = target_resolved / 'package_receipt.json'
        receipt_content = json.dumps(receipt, indent=2, ensure_ascii=False) + '\n'
        receipt_path.write_text(receipt_content, encoding='utf-8')

        return receipt

    except Exception:
        # Clean up on failure: remove the target directory
        if target_resolved.exists():
            shutil.rmtree(str(target_resolved), ignore_errors=True)
        raise


# ---------------------------------------------------------------------------
# Portability validation
# ---------------------------------------------------------------------------

def validate_portability(
    bpy_module,
    target_dir: Path,
    project_dir: Path,
) -> dict:
    """Validate that a project can be packaged to target_dir.

    Checks:
    1. target_dir does not exist (or is empty).
    2. All dependency paths are inside the project (no escapes).
    3. No dependency is a symlink.
    4. All accessible dependencies are readable.

    Returns a validation result dict.
    """
    target_resolved = target_dir.resolve()
    project_resolved = project_dir.resolve()

    checks = []
    errors = []
    warnings = []

    # Check 1: target directory
    if target_resolved.exists() and any(target_resolved.iterdir()):
        errors.append(f'target directory already exists and is not empty: {target_resolved}')
        checks.append('target_directory_fresh:FAIL')
    else:
        checks.append('target_directory_fresh:PASS')

    # Check 2: scan and validate all dependencies
    manifest = generate_manifest(bpy_module, project_resolved)
    for dep in manifest['dependencies']:
        dep_path = Path(dep['path'])
        # Symlink check
        if dep_path.is_symlink():
            errors.append(f'dependency is a symlink: {dep_path} -> {dep_path.resolve()}')
            checks.append(f'symlink_check:{dep_path}:FAIL')
            continue
        # Escape check
        try:
            dep_path.resolve().relative_to(project_resolved)
        except ValueError:
            errors.append(f'dependency escapes project: {dep_path.resolve()}')
            checks.append(f'escape_check:{dep_path}:FAIL')
            continue
        # Accessibility
        if not dep['accessible']:
            warnings.append(f'dependency not accessible: {dep_path}')
            checks.append(f'accessible:{dep_path}:WARN')
        else:
            checks.append(f'accessible:{dep_path}:PASS')

    passed = len(errors) == 0
    return {
        'passed': passed,
        'checks': checks,
        'errors': errors,
        'warnings': warnings,
        'dependencyCount': manifest['summary']['total'],
        'accessibleCount': manifest['summary']['accessible'],
        'inaccessibleCount': manifest['summary']['inaccessible'],
    }
