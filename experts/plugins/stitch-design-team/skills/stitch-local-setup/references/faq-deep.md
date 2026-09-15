# 深度 FAQ

**Q1：配置文件加密吗？** 不加密；它依赖当前用户目录和文件权限，因此不是系统密钥库。

**Q2：Unix 权限是什么？** 目录 `0700`、文件 `0600`。

**Q3：Windows 权限是什么？** 文件位于当前用户的 `APPDATA`；继承用户目录 ACL。

**Q4：如何轮换？** 创建新 key，重新运行 `setup` 覆盖文件，验证后吊销旧 key。

**Q5：CI 怎么使用？** 从 CI secret store 注入 `STITCH_API_KEY`，不提交凭据文件。

**Q6：如何使用自定义 Codex 启动器？** 执行 `stitch_setup.py run -- <command>`。

**Q7：为什么不直接设置系统环境？** 系统环境会影响无关进程，且不同平台持久化方式不一致。

**Q8：网页为什么不能使用该文件？** ChatGPT 网页运行在远端，无法读取本地用户配置。

**Q9：何时移除这套方案？** 官方 Stitch connector/OAuth 通过端到端验证后。移除步骤：先在 Stitch Settings 吊销 key，再删除本机凭据文件（Unix `$XDG_CONFIG_HOME/stitch-design/credentials.json` 或 `~/.config/...`，Windows `%APPDATA%\stitch-design\credentials.json`）；删除后不要继续使用旧 key。

**Q10：空项目列表算成功吗？** 算；它证明认证调用已完成。
