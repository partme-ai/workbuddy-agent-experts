# Codex 编剧

![Codex × Script — 将原始素材转化为银幕故事](assets/script-hero.png)

> 分析和改编小说、故事与已有剧本，产出大纲、分场剧本与语义拆解。

[English](README.md) | [简体中文](README.zh-CN.md)

## 状态与版本

**当前仅为设计与开发规划基线，尚未实现、打包或安装。** 本仓库刻意不创建可能被宿主误认为可运行能力的空 Skill 或 MCP manifest。

插件标识规划为 `codex-script`，仓库为 `codex-script-plugin`。

## 输入与输出

- 输入：SourceMaterial / SourceSpan、改编目标、目标集数或时长、锁定原作事实、素材策略。
- 输出：StoryBible、Outline、EpisodeOutline、Screenplay / Scene、BreakdownCandidate、SourceCoverage。

## 边界

编剧插件决定故事和对白；不自行生成导演镜头路线，不编排实际付费图片或视频，也不代替工作台资产与版本服务。

创作在 Codex / WorkBuddy 宿主执行，结果经工作台 MCP 保存为可审阅版本。本插件不拥有独立数据库。Codex 包格式和 WorkBuddy 接入分别验收，不假定二者天然兼容。

## 文档导航

- [插件功能规格](docs/superpowers/specs/plugin-design.md)
- [开发计划](docs/superpowers/plans/implementation.md)
- [工作台系统架构](https://github.com/partme-ai/creative-production-workbench/blob/main/docs/superpowers/specs/architecture.md)
- [统一契约](https://github.com/partme-ai/creative-production-workbench/blob/main/docs/superpowers/specs/contracts.md)
- [全流程映射](https://github.com/partme-ai/creative-production-workbench/blob/main/docs/superpowers/specs/workflows.md)

## 许可证

当前文档为项目原创设计，仓库为私有，尚未选择对外开源许可。
