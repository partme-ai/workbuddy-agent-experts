# 项目概览

LinuxMirrors 是 MIT 许可的 GNU/Linux 系统软件源更换脚本与 Docker 安装/换源脚本集合。它不是镜像站本身，而是选择镜像站并生成、修改和验证配置的自动化运维工具。

核心入口：

- `ChangeMirrors.sh`：系统软件源，支持多发行版、交互和无人值守参数。
- `DockerInstallation.sh`：Docker Engine 安装、Docker CE 软件仓库与 Registry Mirror。
- 两个 Lite 脚本：面向精简使用，能力不应被视为与主脚本完全等价。
- 官网短地址 `main.sh` 与 `docker.sh` 指向对应主脚本分发入口。

项目强调国内网络适配，同时提供教育网、海外、官方源和多个脚本分发地址。
