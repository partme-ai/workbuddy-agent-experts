# 系统换源参数参考

当前 `ChangeMirrors.sh` 帮助包含：

- 区域：`--abroad`、`--edu`
- 地址：`--source`、`--source-epel`、`--source-security`、`--source-vault`、`--source-portage`、`--source-base-system`
- 路径：对应的 `--branch*` 系列
- 系统：`--codename`、`--protocol`、`--use-intranet-source`
- 官方源/EPEL：`--use-official-source`、`--use-official-source-epel`、`--install-epel`、`--only-epel`
- 行为：`--backup`、`--upgrade-software`、`--clean-cache`、`--clean-screen`
- 输出：`--lang`、`--ignore-backup-tips`、`--print-diff`、`--pure-mode`、`--help`

布尔参数只用 `true`/`false`。组合参数前先运行本地可信副本的 `--help`，不要把不同版本的参数拼在一起。
