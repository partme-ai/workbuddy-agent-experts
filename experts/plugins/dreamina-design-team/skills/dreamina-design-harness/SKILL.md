---
name: dreamina-design-harness
description: Dreamina Design invocation spec for WorkBuddy - the image/video generation CLI (trusted_cli), text2image/image2image/text2video/image2video families across cli/opencli/prompt variants, shot annotation, video evaluation, and the paid submit-once gates with real submit_id verification. Read this before any Dreamina generation task.
---

# 即梦设计调用规范（WorkBuddy）

执行通道：本插件随附的生成 CLI（`scripts/trusted_cli.py` 为受信入口；`dreamina-cli` 技能含完整用法）。
后端：**即梦（Dreamina），付费动作**，submit-once 门禁与真实 submit_id 验收是硬约束。

## 1. 能力族（17 个技能已随插件分发）

| 族 | 技能 |
|---|---|
| 文生图 / 图生图 | `dreamina-cli-text2image` / `image2image`（+ `opencli-*` 变体 + `prompt-*` 提示词口径） |
| 文生视频 / 图生视频 | `dreamina-cli-text2video` / `image2video`（同上三变体） |
| 视频生产流 | `dreamina-video-production`（生产编排）、`dreamina-shot-annotator`（镜头标注） |
| 评测 | `dreamina-video-evaluator`（视频质量评测） |
| 入口 | `dreamina-design-use` / `dreamina-cli` |

**边界（如实）**：设计套件专注**图与视频**，无独立音频生成技能；**声音能力在"即梦画布"套件**
（`dreamina-canvas-generate-audio`），需要配音/音效时转画布团队。

## 2. 付费门禁（不可绕）

- 每次**付费提交**都要：用户明确授权 → 记录真实 `submit_id` → 凭据核对（回执/下载的 SHA-256 等）。
- `submit-once`：一次授权一次提交；失败恢复走技能里的恢复路径，**不得自动重试付费提交**。
- 预算上限由用户给定；报价缺失时（`QUOTE_UNAVAILABLE`）停下问，不猜。

## 3. 标准工作流

1. 明确产物类型（图/视频）与提示词基线（`prompt-*` 技能）。
2. 走 `cli` 或 `opencli` 族执行生成（参数以技能文档为准）。
3. 视频过 `dreamina-video-evaluator`；镜头类需求用 `shot-annotator`。
4. 交付：产物路径、submit_id、验证凭据、消耗与剩余预算、未验证项。

## 4. 纪律

- CLI 输出与回执是事实来源；叙述与输出冲突以输出为准。
- 与**图片工厂**（Codex 后端）是双轨：用户没指定后端时，问清按哪个账本走。
