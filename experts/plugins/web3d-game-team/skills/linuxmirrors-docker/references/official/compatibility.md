# Docker 脚本兼容性

官网说明 Docker 脚本主要支持 Debian 系和 Red Hat 系 Linux 发行版及衍生版，且不会维护一份完整的所有衍生版清单。

执行前核验：

1. `/etc/os-release`、架构、包管理器与 init 系统。
2. 发行版是否有当前 Docker CE 软件仓库与签名配置。
3. Docker 是否已安装、安装来源与当前版本。
4. Docker Desktop、Rootless、Snap 等非标准安装不套用普通 rootful 流程。
5. 独立发行版改用 Docker 官方二进制或发行版仓库。
