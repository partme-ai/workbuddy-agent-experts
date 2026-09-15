#!/usr/bin/env python3
"""Refresh SHA-256 checksums in config/blender-release-matrix.json.

This script is READ-ONLY with respect to the version list. It never adds,
removes, or substitutes a version. It only re-fetches each version's official
``blender-<ver>.sha256`` file and updates the recorded checksums and artifact
names for the combinations already declared in the config.

The fetcher is injectable so unit tests can drive it offline.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "blender-release-matrix.json"

SHA256_LINE_RE = re.compile(r"^([0-9a-f]{64})\s{2}(\S+)$")


class MissingArtifactError(Exception):
    """A required artifact filename was not found in the sha256 file."""


class MalformedLineError(Exception):
    """A line in the sha256 file does not match the expected format."""


@dataclass
class Sha256Entry:
    sha256: str
    filename: str


def _default_fetcher(version: str, blender_dir: str) -> str:
    """Fetch the official sha256 file for a Blender version."""
    url = f"https://download.blender.org/release/{blender_dir}/blender-{version}.sha256"
    req = urllib.request.Request(url, headers={"User-Agent": "codex-blender-plugin/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_sha256_content(
    content: str,
    required_artifacts: list[str] | None = None,
) -> list[Sha256Entry]:
    """Parse sha256sum-format content and optionally verify required artifacts.

    Args:
        content: The raw text of a .sha256 file.
        required_artifacts: If provided, every filename in this list must appear
            in the parsed entries, or MissingArtifactError is raised.

    Returns:
        List of Sha256Entry objects.

    Raises:
        MalformedLineError: If any line does not match the sha256sum format.
        MissingArtifactError: If a required artifact is not found.
    """
    entries: list[Sha256Entry] = []
    for line in content.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        m = SHA256_LINE_RE.match(line)
        if not m:
            raise MalformedLineError(f"malformed sha256 line: {line!r}")
        entries.append(Sha256Entry(sha256=m.group(1), filename=m.group(2)))

    if required_artifacts is not None:
        found = {e.filename for e in entries}
        for artifact in required_artifacts:
            if artifact not in found:
                raise MissingArtifactError(
                    f"required artifact {artifact!r} not found in sha256 file; "
                    f"available: {sorted(found)}"
                )

    return entries


def update_combinations(
    combinations: list[dict],
    fetcher: callable = _default_fetcher,
) -> None:
    """Update sha256/artifact fields for each combination in-place.

    The fetcher is called with (version, blender_dir) and must return the raw
    text of the official .sha256 file.

    Raises:
        MissingArtifactError: If the official file is missing a required artifact.
        MalformedLineError: If the sha256 file has malformed lines.
    """
    for combo in combinations:
        version = combo["version"]
        platform = combo["platform"]

        # Derive the Blender directory (e.g., "4.2.23" -> "Blender4.2")
        major_minor = ".".join(version.split(".")[:2])
        blender_dir = f"Blender{major_minor}"

        # Derive expected artifact filename
        if platform == "macos-arm64":
            expected_artifact = f"blender-{version}-macos-arm64.dmg"
        elif platform == "windows-x64":
            expected_artifact = f"blender-{version}-windows-x64.zip"
        else:
            raise ValueError(f"unknown platform: {platform}")

        content = fetcher(version, blender_dir)
        entries = parse_sha256_content(
            content, required_artifacts=[expected_artifact]
        )

        matching = [e for e in entries if e.filename == expected_artifact]
        combo["sha256"] = matching[0].sha256
        combo["artifact"] = matching[0].filename
        print(f"  {version}/{platform}: {matching[0].sha256[:16]}... OK")


def main() -> int:
    """Run the updater against the live site."""
    config_path = CONFIG_PATH
    if not config_path.exists():
        print(f"ERROR: config not found: {config_path}", file=sys.stderr)
        return 1

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    combinations = config.get("combinations", [])
    if not combinations:
        print("ERROR: no combinations in config", file=sys.stderr)
        return 1

    print(f"Updating {len(combinations)} combinations...")
    try:
        update_combinations(combinations)
    except (MissingArtifactError, MalformedLineError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Only write after all updates succeed (no partial writes).
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Config written to {config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
