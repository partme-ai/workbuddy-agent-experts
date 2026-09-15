# Docker 故障排查

- `--only-registry` 报未安装：确认 `command -v docker` 与 daemon；需要安装时切换到完整安装路径。
- Docker CE 包找不到：核对发行版 codename、branch-version、架构、repo 签名与版本列表。
- daemon 启动失败：先 `jq -e . /etc/docker/daemon.json`，再查看 `journalctl -u docker`，必要时恢复备份。
- Mirror 未显示：检查配置路径、daemon 是否重载/重启，以及当前是否为 Docker Desktop/Rootless。
- 拉取仍失败：区分 DNS/TLS、限流、镜像不存在、鉴权和 Mirror 不同步。
- Compose 命令不存在：检查 Compose V2 插件包，使用 `docker compose version`，不要默认安装旧版二进制。

