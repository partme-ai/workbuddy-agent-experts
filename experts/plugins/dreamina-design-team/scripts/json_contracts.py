"""Dependency-free validation for versioned Dreamina JSON contracts."""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import unquote


SCHEMAS_ROOT = (Path(__file__).resolve().parents[1] / "schemas").resolve()


class ContractValidationError(ValueError):
    """A versioned public JSON artifact violates its closed schema."""


_RFC3339 = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)


def parse_rfc3339(value: Any, *, label: str = "timestamp") -> datetime:
    """Parse one strict timezone-qualified RFC3339 timestamp and normalize to UTC."""
    if not isinstance(value, str) or _RFC3339.fullmatch(value) is None:
        raise ContractValidationError(f"{label} must be a strict RFC3339 timestamp with timezone")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:
        raise ContractValidationError(f"{label} must be a valid RFC3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise ContractValidationError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def load_schema(name: str) -> dict[str, Any]:
    """Load one JSON schema from the plugin's closed schema directory."""
    try:
        target = (SCHEMAS_ROOT / name).resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise ContractValidationError("unsafe schema name") from exc
    if target.parent != SCHEMAS_ROOT or target.suffix != ".json":
        raise ContractValidationError("unsafe schema name")
    try:
        schema = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractValidationError(f"invalid schema: {name}") from exc
    if not isinstance(schema, dict):
        raise ContractValidationError(f"invalid schema: {name}")
    return schema


def canonical_fingerprint(payload: Mapping[str, Any]) -> str:
    """Return the SHA-256 digest of a deterministic UTF-8 JSON encoding."""
    try:
        encoded = json.dumps(
            dict(payload),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise ContractValidationError("payload is not canonical JSON") from exc
    return hashlib.sha256(encoded).hexdigest()


def validate_contract(payload: Any, schema_name: str) -> None:
    """Validate a payload against a local closed JSON schema."""
    schema = load_schema(schema_name)
    _validate(payload, schema, path="$", document=schema, schema_name=schema_name)


def _validate(
    value: Any,
    schema: Mapping[str, Any],
    *,
    path: str,
    document: Mapping[str, Any],
    schema_name: str,
) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ContractValidationError(f"{path} must be a finite number")

    if "$ref" in schema:
        referenced, referenced_document, referenced_name = _resolve_ref(
            str(schema["$ref"]), document=document, schema_name=schema_name
        )
        _validate(
            value,
            referenced,
            path=path,
            document=referenced_document,
            schema_name=referenced_name,
        )

    for subschema in schema.get("allOf", []):
        _validate(value, subschema, path=path, document=document, schema_name=schema_name)
    if "anyOf" in schema and not _matches_any(
        value, schema["anyOf"], path=path, document=document, schema_name=schema_name
    ):
        raise ContractValidationError(f"{path} does not match any allowed schema")
    if "oneOf" in schema:
        matches = sum(
            _matches(value, item, path=path, document=document, schema_name=schema_name)
            for item in schema["oneOf"]
        )
        if matches != 1:
            raise ContractValidationError(f"{path} must match exactly one allowed schema")
    if "not" in schema and _matches(
        value, schema["not"], path=path, document=document, schema_name=schema_name
    ):
        raise ContractValidationError(f"{path} matches a forbidden schema")
    if "if" in schema and _matches(
        value, schema["if"], path=path, document=document, schema_name=schema_name
    ):
        if "then" in schema:
            _validate(value, schema["then"], path=path, document=document, schema_name=schema_name)
    elif "else" in schema:
        _validate(value, schema["else"], path=path, document=document, schema_name=schema_name)

    if "const" in schema and value != schema["const"]:
        raise ContractValidationError(f"{path} must equal the declared constant")
    if "enum" in schema and value not in schema["enum"]:
        raise ContractValidationError(f"{path} is not an allowed value")

    expected = schema.get("type")
    if expected is not None and not _has_type(value, expected):
        raise ContractValidationError(f"{path} must be {_type_label(expected)}")

    if isinstance(value, Mapping):
        properties = schema.get("properties", {})
        for required in schema.get("required", []):
            if required not in value:
                raise ContractValidationError(f"{path}.{required} is required")
        unknown = set(value) - set(properties)
        additional = schema.get("additionalProperties", True)
        if unknown and additional is False:
            raise ContractValidationError(f"{path} has unknown properties: {sorted(unknown)}")
        for key, item in value.items():
            child = properties.get(key)
            if child is None and isinstance(additional, Mapping):
                child = additional
            if child is not None:
                _validate(
                    item,
                    child,
                    path=f"{path}.{key}",
                    document=document,
                    schema_name=schema_name,
                )

    if isinstance(value, list):
        if len(value) < int(schema.get("minItems", 0)):
            raise ContractValidationError(f"{path} has too few items")
        if len(value) > int(schema.get("maxItems", len(value))):
            raise ContractValidationError(f"{path} has too many items")
        if schema.get("uniqueItems") is True:
            seen: set[tuple[Any, ...]] = set()
            for item in value:
                identity = _json_identity(item, path=path)
                if identity in seen:
                    raise ContractValidationError(f"{path} has duplicate items")
                seen.add(identity)
        items = schema.get("items")
        if isinstance(items, Mapping):
            for index, item in enumerate(value):
                _validate(
                    item,
                    items,
                    path=f"{path}[{index}]",
                    document=document,
                    schema_name=schema_name,
                )
        if "contains" in schema and not any(
            _matches(item, schema["contains"], path=f"{path}[{index}]", document=document, schema_name=schema_name)
            for index, item in enumerate(value)
        ):
            raise ContractValidationError(f"{path} does not contain a required item")

    if isinstance(value, str):
        if len(value) < int(schema.get("minLength", 0)):
            raise ContractValidationError(f"{path} is shorter than allowed")
        if len(value) > int(schema.get("maxLength", len(value))):
            raise ContractValidationError(f"{path} is longer than allowed")
        if "pattern" in schema and re.search(str(schema["pattern"]), value) is None:
            raise ContractValidationError(f"{path} does not match the required pattern")

    if _is_number(value):
        if "minimum" in schema and value < schema["minimum"]:
            raise ContractValidationError(f"{path} is below the minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise ContractValidationError(f"{path} is above the maximum")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            raise ContractValidationError(f"{path} is not above the exclusive minimum")
        if "exclusiveMaximum" in schema and value >= schema["exclusiveMaximum"]:
            raise ContractValidationError(f"{path} is not below the exclusive maximum")


def _resolve_ref(
    reference: str, *, document: Mapping[str, Any], schema_name: str
) -> tuple[Mapping[str, Any], Mapping[str, Any], str]:
    target_name, separator, fragment = reference.partition("#")
    if target_name:
        if ":" in target_name or target_name.startswith("/"):
            raise ContractValidationError("unsafe schema reference")
        referenced_document = load_schema(target_name)
        referenced_name = target_name
    else:
        referenced_document = document
        referenced_name = schema_name
    node: Any = referenced_document
    if separator and fragment:
        if not fragment.startswith("/"):
            raise ContractValidationError("invalid schema reference")
        for raw_part in fragment[1:].split("/"):
            part = unquote(raw_part).replace("~1", "/").replace("~0", "~")
            if not isinstance(node, Mapping) or part not in node:
                raise ContractValidationError("invalid schema reference")
            node = node[part]
    if not isinstance(node, Mapping):
        raise ContractValidationError("invalid schema reference")
    return node, referenced_document, referenced_name


def _matches(
    value: Any,
    schema: Mapping[str, Any],
    *,
    path: str,
    document: Mapping[str, Any],
    schema_name: str,
) -> bool:
    try:
        _validate(value, schema, path=path, document=document, schema_name=schema_name)
    except ContractValidationError:
        return False
    return True


def _matches_any(
    value: Any,
    schemas: list[Mapping[str, Any]],
    *,
    path: str,
    document: Mapping[str, Any],
    schema_name: str,
) -> bool:
    return any(
        _matches(value, item, path=path, document=document, schema_name=schema_name)
        for item in schemas
    )


def _has_type(value: Any, expected: Any) -> bool:
    expected_types = expected if isinstance(expected, list) else [expected]
    return any(
        {
            "object": lambda: isinstance(value, Mapping),
            "array": lambda: isinstance(value, list),
            "string": lambda: isinstance(value, str),
            "integer": lambda: isinstance(value, int) and not isinstance(value, bool),
            "number": lambda: _is_number(value),
            "boolean": lambda: isinstance(value, bool),
            "null": lambda: value is None,
        }.get(item, lambda: False)()
        for item in expected_types
    )


def _type_label(expected: Any) -> str:
    if isinstance(expected, list):
        return " or ".join(str(item) for item in expected)
    return str(expected)


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and (not isinstance(value, float) or math.isfinite(value))
    )


def _json_identity(value: Any, *, path: str) -> tuple[Any, ...]:
    """Return a deterministic, type-preserving identity for one JSON value."""
    if value is None:
        return ("null",)
    if isinstance(value, bool):
        return ("boolean", value)
    if _is_number(value):
        return ("number", value)
    if isinstance(value, str):
        return ("string", value)
    if isinstance(value, list):
        return ("array", tuple(_json_identity(item, path=path) for item in value))
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise ContractValidationError(f"{path} contains a non-JSON value")
        return (
            "object",
            tuple(
                (key, _json_identity(value[key], path=path))
                for key in sorted(value)
            ),
        )
    raise ContractValidationError(f"{path} contains a non-JSON value")
