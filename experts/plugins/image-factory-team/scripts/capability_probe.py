#!/usr/bin/env python3
"""Probe whether this machine can run an Image Factory batch.

The probe is deliberately offline and read-only. It inspects the filesystem and
the Codex configuration; it never performs a network call, never reads or copies
authentication material, and never spawns the Codex binary. A probe that can be
executed by accident must not be able to spend anything.

It also never guesses the image model. The model used for generation is selected
by Codex, so the reported `model_reported` is `null` here and the fields that
cannot be established offline are listed under `unverified` instead of being
filled with a plausible-looking value.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - the plugin requires 3.11+
    tomllib = None  # type: ignore[assignment]

SCHEMA_VERSION = "1.0.0"
BINARY_NAME = "codex"
APPSERVER_RELATIVE = Path("plugins") / ".plugin-appserver" / BINARY_NAME
GENERATION_DIR_NAME = "generated_images"
AUTH_FILE_NAME = "auth.json"
CONFIG_FILE_NAME = "config.toml"
FEATURE_KEY = "image_generation"

# Providers known to withhold the image capability from the model provider
# capability set (codex-rs model-provider/src/amazon_bedrock/mod.rs:217).
PROVIDERS_WITHOUT_IMAGE_GENERATION = ("amazon-bedrock", "bedrock")

UNVERIFIED_OFFLINE = (
    "model_is_chosen_by_codex",
    "account_plan_type",
    "provider_capability_flags",
    "feature_default_enabled",
)

INSTALL_GUIDANCE = (
    "Codex was not found on PATH or in $CODEX_HOME. Install the Codex CLI, or point "
    "CODEX_HOME at an installation that provides it, then run the capability probe again. "
    "This plugin does not install Codex for you."
)

WINDOWS_NATIVE_EXECUTABLE_EXTENSIONS = (".com", ".exe")


@dataclass(frozen=True)
class Capability:
    verdict: str
    reasons: tuple[str, ...]
    guidance: str
    codex_home: Path
    generation_dir: Path
    codex_binary: Path | None = None
    binary_source: str | None = None
    auth_present: bool = False
    generation_dir_writable: bool = False
    image_generation_override: bool | None = None
    configured_model: str | None = None
    configured_provider: str | None = None
    model_reported: str | None = None
    unverified: tuple[str, ...] = field(default=UNVERIFIED_OFFLINE)

    @property
    def is_available(self) -> bool:
        return self.verdict == "available"


def _default_codex_home() -> Path:
    override = os.environ.get("CODEX_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".codex"


def _is_executable_file(candidate: Path, platform_name: str | None = None) -> bool:
    """Apply the host platform's executable-file contract without executing the file."""
    selected_platform = os.name if platform_name is None else platform_name
    if not candidate.is_file():
        return False
    if selected_platform == "nt":
        return candidate.suffix.lower() in WINDOWS_NATIVE_EXECUTABLE_EXTENSIONS
    return os.access(candidate, os.X_OK)


def _candidate_paths(base: Path, platform_name: str | None = None) -> tuple[Path, ...]:
    selected_platform = os.name if platform_name is None else platform_name
    if selected_platform != "nt" or base.suffix:
        return (base,)
    return tuple(base.with_suffix(suffix) for suffix in WINDOWS_NATIVE_EXECUTABLE_EXTENSIONS)


def _find_binary(search_path: tuple[str, ...], codex_home: Path) -> tuple[Path | None, str | None]:
    for directory in search_path:
        if not directory:
            continue
        for candidate in _candidate_paths(Path(directory).expanduser() / BINARY_NAME):
            if _is_executable_file(candidate):
                return candidate, "path"
    for bundled in _candidate_paths(codex_home / APPSERVER_RELATIVE):
        if _is_executable_file(bundled):
            return bundled, "codex_home_appserver"
    return None, None


def _writable(target: Path) -> bool:
    existing = target
    while not existing.exists() and existing != existing.parent:
        existing = existing.parent
    if not existing.exists():
        return False
    return os.access(existing, os.W_OK)


def _read_config(config_path: Path) -> tuple[dict, bool]:
    if not config_path.is_file():
        return {}, True
    if tomllib is None:  # pragma: no cover
        return {}, False
    try:
        with config_path.open("rb") as handle:
            return tomllib.load(handle), True
    except (OSError, ValueError):
        return {}, False


def _provider_lacks_image_generation(provider: str | None) -> bool:
    if not provider:
        return False
    lowered = provider.lower()
    return any(blocked in lowered for blocked in PROVIDERS_WITHOUT_IMAGE_GENERATION)


