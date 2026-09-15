"""Canonical approved-root checks for input assets."""

from pathlib import Path

from .errors import HarnessError


class PathPolicy:
    def __init__(self, approved_roots):
        self.roots = tuple(Path(root).resolve() for root in approved_roots)

    def require_file(self, value) -> Path:
        path = Path(value)
        if path.is_symlink():
            raise HarnessError("ASSET_NOT_AUTHORIZED", f"asset must not be a symlink: {path}")
        resolved = path.resolve()
        if not resolved.is_file():
            raise HarnessError("ASSET_NOT_FOUND", f"asset file not found: {resolved}")
        if not any(self._under(resolved, root) for root in self.roots):
            raise HarnessError("ASSET_NOT_AUTHORIZED", f"asset is outside approved roots: {resolved}")
        return resolved

    @staticmethod
    def _under(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False

