#!/usr/bin/env python3
"""A small JSON Schema checker covering exactly the keywords this repository uses.

The plugin ships its contracts as JSON Schema but must not depend on a third-party
validator, so this module implements the subset that appears in `schemas/`:
type, const, enum, pattern, minimum, maximum, minLength, maxLength, minItems,
maxItems, required, properties, additionalProperties, items, $ref, $defs and the
`date-time` format.

Keeping one checker driven by the published schema means the schema file is the
enforcement source; a rule can never be enforced in code that the document does
not state. Anything outside the supported subset raises, rather than being
silently ignored.
"""

from __future__ import annotations

import re

SUPPORTED_KEYWORDS = frozenset(
    {
        "$schema",
        "$id",
        "$defs",
        "$ref",
        "title",
        "description",
        "type",
        "const",
        "enum",
        "pattern",
        "format",
        "minimum",
        "maximum",
        "minLength",
        "maxLength",
        "minItems",
        "maxItems",
        "required",
        "properties",
        "additionalProperties",
        "items",
        "default",
    }
)

SUPPORTED_FORMATS = frozenset({"date-time"})

RFC3339_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")


class UnsupportedSchemaError(Exception):
    """Raised when a schema uses a keyword this checker does not implement."""


def _resolve(reference: str, root: dict) -> dict:
    if not reference.startswith("#/"):
        raise UnsupportedSchemaError(f"only local references are supported: {reference}")
    node: object = root
    for part in reference[2:].split("/"):
        if not isinstance(node, dict) or part not in node:
            raise UnsupportedSchemaError(f"unresolvable reference: {reference}")
        node = node[part]
    if not isinstance(node, dict):
        raise UnsupportedSchemaError(f"reference does not resolve to a schema: {reference}")
    return node


def _check_keywords(schema: dict, path: str) -> None:
    for keyword in schema:
        if keyword not in SUPPORTED_KEYWORDS:
            raise UnsupportedSchemaError(f"{path}: unsupported keyword {keyword!r}")


def _type_matches(instance: object, expected: str) -> bool:
    if expected == "object":
        return isinstance(instance, dict)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "string":
        return isinstance(instance, str)
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "null":
        return instance is None
    raise UnsupportedSchemaError(f"unsupported type {expected!r}")


def validate(instance: object, schema: dict, root: dict | None = None, path: str = "$") -> list[str]:
    """Return human-readable violations; an empty list means the instance conforms."""
    root_schema = root if root is not None else schema
    _check_keywords(schema, path)

    if "$ref" in schema:
        return validate(instance, _resolve(schema["$ref"], root_schema), root_schema, path)

    errors: list[str] = []

    if "const" in schema and instance != schema["const"]:
        return [f"{path}: expected const {schema['const']!r}, got {instance!r}"]

    if "enum" in schema and instance not in schema["enum"]:
        return [f"{path}: {instance!r} is not one of {schema['enum']!r}"]

    expected_type = schema.get("type")
    if expected_type is not None:
        candidates = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_type_matches(instance, candidate) for candidate in candidates):
            return [f"{path}: expected type {expected_type!r}, got {type(instance).__name__}"]

    if isinstance(instance, str):
        pattern = schema.get("pattern")
        if pattern is not None and re.search(pattern, instance) is None:
            errors.append(f"{path}: value {instance!r} does not match pattern {pattern}")
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: longer than maxLength {schema['maxLength']}")
        declared_format = schema.get("format")
        if declared_format is not None:
            if declared_format not in SUPPORTED_FORMATS:
                raise UnsupportedSchemaError(f"{path}: unsupported format {declared_format!r}")
            if declared_format == "date-time" and RFC3339_UTC.match(instance) is None:
                errors.append(f"{path}: {instance!r} is not an RFC 3339 timestamp")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: above maximum {schema['maximum']}")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: fewer than minItems {schema['minItems']}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: more than maxItems {schema['maxItems']}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, entry in enumerate(instance):
                errors.extend(validate(entry, item_schema, root_schema, f"{path}[{index}]"))

    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in instance:
                errors.append(f"{path}: missing required property {name!r}")
        if schema.get("additionalProperties") is False:
            for name in instance:
                if name not in properties:
                    errors.append(f"{path}: unexpected property {name!r}")
        for name, subschema in properties.items():
            if name in instance:
                errors.extend(validate(instance[name], subschema, root_schema, f"{path}/{name}"))

    return errors
