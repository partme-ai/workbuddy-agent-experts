# 三种模式

## 全新安装

配置 Docker CE 软件仓库，安装 Engine、CLI、containerd、Buildx 与 Compose V2，再配置 Registry Mirror。

## CE 软件源更换/修复

目标是包管理器下载 Docker 软件包的仓库。必须验证 repo 文件、签名和包版本列表。

## 仅 Registry

`--only-registry` 只修改镜像拉取加速配置；检测不到 Docker Engine 会退出。目标地址通过 `--source-registry` 指定。

先选模式再生成命令，禁止用一个“换 Docker 源”同时代表三者。
