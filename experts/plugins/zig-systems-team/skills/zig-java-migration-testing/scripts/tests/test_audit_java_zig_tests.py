"""Regression tests for the Java-to-Zig migration completion firewall."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "audit_java_zig_tests.py"
SPEC = importlib.util.spec_from_file_location("audit_java_zig_tests", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


class JavaZigAuditTest(unittest.TestCase):
    def create_fixture(self, root: Path) -> tuple[Path, Path, Path]:
        java_root = root / "java"
        zig_root = root / "zig"
        java_test = java_root / "src/test/java/org/example/ExampleTest.java"
        java_asset = java_root / "src/test/resources/example.json"
        zig_test = zig_root / "example-test/tests/source_parity.zig"
        zig_asset = zig_root / "example-test/suite/source/example.json"
        for path in (java_test, java_asset, zig_test, zig_asset):
            path.parent.mkdir(parents=True, exist_ok=True)
        java_test.write_text(
            """import org.junit.jupiter.api.Test;
class ExampleTest {
    @Test
    void returnsValue() { assertEquals(42, evaluate()); }
}
""",
            encoding="utf-8",
        )
        java_asset.write_text('{"value":42}\n', encoding="utf-8")
        zig_test.write_text(
            """const std = @import("std");
test "returns value" {
    try std.testing.expectEqual(@as(i32, 42), @as(i32, 42));
}
""",
            encoding="utf-8",
        )
        zig_asset.write_bytes(java_asset.read_bytes())
        (zig_root / "build.zig").write_text(
            """const std = @import("std");
pub fn build(b: *std.Build) void {
    _ = b.path("example-test/tests/source_parity.zig");
    _ = b.step("migration-test", "Run complete Java/Zig parity suite");
}
""",
            encoding="utf-8",
        )
        (zig_root / "build.zig.zon").write_text(
            '.{ .name = .example, .version = "0.1.0", .paths = .{ "build.zig", "src" }, }\n',
            encoding="utf-8",
        )
        for artifact in ("case.json", "java.json", "zig.json", "diff.json", "whole.json"):
            (root / artifact).write_text("{}\n", encoding="utf-8")
        manifest = root / "source-test-parity.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema": 2,
                    "target_language": "zig",
                    "java_baseline": "java-sha",
                    "target_baseline": "zig-sha",
                    "acceptance_module": {
                        "name": "example-test",
                        "root": "example-test",
                        "build_manifest": "build.zig",
                        "build_step": "migration-test",
                        "published": False,
                        "components": ["example-core"],
                        "command": "zig build migration-test",
                        "status": "PASS",
                        "failed": 0,
                        "skipped": 0,
                        "not_run": 0,
                        "artifact": "whole.json",
                    },
                    "source_tests": [
                        {
                            "source": "src/test/java/org/example/ExampleTest.java#returnsValue",
                            "case_id": "default",
                            "targets": ["example-test/tests/source_parity.zig#returns value"],
                            "disposition": "MIRRORED",
                            "contract_preserved": True,
                            "inputs_preserved": True,
                            "assertions_preserved": True,
                            "fixture_state_preserved": True,
                            "cleanup_preserved": True,
                            "case_expansion_complete": True,
                            "result_parity": "MATCH",
                            "evidence": "case.json",
                        }
                    ],
                    "assets": [
                        {
                            "source": "src/test/resources/example.json",
                            "target": "example-test/suite/source/example.json",
                            "mode": "COPY_EXACT",
                            "sha256": AUDIT.sha256_file(java_asset),
                        }
                    ],
                    "runs": {
                        "java": {
                            "command": "./mvnw test",
                            "status": "PASS",
                            "failed": 0,
                            "skipped": 0,
                            "not_run": 0,
                            "artifact": "java.json",
                        },
                        "target": {
                            "command": "zig build test",
                            "status": "PASS",
                            "failed": 0,
                            "skipped": 0,
                            "not_run": 0,
                            "artifact": "zig.json",
                        },
                        "differential": {
                            "command": "./run-diff",
                            "status": "PASS",
                            "matched": 1,
                            "mismatched": 0,
                            "harness_failures": 0,
                            "skipped": 0,
                            "not_run": 0,
                            "artifact": "diff.json",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        return java_root, zig_root, manifest

    def audit(self, root: Path):
        java_root, zig_root, manifest = self.create_fixture(root)
        return AUDIT.validate_manifest(
            manifest,
            java_root,
            zig_root,
            AUDIT.extract_java_tests(java_root),
            AUDIT.discover_java_assets(java_root, []),
        )

    def test_complete_manifest_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            summary = self.audit(Path(temporary))
        self.assertFalse(summary.blocked, summary.errors)
        self.assertEqual(summary.mapped_java_tests, 1)
        self.assertEqual(summary.exact_assets, 1)

    def test_missing_java_case_mapping_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            java_root, zig_root, manifest = self.create_fixture(root)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["source_tests"] = []
            payload["runs"]["differential"]["matched"] = 0
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            summary = AUDIT.validate_manifest(
                manifest,
                java_root,
                zig_root,
                AUDIT.extract_java_tests(java_root),
                AUDIT.discover_java_assets(java_root, []),
            )
        self.assertTrue(any("missing Java test mapping" in error for error in summary.errors))

    def test_modified_asset_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            java_root, zig_root, manifest = self.create_fixture(root)
            (zig_root / "example-test/suite/source/example.json").write_text(
                '{"value":43}\n', encoding="utf-8"
            )
            summary = AUDIT.validate_manifest(
                manifest,
                java_root,
                zig_root,
                AUDIT.extract_java_tests(java_root),
                AUDIT.discover_java_assets(java_root, []),
            )
        self.assertTrue(any("SHA-256 mismatch" in error for error in summary.errors))

    def test_unregistered_acceptance_step_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            java_root, zig_root, manifest = self.create_fixture(root)
            build = zig_root / "build.zig"
            build.write_text(
                build.read_text(encoding="utf-8").replace("migration-test", "test"),
                encoding="utf-8",
            )
            summary = AUDIT.validate_manifest(
                manifest,
                java_root,
                zig_root,
                AUDIT.extract_java_tests(java_root),
                AUDIT.discover_java_assets(java_root, []),
            )
        self.assertTrue(any("does not register migration-test" in error for error in summary.errors))

    def test_skipped_differential_case_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            java_root, zig_root, manifest = self.create_fixture(root)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["runs"]["differential"]["skipped"] = 1
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            summary = AUDIT.validate_manifest(
                manifest,
                java_root,
                zig_root,
                AUDIT.extract_java_tests(java_root),
                AUDIT.discover_java_assets(java_root, []),
            )
        self.assertTrue(any("skipped must equal 0" in error for error in summary.errors))


if __name__ == "__main__":
    unittest.main()
