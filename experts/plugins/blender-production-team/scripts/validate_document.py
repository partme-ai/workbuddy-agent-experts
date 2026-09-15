"""Minimal JSON Schema validator for codex-blender receipt schemas.

Uses only the Python standard library. Supports:
  - type checks (string, integer, number, boolean, array, object, null)
  - required fields
  - additionalProperties: false (closed objects)
  - enum constraints
  - pattern constraints (string)
  - minimum / exclusiveMinimum for numeric types
  - items for arrays
  - nested object/array recursion

Returns a list of human-readable error strings; empty list means valid.
"""

import json
import os
import re

_SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")

_pattern_cache: dict[str, re.Pattern] = {}


def _get_pattern(pattern: str) -> re.Pattern:
    if pattern not in _pattern_cache:
        _pattern_cache[pattern] = re.compile(pattern)
    return _pattern_cache[pattern]


def _type_name(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _validate_node(value, schema: dict, path: str) -> list[str]:
    """Recursively validate *value* against *schema*, collecting errors."""
    errors: list[str] = []

    # --- type ---
    expected_type = schema.get("type")
    if expected_type is not None:
        actual = _type_name(value)
        # JSON Schema: integers are also numbers
        if expected_type == "number" and actual == "integer":
            pass  # ok
        elif actual != expected_type:
            errors.append(f"{path}: expected {expected_type}, got {actual}")
            return errors  # no point checking further

    # --- enum ---
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} not in enum {schema['enum']}")

    # --- const ---
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: value must be {schema['const']!r}")

    # --- pattern (strings) ---
    if "pattern" in schema and isinstance(value, str):
        pat = _get_pattern(schema["pattern"])
        if not pat.fullmatch(value):
            errors.append(
                f"{path}: value does not match pattern {schema['pattern']!r}"
            )

    # --- minimum / exclusiveMinimum (numbers) ---
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append(
                f"{path}: value {value} must be > {schema['exclusiveMinimum']}"
            )
        elif "minimum" in schema and value < schema["minimum"]:
            errors.append(
                f"{path}: value {value} must be >= {schema['minimum']}"
            )

    # --- object validation ---
    if isinstance(value, dict):
        props = schema.get("properties", {})
        required = schema.get("required", [])
        additional = schema.get("additionalProperties", True)

        for field in required:
            if field not in value:
                errors.append(f"{path}: missing required field '{field}'")

        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in props:
                errors.extend(_validate_node(child, props[key], child_path))
            elif additional is False:
                errors.append(f"{path}: unknown field '{key}'")
            # if additional is True (default), unknown fields are allowed

    # --- array items ---
    if isinstance(value, list) and "items" in schema:
        item_schema = schema["items"]
        for idx, item in enumerate(value):
            errors.extend(_validate_node(item, item_schema, f"{path}[{idx}]"))

    return errors


def validate_document(schema_name: str, payload: dict) -> list[str]:
    """Validate *payload* against the named schema file.

    *schema_name* is the stem of a JSON file in the ``schemas/`` directory
    (e.g. ``"scene_receipt"`` loads ``schemas/scene_receipt.schema.json``).

    Returns a list of human-readable error strings; an empty list means valid.
    """
    schema_path = os.path.join(_SCHEMA_DIR, f"{schema_name}.schema.json")
    if not os.path.isfile(schema_path):
        return [f"Schema file not found: {schema_path}"]

    with open(schema_path) as f:
        schema = json.load(f)

    return _validate_node(payload, schema, "$")
