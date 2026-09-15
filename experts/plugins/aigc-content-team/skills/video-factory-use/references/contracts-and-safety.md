# 公开契约与安全规则

公开对象包括 `AssetManifest`、`ReelBenchEvidence`、`EditDecision`、`VideoPlan`、`VideoApproval`、
`VideoJob`、`MediaReceipt` 和 `MediaScores`。Schema 版本固定，未知字段拒绝。

素材身份由 SHA-256 而非路径确定。只接受授权根目录中的普通文件；拒绝 URL、路径穿越、符号链接、
设备文件和哈希变化。台账拒绝 `apiKey`、`token`、`password`、`secret` 字段。FFmpeg 仅使用程序生成
的 argv 和封闭枚举，禁止 shell 与调用方 filter graph。

跨插件只交换公开字段：ID、类型、相对路径、哈希、来源、许可、授权时间和回执路径。不 import 私有
模块、不读取数据库。处理的人像、音乐、品牌和字幕由用户保证授权；插件不上传、不收集分析数据。
