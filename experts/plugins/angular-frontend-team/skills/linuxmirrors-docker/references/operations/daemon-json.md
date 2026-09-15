# daemon.json 安全合并

不要用重定向覆盖未知配置。先备份并解析：

```bash
install -d -m 0755 /etc/docker
test ! -f /etc/docker/daemon.json || cp -a /etc/docker/daemon.json /etc/docker/daemon.json.bak
jq . /etc/docker/daemon.json 2>/dev/null || true
```

使用 JSON 工具把 `registry-mirrors` 合并到现有对象，保留 `log-driver`、`data-root`、`proxies`、`insecure-registries` 等键。写入临时文件，`jq -e .` 校验后再原子替换。

Registry Mirror 地址不是凭据存储位置；不要把用户名、密码或 Token 写入 JSON 示例。
