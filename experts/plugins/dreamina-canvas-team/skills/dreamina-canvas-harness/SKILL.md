---
name: dreamina-canvas-harness
description: Dreamina Canvas invocation spec for WorkBuddy - the dreamina-canvas CLI (auth, create/compose, generate image/video/audio, timeline management, quote-and-run, resume), asset download and model discovery. Read this before any canvas creation task.
---

# 即梦画布调用规范（WorkBuddy）

执行通道：`dreamina-canvas` CLI（安装/校验/调用见 `dreamina-canvas-cli` 技能）；本插件随附其脚本与技能。
画布 = **多模态画布创作**：图、视频、**音频**、时间线与成片。

## 1. 能力族（13 个技能已随插件分发）

| 族 | 技能 |
|---|---|
| 环境与入口 | `dreamina-canvas-auth`（登录授权）、`dreamina-canvas-cli`、`dreamina-canvas-use` |
| 画布创建与编排 | `dreamina-canvas-create`、`dreamina-canvas-compose`、`dreamina-canvas-manage-timeline` |
| 生成（图/视频/**音频**） | `dreamina-canvas-generate-image` / `-video` / **`-audio`** |
| 运营 | `dreamina-canvas-quote-and-run`（报价与执行）、`dreamina-canvas-resume-operation`（断点续作）、`dreamina-canvas-discover-models`、`dreamina-canvas-download-assets` |

## 2. 硬规则

- 先 `auth` 后一切；授权态丢失就引导重登，不重试烧配额。
- `quote-and-run`：先报价后执行，报价/预算超限即停。
- 长任务断点走 `resume-operation`，不从头重跑。
- 模型选择用 `discover-models` 实测面（本机 CLI 面可能滞后于主干），不硬编码目录。

## 3. 标准工作流

1. `auth` 确认授权 → `create` 建画布。
2. 按需生成：图 / 视频 / 音频（音频是本套件独有能力，设计套件没有）。
3. `manage-timeline` 编排时间线 → `compose` 合成。
4. `download-assets` 取产物；交付列出：画布标识、素材清单、时间线摘要、产物路径、配额消耗、未验证项。

## 4. 纪律

- CLI 的 stdout/stderr 与标识持久化按 `dreamina-canvas-cli` 技能规范执行。
- 付费动作同样 submit-once：一次授权一次提交，恢复走 resume 技能。
