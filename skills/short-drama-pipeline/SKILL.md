---
name: short-drama-pipeline
description: Short-drama studio orchestration map - which execution team owns which stage (Dreamina Design for generated assets, Dreamina 3D for white-model Seedance video, Video Factory for verified composition), the handoff points, gates and the rough-to-final approval rhythm. Read this before producing any short drama.
---

# 短剧制片厂编排地图

本团队是**薄编排层**：自身不带执行技能。创作方法论（导演/编剧/故事板）在 `references/` 随行；
执行全部调度到三个执行团队，各管一段、各守各的门禁。

## 1. 阶段 → 执行团队 → 门禁

| 阶段 | 执行团队 | 关键门禁 |
|---|---|---|
| 创意/剧本/故事板 | 本团队（方法论 references/ + 成员） | 导演阐述定稿后才进剧本；故事板与分镜逐镜对齐 |
| 生成素材（图/视频片段） | **即梦设计专家团** | 付费 submit-once；quote 超限即停 |
| 白模视频（3D 镜头） | **Blender 生产团队**（建模+预览）→ **即梦3D视觉专家团**（Seedance） | Blender 交接契约；3D 付费门禁同上 |
| 合成与成片 | **视频工厂专家团** | validate-plan 过关才 quote；**rough → 人工批准 → final** |
| 图表/概念图（可选） | ProcessOn 专家团 | — |

双轨说明：纯图素材可选**图片工厂**（Codex 后端）或**即梦设计**（即梦后端）——按用户账本选择，
默认问清。

## 2. 交接点（本团队盯的三个契约）

1. **故事板 → 生成**：每镜的提示词与时长口径随镜移交，生成团队按镜回报产物标识。
2. **Blender → 3D**：白模预览必须带交接契约字段（见即梦3D视觉团队的 `dreamina-3d-harness` 技能）。
3. **素材 → 视频工厂**：shots.json + 素材路径齐套才允许 validate-plan；缺件先补齐再报计划。

## 3. 节奏（硬规则）

- 每阶段产物**先验收再进下一阶段**；验收人可以是本团队 lead 或用户。
- 视频工厂的 final **必须持批准文件**；本团队负责把人工批准落实成文件再放行。
- 任何团队的付费提交，预算信封由本团队统一向用户要，一次授权一次提交。

## 4. 交付

成片 + 分镜对照表 + 各阶段验证结论 + 预算消耗台账 + 未验证项清单。
