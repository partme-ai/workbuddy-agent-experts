---
name: video-factory-run
description: Use when a validated VideoPlan has an explicit matching rough-cut or final-cut approval and should be rendered, collected, and recorded without automatic retry.
---

# Run an approved edit

## When to use · 前置条件

只在 `VideoPlan` 已校验、当前阶段已有匹配批准时执行。粗剪批准不能用于终版，旧 revision 的批准
不能用于新计划。先运行 `probe`；FFmpeg/ffprobe 缺失时指出具体缺项和安装责任，不要自行安装。

## Workflow · 执行

1. 重算 plan/edit hash 并核对 stage、round、quote revision。
2. 在授权根内重新解析普通文件并核对每个 SHA-256。
3. 只渲染台账中 Pending 的内容寻址分段，不重做回执仍有效的分段。
4. 以封闭枚举编译 argv，`shell:false`；不接受用户自定义 filter graph 或网络协议。
5. 粗剪和终版渲染完成后都进入 `ReviewReady`；显式人工 `accept` 后才进入 `Completed`。
6. 对媒体执行 ffprobe、完整解码、二次哈希和策略门，原子发布成片并写入台账。

失败只记录一次，不自动重试。超时、缺能力、哈希变化、批准不匹配或质量硬门失败时，返回“缺少/失败
的具体项 + 如何补齐”，保留分段供恢复。不得覆盖已采用产物。

## Capability boundaries · 能力边界

能做本地 FFmpeg 粗剪与终版；需要有效计划、对应批准和本机 FFmpeg/ffprobe；不调用外部生成服务、
不安装软件、不接受 URL 或任意命令。终版渲染后保持 `ReviewReady`，用户显式 accept 才 Completed。

## Validation and gotchas · 校验与陷阱

每一步重算哈希并验证回执。Chrome 缺失只影响同步审阅；素材缺失时生成 requirements；Failed 需要
新 round；进程中断只恢复 Pending；字幕默认内嵌轨，不谎称已经烧录或完成安全区视觉检查。

参见 [操作与恢复](../video-factory-use/references/operations.md) 和
[契约与安全](../video-factory-use/references/contracts-and-safety.md)。
