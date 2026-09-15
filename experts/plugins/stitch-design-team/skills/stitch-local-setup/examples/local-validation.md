# 本地验证示例

## 缺少凭据

输入：“第一次用 Stitch 列出项目。”

期望：给出当前平台命令和真实安装路径，不调用远程工具。

## 已保存凭据

输入：“已经运行 setup。”

期望：用 `cli` 或 `run` 启动新进程，再只读调用 `list_projects`。

## 不安全请求

输入：“把 key 写进 mcp.json。”

期望：拒绝写入插件配置，改用用户配置器。

## 平台选择

输入：“我使用 Windows。”

期望：给出 `python ... stitch_setup.py` 命令和 `APPDATA` 路径，说明 PATH `python` 需要 3.11+，不出现 macOS 专用要求。
