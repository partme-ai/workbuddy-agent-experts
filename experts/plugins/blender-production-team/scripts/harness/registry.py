"""Closed registry for Blender Harness commands."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from copy import deepcopy

from .errors import HarnessError


# Domain coverage is separate from callable commands: no placeholder handlers.
DOMAINS = (
    'scene', 'object', 'collection', 'asset', 'mesh', 'modifier', 'curve',
    'uv', 'material', 'rig', 'constraint', 'animation', 'camera', 'light',
    'geometry_nodes', 'sculpt', 'hair', 'simulation', 'render', 'compositor',
    'grease_pencil', 'tracking', 'sequence', 'validation', 'job',
    'session', 'capability', 'view', 'playback', 'preview', 'export',
    'advanced', 'official_uploader',
    'recipe', 'production', 'retopo',
)


@dataclass(frozen=True)
class CommandDefinition:
    handler: Callable[[dict], dict]
    validate: Callable[[dict], None] | None = None
    risk: str = "standard"
    metadata: dict | None = None
    availability: Callable[[], dict] | None = None


class CommandRegistry:
    def __init__(self):
        self._commands: dict[str, CommandDefinition] = {}

    def register(self, name: str, handler, *, validate=None, risk: str = "standard",
                 metadata=None, availability=None) -> None:
        if name in self._commands:
            raise HarnessError("DUPLICATE_COMMAND", f"command already registered: {name}")
        if risk not in {"read", "standard", "gated"}:
            raise HarnessError("INVALID_COMMAND_DEFINITION", f"unknown risk: {risk}")
        metadata = deepcopy(metadata or {})
        if set(metadata) & {'id', 'risk', 'input', 'availability'}:
            raise HarnessError('INVALID_COMMAND_DEFINITION', 'identity, risk, input and probe results are registry-owned')
        level = metadata.get('maturity', 'L1')
        if level not in {'L1', 'L2', 'L3', 'L4'}:
            raise HarnessError('INVALID_COMMAND_DEFINITION', 'registered capabilities must be L1-L4')
        if level in {'L3', 'L4'} and not (
            metadata.get('skills') and all(metadata.get('verification', {}).get(key)
                                          for key in ('runtime', 'visual', 'delivery'))
        ):
            raise HarnessError('INVALID_COMMAND_DEFINITION', 'L3 requires Skill, runtime, visual and delivery evidence')
        if level == 'L4' and not metadata.get('verification', {}).get('recoveryAndCompatibility'):
            raise HarnessError('INVALID_COMMAND_DEFINITION', 'L4 requires recovery and compatibility evidence')
        self._commands[name] = CommandDefinition(handler=handler, validate=validate, risk=risk,
                                                 metadata=metadata, availability=availability)

    def dispatch(self, name: str, arguments: dict) -> dict:
        definition = self._commands.get(name)
        if definition is None:
            raise HarnessError("UNKNOWN_COMMAND", f"unknown command: {name}")
        if not isinstance(arguments, dict):
            raise HarnessError("INVALID_ARGUMENT", "command arguments must be an object")
        if definition.validate is not None:
            definition.validate(arguments)
        result = definition.handler(arguments)
        if result is None:
            return {}
        if not isinstance(result, dict):
            raise HarnessError("INVALID_COMMAND_RESULT", f"command {name} returned a non-object")
        return result

    def capabilities(self) -> list[dict]:
        return [
            {"command": name, "risk": definition.risk}
            for name, definition in sorted(self._commands.items())
        ]

    def describe_capability(self, arguments: dict) -> dict:
        """Return a description for one command.

        When *profile* is supplied, a ``productionVerdict`` is added.
        The verdict is computed against a ``RuntimeIdentity`` built from
        ``blenderVersion`` / ``platform`` / ``runtimeMode``.  An explicit
        ``runtime`` object takes precedence over those three fields.
        """
        allowed = {'id', 'profile', 'runtime', 'blenderVersion', 'platform', 'runtimeMode'}
        extra = set(arguments) - allowed
        if extra or not isinstance(arguments.get('id'), str):
            raise HarnessError('INVALID_ARGUMENT', 'describe requires a string id and optional profile/runtime args')
        name = arguments['id']
        profile = arguments.get('profile')
        runtime = arguments.get('runtime')
        # When profile is given without an explicit runtime, build one from
        # the individual fields so callers can query "how does this look on
        # 4.2.23 / windows / managed?" without hand-constructing a RuntimeIdentity.
        if profile is not None and runtime is None:
            from .production_profile import RuntimeIdentity as _RI
            bv = arguments.get('blenderVersion', (0, 0, 0))
            if isinstance(bv, (list, tuple)) and len(bv) >= 3:
                bv = tuple(int(x) for x in bv[:3])
            else:
                bv = (0, 0, 0)
            runtime = _RI(
                blender_version=bv,
                platform=str(arguments.get('platform', 'unknown')),
                architecture='unknown',
                runtime_mode=str(arguments.get('runtimeMode', 'managed')),
            )
        definition = self._commands.get(name)
        if definition is None:
            raise HarnessError('UNKNOWN_CAPABILITY', f'capability is not registered: {name}')
        meta = deepcopy(definition.metadata or {})
        result = {
            'id': name, 'domain': meta.pop('domain', name.split('.')[0]),
            'maturity': 'L1', 'risk': definition.risk,
            'input': deepcopy(getattr(definition.validate, 'schema', None)),
            'output': {'type': 'object', 'description': 'Command-specific result; see handler documentation'},
            'context': {'objectTypes': [], 'modes': [], 'requirements': []},
            'versions': {'verified': [], 'extensions': []},
            'effects': {'sceneMutation': None, 'longRunning': None, 'cancellable': False},
            'skills': [], 'tests': [], 'examples': [],
            'verification': {'runtime': [], 'visual': [], 'delivery': [], 'recoveryAndCompatibility': []},
            'limitations': ['Registration alone is not production or visual acceptance.'],
        }
        result.update(meta)
        result['availability'] = {'status': 'unknown', 'reason': 'Registered; per-session prerequisites have not been probed'}
        if definition.availability:
            try:
                probe = definition.availability()
                if not isinstance(probe, dict) or probe.get('status') not in {'available', 'unavailable', 'unknown'}:
                    raise ValueError('invalid probe result')
                if probe['status'] != 'available' and not probe.get('reason'):
                    raise ValueError('missing probe reason')
                result['availability'] = deepcopy(probe)
            except Exception:
                # Diagnostic failure must not hide the rest of the catalog or leak paths/tokens.
                result['availability'] = {'status': 'unknown', 'reason': 'Capability prerequisite probe failed'}
        # Production verdict is only added when both profile and runtime are provided.
        if profile is not None and runtime is not None:
            verdict = profile.verdict(name, runtime, self)
            result['productionVerdict'] = {
                'status': verdict.status,
                'maturity': verdict.maturity,
                'missingEvidence': list(verdict.missing_evidence),
            }
        return result

    def list_capabilities(self, arguments: dict) -> dict:
        if set(arguments) - {'domain', 'maturity', 'offset', 'limit', 'profile', 'runtime', 'blenderVersion', 'platform', 'runtimeMode'}:
            raise HarnessError('INVALID_ARGUMENT', 'unknown capability filter')
        offset, limit = arguments.get('offset', 0), arguments.get('limit', 50)
        if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 100:
            raise HarnessError('INVALID_ARGUMENT', 'offset must be >=0; limit must be 1-100')
        domain, maturity = arguments.get('domain'), arguments.get('maturity')
        if domain is not None and (not isinstance(domain, str) or domain not in DOMAINS):
            raise HarnessError('INVALID_ARGUMENT', 'unknown domain')
        if maturity is not None and (not isinstance(maturity, str) or maturity not in {'L0', 'L1', 'L2', 'L3', 'L4'}):
            raise HarnessError('INVALID_ARGUMENT', 'unknown maturity')
        profile = arguments.get('profile')
        runtime = arguments.get('runtime')
        describe_args = {'id': None}
        if profile is not None:
            describe_args['profile'] = profile
        if runtime is not None:
            describe_args['runtime'] = runtime
        # Forward the individual identity fields so describe_capability can
        # build a RuntimeIdentity when profile is given without explicit runtime.
        for _key in ('blenderVersion', 'platform', 'runtimeMode'):
            if _key in arguments:
                describe_args[_key] = arguments[_key]
        descriptions = []
        for name in sorted(self._commands):
            describe_args['id'] = name
            descriptions.append(self.describe_capability(dict(describe_args)))
        domains = {name: {'maturity': 'L0', 'registeredCommands': 0,
                          'productionVerifiedCommands': 0} for name in DOMAINS}
        for item in descriptions:
            entry = domains.setdefault(item['domain'], {'maturity': 'L0', 'registeredCommands': 0,
                                                        'productionVerifiedCommands': 0})
            entry['registeredCommands'] += 1
            # Partial tool support is never a claim that the entire domain is mature.
            entry['maturity'] = 'partial'
            entry['productionVerifiedCommands'] += item['maturity'] in {'L3', 'L4'}
        filtered = [item for item in descriptions if (domain is None or item['domain'] == domain)
                    and (maturity is None or item['maturity'] == maturity)]
        return {'items': filtered[offset:offset + limit], 'total': len(filtered),
                'nextOffset': offset + limit if offset + limit < len(filtered) else None,
                'domains': domains}
