---
name: video-factory-plan
description: Use when local images, clips, audio, or ReelBench shot evidence must be converted into a validated rough-cut or final-cut EditDecision before rendering.
---

# Plan a Video Factory edit

## When to use · 何时使用

当用户已有创作目标与本地素材，需要把自然语言剪辑要求变成可执行、可批准、可版本化的
`EditDecision` 和 `VideoPlan` 时使用。单纯拉片用 `video-shots`，已有计划的渲染用 run Skill。

## Workflow · 计划流程

1. 为每项素材登记稳定 ID、本地相对路径、SHA-256、类型、来源与授权信息。
2. 使用有理 timebase 与整数 ticks，创建稳定 `C01...` clip ID。
3. 明确源入点/出点、时间线位置、轨道、转场、运动和增益；禁止悬空素材和重叠。
4. 输出画幅仅选 16:9、9:16 或 1:1；终版音频/字幕用对应 Asset ID 引用。
5. 执行 `bin/video-factory validate-plan video-plan.json`。
6. 执行 `bin/video-factory quote video-plan.json --stage rough|final`，等待当前阶段批准。

信息不足时先给“假设版计划”，明确假设的时长、画幅和节奏，再列出缺少的素材或选择；不要只说
“请提供更多信息”。缺素材时输出 `asset-requirements.json`，不得虚构文件或哈希。

## Capability boundaries · 能力边界

能做：从授权素材和 ReelBench 证据形成可版本化时间线。需要条件：素材路径、哈希、时长和输出
规格必须可验证。不做：不生成缺失媒体、不猜测哈希、不启动渲染、不调用其他插件私有模块。

## Validation · 输出与门禁

输出必须是闭合 Schema，不含未知字段、URL、凭据或任意滤镜。素材、顺序、规格或 revision 改变后，
旧批准失效。自然语言反馈生成新 revision 和结构化 diff，不覆盖旧版本。

## Gotchas · 常见陷阱

禁止浮点时间线、重复 clip ID、越界裁切、悬空素材、同轨重叠、未知字段和旧批准复用。遇到信息
不足时先给带明确假设的草案，并逐项列出用户需要补充的素材或选择。

参见 [契约与安全](../video-factory-use/references/contracts-and-safety.md) 和
[端到端示例](../video-factory-use/references/examples-and-faq.md)。
