---
name: dreamina-3d-harness
description: Dreamina 3D invocation spec for WorkBuddy - the Blender handoff contract (white-model preview to Seedance video), paid submit-once gates, jimeng-web fallback, resume, and how this team connects to the Blender production team. Read this before any 3D visual or white-model video task.
---

# 即梦3D视觉调用规范（WorkBuddy）

执行通道：**Dreamina Design MCP**（即梦后端，付费）。本团队的核心场景：
**Blender 白模/预览 → 即梦 3D → Seedance 视频**。

## 1. 与 Blender 生产团队的衔接（上游已验证的交接契约）

1. 上游：Blender 3D 生产专家团产出**已验证的预览/交接产物**（白模视频或预览帧，带交接契约字段）。
2. 本团队用 `dreamina-3d-from-blender` 技能消费交接产物：校验预览 → 组装 3D 提交。
3. 交接契约字段以该技能文档为准；字段对不上就是交接失败，退回上游重出，**不要手工猜字段**。

## 2. 付费门禁（auto_with_budget / auto_exact_request）

- 一次授权一次提交（submit-once）；`quote` 超上限即停，恢复不自动再付费。
- 上游如实：Dreamina Design 目前**无权威报价工具**时会停在 `QUOTE_UNAVAILABLE`——
  用户可改批一次完全指定的 `auto_exact_request`（仍不绕过平台原生付费确认）。
- 提交后：记录标识 → 轮询 → 下载 → **独立验证**产物（哈希/内容）。

## 3. 技能族（6 个已随插件分发）

| 技能 | 用途 |
|---|---|
| `dreamina-3d-from-blender` | 消费 Blender 交接产物（本团队主场景） |
| `dreamina-3d-auto-seedance` | 验证过的预览 → Seedance 视频（自动档，含付费门禁与恢复） |
| `dreamina-3d-jimeng-web` | 网页端操作路径（自动档受阻时的人工通道） |
| `dreamina-3d-resume` | 断点恢复 |
| `dreamina-3d-from-maya` | **暂缓**：maya→3D 交接存在已知断点，修通前不承接 |
| `dreamina-3d-use` | 入口路由 |

## 4. 标准工作流（白模视频）

1. 确认拿到 Blender 团队的交接产物与授权信封（预算/分辨率/时长偏好）。
2. `from-blender` 校验与组装 → `auto-seedance` 提交（门禁规则见上）。
3. 下载后独立验证；失败走 `resume`，不重复付费。
4. 交付：交接产物标识、submit 记录、视频路径与验证结论、剩余预算、未验证项。

## 5. 纪律

- MCP 失败如实报错；网页端兜底前先征得用户同意。
- 本团队不做建模——建模需求转 Blender 生产团队，拿到交接产物再回来。
