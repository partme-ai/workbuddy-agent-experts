import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "inventory_openapi.py"
SPEC = importlib.util.spec_from_file_location("inventory_openapi", MODULE_PATH)
INVENTORY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = INVENTORY
SPEC.loader.exec_module(INVENTORY)


class OpenApiInventoryTest(unittest.TestCase):
    def test_inventory_preserves_contract_facts(self):
        spec = {
            "openapi": "3.1.0",
            "paths": {
                "/users/{id}": {
                    "parameters": [{"name": "id", "in": "path", "required": True}],
                    "get": {
                        "operationId": "getUser",
                        "responses": {"200": {"description": "ok"}, "404": {"description": "missing"}},
                    },
                }
            },
        }
        result = INVENTORY.build_inventory(spec, "openapi.json")
        self.assertEqual(1, len(result))
        self.assertEqual("GET", result[0]["method"])
        self.assertEqual(["200", "404"], result[0]["responses"])
        self.assertEqual(["id (path, required)"], result[0]["parameters"])

    def test_json_spec_loading(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "openapi.json"
            path.write_text(json.dumps({"openapi": "3.0.3", "paths": {}}), encoding="utf-8")
            self.assertEqual("3.0.3", INVENTORY.load_spec(path)["openapi"])

    def test_cli_writes_inventory_and_refuses_implicit_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            spec_path = root / "openapi.json"
            output_path = root / "inventory.json"
            spec_path.write_text(
                json.dumps(
                    {
                        "openapi": "3.0.3",
                        "paths": {
                            "/health": {
                                "get": {
                                    "operationId": "health",
                                    "responses": {"200": {"description": "ok"}},
                                }
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            command = [
                sys.executable,
                str(MODULE_PATH),
                str(spec_path),
                "--format",
                "json",
                "--output",
                str(output_path),
            ]
            first = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(0, first.returncode, first.stderr)
            inventory = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual("GET", inventory[0]["method"])
            self.assertEqual("/health", inventory[0]["path"])

            second = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(2, second.returncode)
            self.assertIn("use --force to overwrite", second.stderr)


if __name__ == "__main__":
    unittest.main()
