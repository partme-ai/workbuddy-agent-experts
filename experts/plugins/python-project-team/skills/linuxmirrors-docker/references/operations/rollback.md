# Docker 回滚

变更前记录：

- `docker version`、`docker info`、服务 active/enabled 状态。
- Docker CE repo 文件与 keyring。
- `/etc/docker/daemon.json` 及其权限、属主。

失败后：

1. 停止继续安装或拉取测试。
2. 恢复 `daemon.json.bak` 或删除本次新增文件。
3. 恢复原 CE repo/keyring。
4. 先做 JSON 与 repo 语法检查，再恢复原服务状态。
5. 验证 `docker info`、容器列表和原 Registry 行为。

卸载 Docker Engine 可能影响镜像、容器和 volume，不作为默认回滚动作。
