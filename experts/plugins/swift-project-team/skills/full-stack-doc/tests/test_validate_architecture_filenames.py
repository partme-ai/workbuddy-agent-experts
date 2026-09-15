from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_architecture_filenames.py"
)
SPEC = importlib.util.spec_from_file_location("validate_architecture_filenames", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ArchitectureFilenameValidatorTest(unittest.TestCase):
    def test_accepts_required_output_patterns(self) -> None:
        valid = [
            "ExamplePlatform-Architecture.md",
            "ExamplePlatform-Architecture.zh_CN.md",
            "ExamplePlatform-Gateway-Architecture.md",
            "ExamplePlatform-Gateway-Architecture.zh_CN.md",
            "示例平台-V2-Architecture.zh_CN.md",
            "8、ExamplePlatform-Architecture.zh_CN.md",
            "3、ExamplePlatform-V2-Architecture.zh_CN.md",
        ]
        self.assertEqual([], VALIDATOR.validate_paths(valid))

    def test_rejects_legacy_and_inconsistent_variants(self) -> None:
        invalid = [
            "ExamplePlatform-Architecture_CN.md",
            "ExamplePlatform-Architecture.zh-CN.md",
            "ExamplePlatform-architecture.md",
            "ExamplePlatform-架构设计.md",
            "Architecture.md",
        ]
        errors = VALIDATOR.validate_paths(invalid)
        self.assertEqual(len(invalid), len(errors))

    def test_requires_identical_bilingual_stems_when_requested(self) -> None:
        paths = [
            "ExamplePlatform-Architecture.md",
            "ExamplePlatform-Gateway-Architecture.zh_CN.md",
        ]
        errors = VALIDATOR.validate_paths(paths, require_pairs=True)
        self.assertEqual(2, len(errors))

    def test_accepts_matching_bilingual_pair(self) -> None:
        paths = [
            "ExamplePlatform-Architecture.md",
            "ExamplePlatform-Architecture.zh_CN.md",
        ]
        self.assertEqual([], VALIDATOR.validate_paths(paths, require_pairs=True))

    def test_lifecycle_structure_uses_architecture_suffixes(self) -> None:
        skill_root = Path(__file__).resolve().parents[1]
        structure = (skill_root / "references" / "structure.md").read_text(encoding="utf-8")
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("8、{{PRODUCT_NAME}}-Architecture.zh_CN.md", structure)
        self.assertIn("3、{{PRODUCT_NAME}}-{{VERSION}}-Architecture.zh_CN.md", structure)
        self.assertIn("8、{{PRODUCT_NAME}}-Architecture.zh_CN.md", skill)
        self.assertIn("3、{{PRODUCT_NAME}}-V1-Architecture.zh_CN.md", skill)


if __name__ == "__main__":
    unittest.main()
