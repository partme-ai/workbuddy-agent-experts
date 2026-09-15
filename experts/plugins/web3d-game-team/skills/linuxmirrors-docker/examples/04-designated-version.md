# 示例：指定 Docker 版本

**用户**：安装 Docker Engine 28.0.0。

**处理**：先查询目标 CE 仓库的版本列表与发行版包格式，再使用 `--designated-version`；不能假设简短版本一定存在。

**验证**：安装前保存当前版本，安装后检查 Client/Server、containerd 与 Compose V2。

**降级**：目标版本不存在时给可用版本列表，不自动改装“最新版本”。
