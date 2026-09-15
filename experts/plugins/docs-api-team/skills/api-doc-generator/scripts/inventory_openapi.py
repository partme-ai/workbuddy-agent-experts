#!/usr/bin/env python3
"""Create a deterministic endpoint inventory from an OpenAPI/Swagger document."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - JSON input remains supported
    yaml = None


HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def load_spec(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        if yaml is None:
            raise ValueError("PyYAML is required for YAML OpenAPI files")
        data = yaml.safe_load(text)
    if not isinstance(data, dict) or not (data.get("openapi") or data.get("swagger")):
        raise ValueError("input is not an OpenAPI or Swagger document")
    return data


def parameter_names(parameters) -> list[str]:
    result = []
    for parameter in parameters or []:
        if not isinstance(parameter, dict):
            continue
        if "$ref" in parameter:
            result.append(parameter["$ref"])
        elif parameter.get("name"):
            location = parameter.get("in", "unknown")
            required = "required" if parameter.get("required") else "optional"
            result.append(f"{parameter['name']} ({location}, {required})")
    return result


def build_inventory(spec: dict, source: str) -> list[dict]:
    inventory = []
    for path_name, path_item in sorted((spec.get("paths") or {}).items()):
        if not isinstance(path_item, dict):
            continue
        inherited_parameters = path_item.get("parameters") or []
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            responses = operation.get("responses") or {}
            inventory.append(
                {
                    "method": method.upper(),
                    "path": path_name,
                    "operationId": operation.get("operationId"),
                    "summary": operation.get("summary"),
                    "tags": operation.get("tags") or [],
                    "parameters": parameter_names(inherited_parameters + (operation.get("parameters") or [])),
                    "requestBody": bool(operation.get("requestBody")),
                    "responses": sorted(str(code) for code in responses),
                    "security": operation.get("security", spec.get("security", [])),
                    "evidence": source,
                }
            )
    return inventory


def to_markdown(inventory: list[dict]) -> str:
    lines = [
        "# API Endpoint Inventory",
        "",
        "| Method | Path | Operation | Parameters | Request body | Responses | Evidence |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in inventory:
        parameters = "<br>".join(item["parameters"]) or "—"
        responses = ", ".join(item["responses"]) or "待确认"
        operation = item["operationId"] or item["summary"] or "待确认"
        lines.append(
            f"| {item['method']} | `{item['path']}` | {operation} | {parameters} | "
            f"{'是' if item['requestBody'] else '否'} | {responses} | `{item['evidence']}` |"
        )
    lines.extend(["", f"Endpoint count: {len(inventory)}", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        spec_path = args.spec.resolve()
        inventory = build_inventory(load_spec(spec_path), str(spec_path))
        output = to_markdown(inventory) if args.format == "markdown" else json.dumps(inventory, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            if args.output.exists() and not args.force:
                raise ValueError(f"output exists: {args.output}; use --force to overwrite")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
            print(f"WROTE    {args.output} endpoints={len(inventory)}")
        else:
            sys.stdout.write(output)
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR    {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
