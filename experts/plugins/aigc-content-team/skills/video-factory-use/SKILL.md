---
name: video-factory-use
description: Use when a request involves automatic video editing, rough cuts, final cuts, synchronized shot review, media verification, or recovery and must be routed to the correct Video Factory workflow.
---

# Video Factory

## Quick start · 30 秒开始

用户只需说目标，例如：

- “把这 8 段采访自动剪成 60 秒竖版粗剪。”
- “给这个成语故事的图片做成带旁白和字幕的视频。”
- “先拉片，再给我一版带镜头信息的审阅视频。”

先识别目标，再走唯一对应路线：拉片用 `video-shots`；同步镜头信息审阅用 `video-sync`；
自动剪辑计划用 `video-factory-plan`；已批准渲染用 `video-factory-run`；验收用
`video-factory-judge`；中断恢复用 `video-factory-recover`。

## Workflow · 工作流

1. 明确成片目的、受众、时长、画幅和已有素材；信息不足时先给带假设的草案并列出缺项。
2. 已有视频需要证据时先路由 `video-shots`，不要自行复制其切点算法。
3. 生成闭合 `EditDecision` 与 `VideoPlan`，校验后报价。
4. 粗剪批准通过后渲染；需要镜头数据叠加时再路由原样 `video-sync`。
5. 把用户意见转成新 revision，保留旧决定和旧成片。
6. 终版重新报价、重新批准，渲染后执行确定性质量门和人工确认。

## Capability boundaries · 能力边界

### 能做

- 从授权图片、视频、音频和字幕制作粗剪与终版。
- 硬切、淡入淡出、叠化、图片推拉平移、横竖方三种画幅。
- 生成可恢复台账、媒体回执、技术门禁和审阅证据。

### 需要素材或本机能力

- 拉片需要本地视频、FFmpeg 和 ffprobe。
- 同步审阅需要原片、`shots.json`、输入音轨和 Chrome。
- 图片、Blender 动画、音乐及旁白必须由其所有者提供带哈希的授权文件。

### 不做

- 不把本地合成描述成原生 AI 文生视频。
- 不调用外部视频 API、读取 API Key 或自动安装软件。
- 不承担 PartMe Studio UI、图片生成或 Blender 控制。

原生生成请求在 0.1.0 明确 blocked；不能把本地合成或第三方能力冒充 Codex 原生视频生成。

## Rules and validation · 安全与准确性

只接受授权根目录内的普通本地文件。拒绝 URL、路径穿越、符号链接逃逸、特殊文件、哈希变化、
任意 FFmpeg 表达式和凭据字段。可测量事实必须来自程序证据；不确定的信息标为 `NOT_RUN`，
不得编造成功。模型建议不能覆盖确定性失败，人工驳回不能被模型分数覆盖。

## Gotchas · 常见陷阱

旧批准不能用于新 revision；同步审阅不是客户终版；无音轨原片不能直接交给 `video-sync`；缺失
Chrome 只降级同步审阅；`SKIPPED` 不能写成 `PASS`。修复模板和完整 FAQ 见下方参考文档。

## References · 深入阅读

- [路由决策](references/routing.md)
- [公开契约与安全](references/contracts-and-safety.md)
- [操作与失败恢复](references/operations.md)
- [端到端示例与 FAQ](references/examples-and-faq.md)
