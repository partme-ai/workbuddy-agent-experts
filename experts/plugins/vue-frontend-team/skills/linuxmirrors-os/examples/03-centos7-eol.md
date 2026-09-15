# 示例：CentOS 7 EOL

**用户**：CentOS 7 普通源 404，怎么处理？

**处理**：识别 EOL，核验目标镜像的 vault 与 EPEL archive 路径；不要继续使用普通 rolling 仓库。

**计划**：分别设置主仓库/vault 与 EPEL 参数，备份 `/etc/yum.repos.d`，先只执行 makecache。

**验证**：`yum makecache`、repo 列表、GPG 签名；失败则恢复目录备份或切官方归档。
