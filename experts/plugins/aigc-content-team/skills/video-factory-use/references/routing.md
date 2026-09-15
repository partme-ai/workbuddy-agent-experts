# 路由决策

| 意图 | 主 Skill | Near miss |
| --- | --- | --- |
| 已有视频拉片、切点、运镜、节奏 | `video-shots` | 不负责自动成片 |
| 原片 + shots 信息同步展示 | `video-sync` | 它不是正式剪辑器 |
| 把目标和素材变成时间线 | `video-factory-plan` | 不执行渲染 |
| 已批准粗剪或终版 | `video-factory-run` | 无批准不得执行 |
| 技术与语义验收 | `video-factory-judge` | 不改写计划 |
| 中断后的合法下一步 | `video-factory-recover` | 不自动重试失败 |

多意图按“证据 → 计划 → 批准 → 渲染 → 审阅 → 新 revision → 终版 → 验收”排序。缺素材时先输出
需求，不越权调用 Image Factory 或 Blender Plugin 私有代码。原生生成请求在 0.1.0 明确 blocked。
