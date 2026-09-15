---
name: video-factory-harness
description: Video Factory CLI invocation spec for WorkBuddy - probe, analyze, analyze-finalize, validate-plan, quote, run (rough/final stages with approval gate), review-sync, plus the director/script/storyboard methodology references. Read this before producing any short-drama video.
---

# 视频工厂调用规范（WorkBuddy）

执行通道是本插件随附的 Node CLI：`<插件根>/bin/video-factory`（自动剪辑与**验证式**合成）。
方法论（导演/剧本/故事板）在插件 `references/` 下随行，先读方法再动手。

## 1. 子命令面

```
video-factory probe                          # 环境探测（第一步）
video-factory analyze <video>                # 镜头分析
video-factory analyze-finalize <shots.json> --track <track.json> --frames <dir>
video-factory validate-plan <plan.json>      # 计划校验（未过不进 quote）
video-factory quote <plan.json> --stage rough|final
video-factory run <plan.json> --stage rough|final --approval <approval.json>
video-factory review-sync <rough-cut> <shots.json>
```

## 2. 硬规则（来自上游验证记录）

- **final 阶段必须持 approval 文件**——没有人工批准文件不进 final 合成。
- rough → 人工审 → final 是唯一节奏；跳过 rough 直接 final 属违规。
- `validate-plan` 不过的问题清单要逐条解决，不许带病 quote。

## 3. 标准工作流（短剧生产）

1. **创意与方法**：按 `references/director`（创意方向）、`references/script`（剧本/分镜脚本）、
   `references/storyboard`（镜头/节奏）产出拍摄计划。
2. **素材分析**：`analyze` → `analyze-finalize` 产出 shots.json。
3. **计划与报价**：写 plan.json → `validate-plan` → `quote --stage rough`。
4. **粗剪**：`run --stage rough` → 人工审粗剪 → `review-sync` 对轨。
5. **终剪**：拿到批准后 `run --stage final`，交付成片与验证报告。
6. 交付时列出：计划摘要、阶段产物路径、验证结论、未验证项。

## 4. 纪律

- 7 个 `video-factory-*` / `video-shots` / `video-sync` 技能已随插件分发，**对应阶段先读对应技能**。
- CLI 每步输出是事实来源；"应该剪好了"不算数，验证结论必须来自命令输出。
- 配额与时长约束以 quote 输出为准。
