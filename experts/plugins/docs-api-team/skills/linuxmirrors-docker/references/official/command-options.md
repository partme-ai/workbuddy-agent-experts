# Docker 脚本参数参考

当前 `DockerInstallation.sh` 帮助包含：

- CE 软件源：`--source`、`--branch`、`--branch-version`、`--codename`、`--protocol`、`--use-intranet-source`
- Registry：`--source-registry`（多个地址用英文逗号分隔）、`--only-registry`
- 安装：`--designated-version`、`--install-latest`
- 行为：`--close-firewall`、`--clean-screen`、`--ignore-backup-tips`
- 输出：`--lang`、`--pure-mode`、`--help`

布尔值只用 `true`/`false`。不要把 `--source` 当成 Registry，也不要把 `--source-registry` 当成软件包仓库。
