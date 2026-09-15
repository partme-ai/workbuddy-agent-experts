# 本地路由示例

- 输入“列出已有 Stitch 项目” → `stitch-mcp-list-projects`，不选择写 Skill。
- 输入“凭据缺失” → 先运行 `scripts/stitch_setup.py check`，失败后转 `stitch-local-setup`。
- 输入“完成页面生成、双图对比、批准和归档” → `stitch-delivery-harness`，不把一次生成回执当完成。
- 输入“整理本地 HTML 和图片” → `stitch-extract-static-html` 或目标转换 Skill，不调用远程上传。
- 输入“把已审核的 demo.html 明确上传到项目 123” → `stitch-upload-to-stitch`；输入“明确下载屏幕 abc” → `stitch-mcp-get-screen` 后安全保存指定资产。
