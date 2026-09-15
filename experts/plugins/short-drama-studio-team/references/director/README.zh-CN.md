# Codex 导演

![Codex × Director — 将剧本转化为电影化制作方案](assets/director-hero.png)

> 将选定分场剧本转为导演阐述、视听风格、场面调度、镜头意图和可执行制作路线。

[English](README.md) | [简体中文](README.zh-CN.md)

## 状态与版本

**当前仅为设计与开发规划基线，尚未实现、打包或安装。** 本仓库刻意不创建可能被宿主误认为可运行能力的空 Skill 或 MCP manifest。

插件标识规划为 `codex-director`，仓库为 `codex-director-plugin`。

## 输入与输出

- 输入：选定 Screenplay / Scene revision、StoryBible、资产规格、目标画幅与时长、执行策略。
- 输出：DirectorPlan、SceneTreatment、ShotIntent、ContinuityConstraints、ProductionRoute、ChangeProposal。

## 边界

导演插件解释如何拍，不擅自改变发生什么或人物说什么。镜头意图与最终 Shot / Panel 保持区分，不重复创建 Storyboard 数据。

创作在 Codex / WorkBuddy 宿主执行，结果经工作台 MCP 保存为可审阅版本。本插件不拥有独立数据库。Codex 包格式和 WorkBuddy 接入分别验收，不假定二者天然兼容。

## 文档导航

- [插件功能规格](docs/superpowers/specs/plugin-design.md)
- [开发计划](docs/superpowers/plans/implementation.md)
- [工作台系统架构](https://github.com/partme-ai/creative-production-workbench/blob/main/docs/superpowers/specs/architecture.md)
- [统一契约](https://github.com/partme-ai/creative-production-workbench/blob/main/docs/superpowers/specs/contracts.md)
- [全流程映射](https://github.com/partme-ai/creative-production-workbench/blob/main/docs/superpowers/specs/workflows.md)

## 许可证

当前文档为项目原创设计，仓库为私有，尚未选择对外开源许可。
