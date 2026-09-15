---
name: stitch-local-setup
description: 本地首次使用 Stitch Design、缺少 STITCH_API_KEY 或认证失败时，指导 Windows、macOS、Linux 用户从 Stitch Settings 获取 key，并通过插件配置器完成一次性设置；网页 ChatGPT 连接不使用本流程。
license: Apache-2.0
---

# Stitch Design 本地首次设置

## 快速开始

典型触发：

1. “第一次使用 Stitch Design。”
2. “Stitch 提示缺少 STITCH_API_KEY。”
3. “帮我配置 Stitch key，但不要写进 shell profile。”

面向 Windows、macOS、Linux 的本地 Codex 用户。插件已内置本地 stdio MCP 代理；本 Skill 只处理用户凭据缺失和受限的用户级配置。

所有支持宿主的 PATH 中的 `python` 必须解析为 Python 3.11 或更高版本；插件 MCP 和本设置流程使用同一命令。

## 能力边界说明

### ✅ 擅长处理

- 检查 `STITCH_API_KEY` 是否已在当前进程或用户配置中设置，不输出其值。
- 指导用户隐藏输入自己的 Stitch API key，并保存到跨平台的当前用户受限配置文件。
- 用保存的凭据启动 Codex CLI，或向用户指定的本地命令注入环境变量。

### ⚠️ 需要用户完成

- 登录 [Stitch Settings](https://stitch.withgoogle.com/settings) 创建或轮换自己的 key。
- 只在本机配置器的隐藏提示中输入 key。
- 重新启动 Codex，让新进程获得 `STITCH_API_KEY`。

### ❌ 不适用场景及交接

- ChatGPT 网页插件授权：应由正式 connector/OAuth 处理，不要求用户粘贴 key。
- 团队共享一个作者 key：每位用户使用独立凭据，或建设租户隔离的认证网关。
- 将 Key 写入 Codex 配置、shell profile、项目文件或权限不受限的文件。

## 首次使用工作流

1. 先用配置器做只读检查；它同时校验凭据是否可读、以及插件根 `.mcp.json` 是否存在，只输出状态行，不打印 key 或路径：

   ```bash
   python /absolute/plugin/root/scripts/stitch_setup.py check
   ```

2. 检查通过后继续原来的 Stitch 任务。
3. 检查失败时暂停远程调用，并按最后一行输出区分两个分支，不要混为一谈：

   - `STITCH_API_KEY is not configured`：凭据缺失。MCP 代理会自动打开本地 Token 页面；告诉用户从 Stitch Settings 创建 key，不要让用户把 key 粘贴到聊天。代理在刷新一次后仍收到 401 时也会打开同一页面，用于更换失效 Key。
   - `Stitch MCP configuration is missing`：凭据可读但插件根缺少 `.mcp.json`，属于安装不完整。此时新建 key 无效，应修复或重新安装插件后重跑 `check`。
4. 正常情况下等待自动打开的本地页面。代理使用 10 分钟冷却标记避免同一缺失凭据连续弹窗；标记只记录启动时间，不包含 key。只有浏览器被系统策略阻止或页面未出现时，才从当前 `SKILL.md` 向上两级定位插件根目录并手动打开：

   - Windows：

     ```powershell
     python C:\absolute\plugin\root\scripts\stitch_setup.py ui
     ```

   - macOS / Linux：

     ```bash
     python /absolute/plugin/root/scripts/stitch_setup.py ui
     ```

5. 用户在单卡片中粘贴并保存 Token；获取链接、三条说明和高级命令保持轻量，不再显示独立三步向导。
6. 凭据仅来自当前进程或受限的用户配置文件；没有其他存储迁移入口。
7. 设置后先回到对话重新发起原请求。若当前宿主没有重新建立 MCP 进程，再使用配置器启动 Codex：

   ```bash
   python /absolute/plugin/root/scripts/stitch_setup.py cli
   ```

   Windows 使用同一个 `python ... cli` 命令。自定义启动命令使用 `run -- <command>`。
8. 新任务先只读调用 `list_projects`。项目列表或明确的空列表都算认证成功；未知或超时不执行写操作。

## 安全与降级

- 不搜索浏览器、其他客户端配置、shell profile、历史或日志中的 key。
- 不执行 `echo "$STITCH_API_KEY"`、`printenv STITCH_API_KEY` 或全量 `env`。
- Key 不进入插件目录、Git 或 Codex 配置；用户配置目录和文件在 Unix 使用 `0700`/`0600`，Windows 继承当前用户 Profile ACL。配置器不修改 `.zshrc`、PowerShell Profile 或系统环境。
- PATH `python` 缺失或低于 3.11 时，先阻塞插件调用并给出修复说明；会话级环境变量不能修复解释器前置条件。

## FAQ

**Q1：key 在哪里获取？** 在 [Stitch Settings](https://stitch.withgoogle.com/settings) 创建。

**Q2：为什么安装后还需要 key？** 安装已完成 MCP 配置；key 用于 Stitch 用户认证。

**Q3：会修改 shell 配置吗？** 不会。配置器使用独立的用户凭据文件。

**Q3.1：为什么页面没有自动打开？** 自动打开由本地 MCP 代理在首次缺少凭据时触发，并有 10 分钟防重复冷却。若浏览器策略阻止打开，请使用上面的 `ui` 命令；不需要把 key 发到聊天。

**Q4：保存在哪里？** Unix 使用 `$XDG_CONFIG_HOME/stitch-design/credentials.json` 或 `~/.config/...`，Windows 使用 `%APPDATA%\stitch-design\credentials.json`。移除方式为先在 Stitch Settings 吊销 key，再删除该凭据文件；删除后不要继续使用旧 key。

**Q5：如何验证？** 运行 `stitch_setup.py check`，重启后只读调用 `list_projects`。

**Q6：能把 key 发给智能体吗？** 不能，只在本机隐藏提示中输入。

## 按需参考

- 状态和平台分支见 [工作流](references/workflow.md)。
- 不安全方案见 [反模式](references/anti-patterns.md)。
- 存储、轮换和 connector 边界见 [深度 FAQ](references/faq-deep.md)。
- 行为验证见 [本地验证示例](examples/local-validation.md)。