def probe(
    search_path: tuple[str, ...] | list[str] | None = None,
    codex_home: Path | None = None,
    config_path: Path | None = None,
    binary_override: Path | str | None = None,
) -> Capability:
    """Inspect the local environment. Read-only, offline, never executes anything."""
    home = Path(codex_home) if codex_home is not None else _default_codex_home()
    paths = tuple(search_path) if search_path is not None else tuple(os.environ.get("PATH", "").split(os.pathsep))
    config_file = Path(config_path) if config_path is not None else home / CONFIG_FILE_NAME
    generation_dir = home / GENERATION_DIR_NAME

    if binary_override is not None:
        candidate = Path(binary_override)
        if not _is_executable_file(candidate):
            return Capability(
                verdict="unavailable",
                reasons=("codex_binary_missing",),
                guidance=(
                    f"the binary given explicitly is not executable: {candidate}. "
                    "On Windows, provide a native .exe or .com Codex binary; "
                    "script launchers such as .cmd, .bat, .py, and .js are not executed."
                ),
                codex_home=home,
                generation_dir=generation_dir,
            )
        binary, source = candidate, "explicit"
    else:
        binary, source = _find_binary(paths, home)
        if binary is None:
            return Capability(
                verdict="unavailable",
                reasons=("codex_binary_missing",),
                guidance=INSTALL_GUIDANCE,
                codex_home=home,
                generation_dir=generation_dir,
            )

    reasons: list[str] = ["verified_codex_binary"]
    config, config_ok = _read_config(config_file)
    if not config_ok:
        reasons.append("config_unreadable")

    features = config.get("features") if isinstance(config.get("features"), dict) else {}
    override = features.get(FEATURE_KEY)
    if not isinstance(override, bool):
        override = None

    model = config.get("model") if isinstance(config.get("model"), str) else None
    provider = config.get("model_provider") if isinstance(config.get("model_provider"), str) else None

    auth_present = (home / AUTH_FILE_NAME).is_file()
    writable = _writable(generation_dir)

    if not auth_present:
        reasons.append("auth_missing")
    if override is False:
        reasons.append("generation_disabled_by_config")
    if _provider_lacks_image_generation(provider):
        reasons.append("provider_lacks_image_generation")
    if not writable:
        reasons.append("generation_dir_unwritable")

    blocking = {
        "auth_missing",
        "generation_disabled_by_config",
        "provider_lacks_image_generation",
        "generation_dir_unwritable",
    }
    verdict = "unavailable" if blocking.intersection(reasons) else "available"
    guidance = "" if verdict == "available" else _build_guidance(reasons)

    return Capability(
        verdict=verdict,
        reasons=tuple(reasons),
        guidance=guidance,
        codex_home=home,
        generation_dir=generation_dir,
        codex_binary=binary,
        binary_source=source,
        auth_present=auth_present,
        generation_dir_writable=writable,
        image_generation_override=override,
        configured_model=model,
        configured_provider=provider,
    )


def _build_guidance(reasons: tuple[str, ...]) -> str:
    parts: list[str] = []
    if "auth_missing" in reasons:
        parts.append("Sign in to Codex on this machine; the probe does not create or read credentials.")
    if "generation_disabled_by_config" in reasons:
        parts.append(f"Remove the [features] {FEATURE_KEY} = false override from the Codex config.")
    if "provider_lacks_image_generation" in reasons:
        parts.append("The configured model provider does not expose image generation; select a provider that does.")
    if "generation_dir_unwritable" in reasons:
        parts.append("Make the Codex generated_images directory writable, or free space for it.")
    if "config_unreadable" in reasons:
        parts.append("The Codex config could not be parsed; fix it so the feature overrides can be read.")
    return " ".join(parts) if parts else INSTALL_GUIDANCE


def as_report(capability: Capability) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "verdict": capability.verdict,
        "reasons": list(capability.reasons),
        "guidance": capability.guidance,
        "codex_home": str(capability.codex_home),
        "generation_dir": str(capability.generation_dir),
        "codex_binary": str(capability.codex_binary) if capability.codex_binary else None,
        "binary_source": capability.binary_source,
        "auth_present": capability.auth_present,
        "generation_dir_writable": capability.generation_dir_writable,
        "image_generation_override": capability.image_generation_override,
        "configured_model": capability.configured_model,
        "configured_provider": capability.configured_provider,
        "model_reported": capability.model_reported,
        "unverified": list(capability.unverified),
    }


def render_json(capability: Capability) -> str:
    return json.dumps(as_report(capability), indent=2, sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    codex_home = None
    if "--codex-home" in args:
        codex_home = Path(args[args.index("--codex-home") + 1])
    binary = None
    if "--codex-bin" in args:
        binary = Path(args[args.index("--codex-bin") + 1])
    capability = probe(codex_home=codex_home, binary_override=binary)
    sys.stdout.write(render_json(capability) + "\n")
    return 0 if capability.is_available else 1


if __name__ == "__main__":
    raise SystemExit(main())
