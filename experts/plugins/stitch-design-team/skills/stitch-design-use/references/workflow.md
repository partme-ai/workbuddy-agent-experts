# 根路由工作流

1. 确认用户明确提到 Stitch 或上下文已进入 Stitch 工作流。
2. 用 `scripts/stitch_setup.py check` 检查环境优先、用户配置兜底的凭据链与插件 MCP 配置。
3. 将请求分为认证、读取、远程写、本地准备、明确上传、明确下载、删除或完整交付。本地准备不得自动升级为远程上传。
4. 选择最窄的一个主 Skill；只有主流程确实需要时才追加下游步骤。
5. 记录实际完成、未知写结果、尚需批准和未验证事项。

读取工具使用当前资源合同：`get_project` 的 `name` 是 `projects/{project}`；`list_screens` 的 `projectId` 是纯 ID；`get_screen` 的 `name` 是 `projects/{project}/screens/{screen}`。
