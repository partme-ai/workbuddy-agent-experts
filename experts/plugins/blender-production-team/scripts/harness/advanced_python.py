"""Explicitly authorized expert Python with a restrictive static policy."""

from __future__ import annotations

import ast
import hashlib

from .errors import HarnessError


MAX_SCRIPT_BYTES = 64 * 1024
FORBIDDEN_NAMES = {"__import__", "compile", "eval", "exec", "open", "input", "breakpoint"}
FORBIDDEN_NODES = (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)


class AdvancedPythonExecutor:
    def __init__(self, bpy_module):
        self.bpy = bpy_module

    def execute(self, arguments: dict) -> dict:
        script = arguments.get("script")
        if not isinstance(script, str) or not script.strip():
            raise HarnessError("INVALID_ARGUMENT", "script must be a non-empty string")
        encoded = script.encode("utf-8")
        if len(encoded) > MAX_SCRIPT_BYTES:
            raise HarnessError("PYTHON_POLICY_REJECTED", "script exceeds 64 KiB")
        try:
            tree = ast.parse(script, mode="exec")
        except SyntaxError as exc:
            raise HarnessError("INVALID_ARGUMENT", f"script syntax error: {exc}") from exc
        for node in ast.walk(tree):
            if isinstance(node, FORBIDDEN_NODES):
                raise HarnessError("PYTHON_POLICY_REJECTED", f"forbidden syntax: {type(node).__name__}")
            if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
                raise HarnessError("PYTHON_POLICY_REJECTED", f"forbidden name: {node.id}")
            if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
                raise HarnessError("PYTHON_POLICY_REJECTED", f"private attribute access is forbidden: {node.attr}")
        safe_builtins = {
            "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict, "enumerate": enumerate,
            "float": float, "int": int, "len": len, "list": list, "max": max, "min": min,
            "range": range, "round": round, "set": set, "str": str, "sum": sum, "tuple": tuple,
            "zip": zip,
        }
        code = compile(tree, "<codex-blender-authorized>", "exec")
        exec(code, {"__builtins__": safe_builtins, "bpy": self.bpy}, {})
        return {
            "changedObjects": [],
            "result": {"scriptSha256": hashlib.sha256(encoded).hexdigest()},
            "warnings": ["AUTHORIZED_EXPERT_PYTHON"],
        }

