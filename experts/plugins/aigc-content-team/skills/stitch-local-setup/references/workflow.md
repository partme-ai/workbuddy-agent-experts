# 跨平台本地凭据工作流

1. 环境变量存在：直接使用，不读配置文件。
2. 环境变量缺失、凭据文件有效：启动器读取后仅注入子进程。
3. 两者都缺失：本地 MCP 代理自动启动 `stitch_setup.py ui`，随后返回缺少凭据错误，不调用远程 Stitch。10 分钟内的重复请求不会重复打开窗口；自动启动失败时使用安装副本中的 `ui` 命令降级。
4. Windows 路径：`%APPDATA%\stitch-design\credentials.json`。
5. macOS/Linux 路径：`$XDG_CONFIG_HOME/stitch-design/credentials.json`，未设置时使用 `~/.config/stitch-design/credentials.json`。
6. `check` 只输出状态行：`STITCH_API_KEY is not configured`、`STITCH_API_KEY is available through the configured secret provider`、`Stitch MCP configuration is present` 或 `Stitch MCP configuration is missing`。它不输出 key，也不输出任何路径；按最后一行区分"凭据缺失"与"插件安装不完整"。凭据文件不可读或损坏时，`check` 改在 stderr 报 `Stitch credential check failed: ...` 并以 1 退出；此时先修复或删除该凭据文件再重跑 `check`，不要新建 key。
7. `list_projects` 返回项目或空列表后，才标记认证可用。

用户交接必须包含 Stitch Settings、当前缺项、自动打开状态、安全边界和只读验证步骤；只有自动打开失败时才要求用户使用安装副本中的真实脚本路径。
