from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_templates.py"
SPEC = importlib.util.spec_from_file_location("validate_templates", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class TemplateValidatorTest(unittest.TestCase):
    def test_repository_templates_pass(self) -> None:
        self.assertEqual([], VALIDATOR.validate_repository())

    def test_detects_private_name(self) -> None:
        private_name = "Part" + "Me"
        errors = VALIDATOR.validate_template_text("sample.md", f"# Title\n\n{private_name}\n")
        self.assertTrue(any("private product name" in error for error in errors))

    def test_detects_unknown_token(self) -> None:
        errors = VALIDATOR.validate_template_text("sample.md", "# Title\n\n{{UNKNOWN_TOKEN}}\n")
        self.assertTrue(any("unknown global placeholders" in error for error in errors))

    def test_detects_unbalanced_fence(self) -> None:
        errors = VALIDATOR.validate_template_text("sample.md", "# Title\n\n```json\n{}\n")
        self.assertTrue(any("unbalanced fenced code block" in error for error in errors))

    def test_detects_second_h1(self) -> None:
        errors = VALIDATOR.validate_template_text("sample.md", "# First\n\n# Second\n")
        self.assertTrue(any("expected one H1" in error for error in errors))

    def test_readme_template_has_complete_reading_path(self) -> None:
        path = Path(__file__).resolve().parents[1] / "templates" / "readme" / "README模板.md"
        text = path.read_text(encoding="utf-8")
        required_headings = [
            "## 1. 项目简介",
            "## 3. 一眼看懂",
            "## 4. 架构与核心流程",
            "## 6. 快速开始",
            "## 8. 配置",
            "## 14. 测试与质量保证",
            "## 15. 部署与运维",
            "## 16. 安全",
            "## 18. 故障排查与常见问题",
            "## 23. 贡献指南",
        ]
        positions = [text.index(item) for item in required_headings]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("```text", text)
        self.assertIn("```mermaid", text)

    def test_readme_template_family_has_type_specific_content(self) -> None:
        root = Path(__file__).resolve().parents[1] / "templates" / "readme"
        expectations = {
            "README-Java项目模板.md": [
                "## 3. 运行要求与兼容性",
                "## 4. 架构与模块",
                "### 5.1 使用 BOM（推荐）",
                "Starter",
                "Maven",
            ],
            "README-Rust项目模板.md": [
                "MSRV",
                "Cargo Workspace",
                "## 7. Cargo Features",
                "unsafe",
                "crates.io",
            ],
            "README-插件项目模板.md": [
                "## 扩展契约",
                "## 重试、幂等与恢复",
                "插件 ID",
                "宿主版本",
                "ACK",
            ],
            "README-技能包与生态目录模板.md": [
                "## 技能目录",
                "## 支持的 Agent",
                "## 技能如何被发现与加载",
                "SKILL.md",
                "渐进式披露",
            ],
        }
        for filename, required in expectations.items():
            with self.subTest(filename=filename):
                text = (root / filename).read_text(encoding="utf-8")
                for item in required:
                    self.assertIn(item, text)
                self.assertIn("```text", text)
                self.assertIn("```mermaid", text)

    def test_rust_profiles_cover_domain_variants(self) -> None:
        root = Path(__file__).resolve().parents[1] / "templates" / "readme" / "rust-profiles"
        expectations = {
            "README.md": ["选择矩阵", "组合约束", "纯设计阶段"],
            "文档与文件格式处理剖面.md": ["往返保真", "模板填充语义", "格式安全"],
            "上游兼容与移植剖面.md": ["兼容层级", "对象与方法映射", "兼容测试体系"],
            "大型工具箱Workspace剖面.md": ["能力地图", "Facade 与重导出", "Feature 成本"],
            "认证与安全框架剖面.md": ["Token 生命周期", "Web 框架适配", "威胁模型"],
            "纯设计阶段剖面.md": ["尚未提供可构建的 Cargo workspace", "当前交付物", "转为实现阶段"],
            "多语言README布局剖面.md": ["标准双文件", "兼容现有命名", "单文件双语"],
        }
        self.assertEqual(set(expectations), {path.name for path in root.glob("*.md")})
        for filename, required in expectations.items():
            with self.subTest(filename=filename):
                text = (root / filename).read_text(encoding="utf-8")
                for item in required:
                    self.assertIn(item, text)

    def test_rust_template_routes_to_profiles(self) -> None:
        path = Path(__file__).resolve().parents[1] / "templates" / "readme" / "README-Rust项目模板.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("rust-profiles/README.md", text)
        self.assertIn("不要把所有剖面全部复制", text)

    def test_architecture_template_has_complete_contract(self) -> None:
        path = Path(__file__).resolve().parents[1] / "templates" / "architecture" / "架构设计文档模板.md"
        text = path.read_text(encoding="utf-8")
        required_headings = [
            "## 2. 执行摘要",
            "## 4. 范围、边界与外部上下文",
            "## 5. 当前态、目标态与差距",
            "## 8. 组件、模块与依赖",
            "## 10. 核心业务与系统主链",
            "## 12. 数据、状态与一致性",
            "## 15. 安全、隐私与信任边界",
            "## 16. 可靠性、失败与恢复",
            "## 18. 部署、升级与回滚",
            "## 22. 测试、验证与架构验收",
        ]
        positions = [text.index(item) for item in required_headings]
        self.assertEqual(positions, sorted(positions))
        for marker in ["```text", "```mermaid", "sequenceDiagram", "stateDiagram-v2"]:
            self.assertIn(marker, text)

    def test_architecture_profiles_cover_system_variants(self) -> None:
        root = Path(__file__).resolve().parents[1] / "templates" / "architecture" / "profiles"
        expectations = {
            "README.md": ["选择矩阵", "组合规则", "互斥与裁剪"],
            "运行时与应用平台架构剖面.md": ["技术栈与运行时收敛", "启动与装配", "并发实现剖面"],
            "插件与扩展体系架构剖面.md": ["扩展点目录", "生命周期状态机", "隔离与权限"],
            "边缘与嵌入式架构剖面.md": ["硬件与资源画像", "Capability Manifest", "OTA 与回滚"],
            "消息与事件驱动架构剖面.md": ["ACK、提交与交付语义", "死信与重放", "背压与积压"],
            "AI-Agent与RAG架构剖面.md": ["确定性与非确定性边界", "RAG 运行链", "Tool 合同与执行安全"],
            "可观测性与控制面架构剖面.md": ["指标目录与基数", "期望状态与实际状态", "控制命令合同"],
        }
        self.assertEqual(set(expectations), {path.name for path in root.glob("*.md")})
        for filename, required in expectations.items():
            with self.subTest(filename=filename):
                text = (root / filename).read_text(encoding="utf-8")
                for item in required:
                    self.assertIn(item, text)


if __name__ == "__main__":
    unittest.main()
