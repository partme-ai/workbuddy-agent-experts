# Docker 变更预检

```bash
cat /etc/os-release
uname -m
id -u
command -v docker systemctl service jq 2>/dev/null
docker version 2>/dev/null || true
docker info 2>/dev/null || true
test -f /etc/docker/daemon.json && jq . /etc/docker/daemon.json
```

还要确认：安装来源、现有 repo、`daemon.json`、代理、日志驱动、data-root、私有 Registry、磁盘空间、维护窗口和回滚通道。

JSON 无法解析、Docker 管理方式未知或无变更授权时停止，只给诊断和审阅版方案。
