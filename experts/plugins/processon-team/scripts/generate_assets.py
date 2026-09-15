#!/usr/bin/env python3
"""Generate deterministic Codex plugin assets from the approved ProcessOn SVG."""

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


def validate_svg(source: Path) -> tuple[int, int]:
    """Return the source viewBox dimensions or raise an actionable error."""
    if not source.is_file():
        raise FileNotFoundError(f"SVG source does not exist: {source}")

    root = ET.fromstring(source.read_bytes())
    view_box = root.attrib.get("viewBox", "").split()
    if len(view_box) != 4:
        raise ValueError(f"SVG source has no valid viewBox: {source}")

    width = float(view_box[2])
    height = float(view_box[3])
    if width <= 0 or height <= 0:
        raise ValueError(f"SVG viewBox dimensions must be positive: {source}")
    return math.ceil(width), math.ceil(height)


def copy_source_svg(source: Path, destination: Path) -> None:
    """Copy the approved SVG bytes unchanged."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != destination.resolve():
        shutil.copyfile(source, destination)


def render_wordmark_png(
    source: Path,
    destination: Path,
    background: str,
) -> None:
    """Render the complete official wordmark at its native aspect ratio."""
    width, height = validate_svg(source)

    rsvg = shutil.which("rsvg-convert")
    magick = shutil.which("magick")
    if not rsvg or not magick:
        raise RuntimeError(
            "Asset generation requires existing rsvg-convert and ImageMagick "
            "executables; install them explicitly before retrying."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="processon-assets-") as temp_dir:
        rendered = Path(temp_dir) / "mark.png"
        subprocess.run(
            [
                rsvg,
                "--width",
                str(width),
                "--height",
                str(height),
                "--output",
                str(rendered),
                str(source),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        if background == "none":
            shutil.copyfile(rendered, destination)
            return
        subprocess.run(
            [
                magick,
                "-size",
                f"{width}x{height}",
                f"xc:{background}",
                str(rendered),
                "-gravity",
                "center",
                "-composite",
                "-strip",
                str(destination),
            ],
            check=True,
            capture_output=True,
            text=True,
        )


def render_composer_icon(source: Path, destination: Path) -> None:
    """Crop the official square On mark for compact composer surfaces."""
    rsvg = shutil.which("rsvg-convert")
    magick = shutil.which("magick")
    if not rsvg or not magick:
        raise RuntimeError("Composer icon generation requires rsvg-convert and ImageMagick")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="processon-icon-") as temp_dir:
        rendered = Path(temp_dir) / "wordmark.png"
        subprocess.run(
            [rsvg, "--width", "872", "--height", "250", "--output", str(rendered), str(source)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [magick, str(rendered), "-crop", "250x250+622+0", "+repage", "-resize", "64x64", "-strip", str(destination)],
            check=True,
            capture_output=True,
            text=True,
        )


def render_light_wordmark(source: Path, destination: Path) -> None:
    """Render a light-surface wordmark with dark Process and the official On mark."""
    rsvg = shutil.which("rsvg-convert")
    magick = shutil.which("magick")
    if not rsvg or not magick:
        raise RuntimeError("Light wordmark generation requires rsvg-convert and ImageMagick")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="processon-light-logo-") as temp_dir:
        rendered = Path(temp_dir) / "wordmark.png"
        left = Path(temp_dir) / "process.png"
        subprocess.run(
            [rsvg, "--width", "873", "--height", "250", "--output", str(rendered), str(source)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [magick, str(rendered), "-crop", "623x250+0+0", "+repage", "-fill", "#111111", "-colorize", "100", str(left)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [magick, str(rendered), str(left), "-geometry", "+0+0", "-composite", "-strip", str(destination)],
            check=True,
            capture_output=True,
            text=True,
        )


def generate_assets(source: Path, assets_dir: Path) -> None:
    """Copy the approved vector and generate all manifest PNG assets."""
    validate_svg(source)
    vector = assets_dir / "logo.svg"
    copy_source_svg(source, vector)
    render_wordmark_png(vector, assets_dir / "logo.png", "#2F80ED")
    render_wordmark_png(vector, assets_dir / "logo-dark.png", "none")
    render_light_wordmark(vector, assets_dir / "logo-light.png")
    render_composer_icon(vector, assets_dir / "composer-icon.png")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("assets_dir", type=Path)
    args = parser.parse_args()
    generate_assets(args.source, args.assets_dir)
    print(f"Generated ProcessOn assets in {args.assets_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
