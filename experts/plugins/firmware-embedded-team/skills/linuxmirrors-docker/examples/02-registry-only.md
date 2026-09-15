# 示例：仅更换 Registry Mirror

**用户**：Docker 已安装，只配置镜像加速。

**预检**：`docker version`、`docker info`、解析现有 `/etc/docker/daemon.json`。

**计划**：使用 `--only-registry --source-registry registry.example.com`，先备份 JSON，不改 CE repo。

**验证**：`docker info` 显示 Mirror，实际拉取公开小镜像。

**回滚**：恢复 `daemon.json.bak` 并恢复原服务状态。
