# 示例：Ubuntu 交互式换源

**用户**：Ubuntu 24.04 在中国大陆换源。

**预检**：确认 `/etc/os-release`、root shell、架构、备份空间、目标镜像支持 noble。

**计划**：下载并审查固定版本脚本；保留备份；交互选择兼容镜像；默认不升级全部软件包。

**验证**：检查 `.sources`/`sources.list`、运行 `apt-get update`、确认无 Release/签名/TLS 错误。

**回滚**：恢复对应 `.bak`，再次 `apt-get update`。
