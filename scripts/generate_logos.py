#!/usr/bin/env python3
"""Generate team logo icons into teams/<id>/logo.png (static, tracked assets).

Design: 256x256 rounded-square, two-tone — category color background,
white initials derived from the team id (first letters of words, max 2).
Requires Pillow only on the machine that runs this generator; the output
is committed so builds/installers never need it.

Usage: python3 scripts/generate_logos.py [--force]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]

CATEGORY_COLORS = {
    "01": (109, 40, 217),   # ProductDesign  — purple
    "02": (29, 78, 216),    # Engineering    — blue
    "03": (4, 120, 87),     # Quality        — green
    "04": (14, 116, 144),   # Documentation  — cyan
    "05": (190, 24, 93),    # Marketing      — pink
    "06": (180, 83, 9),     # Content        — amber
    "07": (194, 65, 12),    # Sales          — orange
    "12": (55, 65, 81),     # Industry       — gray
}
DEFAULT_COLOR = (55, 65, 81)

FONT_CANDIDATES = [
    "/System/Library/Fonts/Helvetica.ttc",            # macOS
    "/System/Library/Fonts/SFNS.ttf",                 # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",       # Linux alt
    "C:/Windows/Fonts/arialbd.ttf",                   # Windows
]


def _load_font(size: int):
    for cand in FONT_CANDIDATES:
        if Path(cand).is_file():
            try:
                return ImageFont.truetype(cand, size)
            except Exception:
                continue
    return ImageFont.load_default()


def initials(team_id: str) -> str:
    """First letters of the first two significant words, e.g.
    java-backend-team -> JB, cn-intel-team -> CI, 3d-production -> 3D."""
    words = re.split(r"[-_]+", team_id)
    letters: list[str] = []
    for w in words:
        if w in ("team",):
            continue
        if w:
            letters.append(w[0].upper())
        if len(letters) == 2:
            break
    return "".join(letters) or "WB"


def rounded_rect(size: int, radius: int, color) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=color)
    return img


def make_icon(team_id: str, category: str, out: Path, force: bool) -> bool:
    if out.is_file() and not force:
        return False
    cat = category.split("-")[0]
    color = CATEGORY_COLORS.get(cat, DEFAULT_COLOR)
    size, radius = 256, 56
    img = rounded_rect(size, radius, color)
    draw = ImageDraw.Draw(img)
    letters = initials(team_id)
    font = _load_font(110)
    bbox = draw.textbbox((0, 0), letters, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1]),
              letters, fill=(255, 255, 255), font=font)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="regenerate even if logo.png exists")
    args = ap.parse_args()

    generated = skipped = 0
    for team_yaml in sorted((ROOT / "teams").glob("*.yaml")):
        text = team_yaml.read_text(encoding="utf-8")
        m = re.search(r"^id:\s*(\S+)", text, re.M)
        c = re.search(r"^category:\s*(\S+)", text, re.M)
        if not m:
            continue
        team_id = m.group(1)
        category = c.group(1) if c else ""
        out = ROOT / "teams" / team_id / "logo.png"
        if make_icon(team_id, category, out, args.force):
            generated += 1
        else:
            skipped += 1
    print(f"logos generated: {generated}, skipped (existing): {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
