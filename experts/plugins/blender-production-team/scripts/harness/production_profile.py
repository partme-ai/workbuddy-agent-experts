"""Evidence-gated production profile.

The profile selects commands for the production catalog based on maturity,
class, and evidence requirements.  It does *not* re-implement the
registration-time evidence gate; it uses the evidence that registration
already enforces and adds path-existence validation on top.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .errors import HarnessError
from .registry import CommandRegistry

# Classes that are never production-eligible.
_NEVER_PRODUCTION = frozenset({'expert', 'experimental'})

# Maturity levels that qualify for the production catalog.
_PRODUCTION_MATURITY = frozenset({'L3', 'L4'})

# Evidence keys required for L3 commands.
_L3_EVIDENCE = ('skills', 'runtime', 'visual', 'delivery')

# Additional evidence keys required for L4 commands.
_L4_EXTRA_EVIDENCE = ('recoveryAndCompatibility',)

# Domains whose commands are optional -- they never block a core ready verdict.
_OPTIONAL_DOMAINS = frozenset({'official_uploader'})


@dataclass(frozen=True)
class RuntimeIdentity:
    """Identifies the Blender runtime context for a verdict.

    Defined here because Task 2 runs before Task 3 creates compat/base.py.
    Task 3 will import and re-export this from compat/base.py.
    """
    blender_version: tuple[int, int, int]
    platform: str
    architecture: str
    runtime_mode: str


@dataclass(frozen=True)
class CapabilityVerdict:
    """Result of evaluating a single command against the production profile."""
    status: str  # 'ready' | 'blocked' | 'excluded' | 'not_production'
    maturity: str  # 'L1' | 'L2' | 'L3' | 'L4' or ''
    missing_evidence: tuple[str, ...]


class ProductionProfile:
    """Load and query a production profile configuration."""

    def __init__(self, config: dict):
        self._exclude_domains: frozenset[str] = frozenset(
            config.get('excludeDomains', ())
        )
        self._exclude_classes: frozenset[str] = (
            frozenset(config.get('excludeClasses', ())) | _NEVER_PRODUCTION
        )

    @classmethod
    def load(cls, path: Path) -> ProductionProfile:
        """Load a profile from a JSON file."""
        data = json.loads(path.read_text())
        return cls(data)

    def _is_excluded(self, command_id: str, meta: dict) -> bool:
        """A command is excluded if its class or domain is excluded."""
        domain = meta.get('domain', command_id.split('.')[0])
        cmd_class = meta.get('class', 'standard')
        if cmd_class in self._exclude_classes:
            return True
        if domain in self._exclude_domains:
            return True
        return False

    def _required_evidence(self, maturity: str) -> tuple[str, ...]:
        """Return the evidence keys a maturity level requires."""
        if maturity == 'L4':
            return _L3_EVIDENCE + _L4_EXTRA_EVIDENCE
        if maturity == 'L3':
            return _L3_EVIDENCE
        return ()

    def verdict(self, command_id: str, runtime: RuntimeIdentity,
                registry: CommandRegistry) -> CapabilityVerdict:
        """Evaluate one command against the production profile.

        Uses the evidence that registration already enforces and adds
        path-existence validation.
        """
        # Look up the command from the registry.
        definition = registry._commands.get(command_id)
        if definition is None:
            return CapabilityVerdict('blocked', '', ('unregistered',))

        meta = definition.metadata or {}

        # Exclusion checks.
        if self._is_excluded(command_id, meta):
            return CapabilityVerdict('excluded', meta.get('maturity', 'L1'), ())

        maturity = meta.get('maturity', 'L1')

        # Only L3/L4 are production-eligible.
        if maturity not in _PRODUCTION_MATURITY:
            return CapabilityVerdict('not_production', maturity, ())

        # Check required evidence presence and path existence.
        required = self._required_evidence(maturity)
        missing: list[str] = []
        project_root = Path(__file__).resolve().parents[2]

        for key in required:
            if key == 'skills':
                if not meta.get('skills'):
                    missing.append('skills')
            else:
                evidence_paths = (meta.get('verification') or {}).get(key, ())
                if not evidence_paths:
                    missing.append(key)
                else:
                    # A declared evidence path that does not exist on disk
                    # makes the validator fail (no dangling evidence).
                    # Paths may include a '#heading' anchor suffix (e.g.
                    # 'docs/verification/matrix.md#scene'); only the file
                    # portion is validated on disk; the anchor is not verified.
                    for ep in evidence_paths:
                        file_part = ep.split('#', 1)[0]
                        if not (project_root / file_part).is_file():
                            missing.append(f'{key}:{ep}')

        return CapabilityVerdict(
            status='blocked' if missing else 'ready',
            maturity=maturity,
            missing_evidence=tuple(missing),
        )

    def status(self, runtime: RuntimeIdentity,
               registry: CommandRegistry) -> dict:
        """Compute the production status for all registered commands.

        Returns a dict with status, productionCommands, optionalCommands,
        blockedCommands, and catalogHash.
        """
        production_commands: list[str] = []
        optional_commands: list[str] = []
        blocked_commands: list[str] = []
        l1_commands: list[str] = []

        for name in sorted(registry._commands):
            definition = registry._commands[name]
            meta = definition.metadata or {}
            domain = meta.get('domain', name.split('.')[0])

            if domain in _OPTIONAL_DOMAINS:
                optional_commands.append(name)
                continue

            v = self.verdict(name, runtime, registry)
            if v.status == 'ready':
                production_commands.append(name)
            elif v.status == 'blocked':
                blocked_commands.append(name)
            elif v.status == 'not_production' and v.maturity == 'L1':
                l1_commands.append(name)
            # excluded commands are silently omitted.

        # Compute catalog hash: canonical JSON of the profile + production set.
        hash_input = json.dumps({
            'excludeDomains': sorted(self._exclude_domains - _NEVER_PRODUCTION),
            'excludeClasses': sorted(self._exclude_classes - _NEVER_PRODUCTION),
            'productionCommands': production_commands,
        }, sort_keys=True, separators=(',', ':'))
        catalog_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        overall = 'ready' if not blocked_commands else 'blocked'

        return {
            'status': overall,
            'productionCommands': production_commands,
            'optionalCommands': optional_commands,
            'blockedCommands': blocked_commands,
            'l1Commands': l1_commands,
            'catalogHash': catalog_hash,
        }
