# 示例：全新安装 Docker Engine

**用户**：Rocky Linux 9 安装 Docker。

**预检**：确认架构、root、dnf、现有容器运行时、repo 和防火墙策略。

**计划**：审查固定版本 `DockerInstallation.sh`，选择 CE 软件源与安装版本；保持防火墙不变。

**验证**：repo 元数据、`docker version`、服务状态、`docker compose version` 和公开小镜像拉取。

**回滚**：恢复 repo/daemon 配置；卸载前单独评估容器、镜像和 volume 数据。
