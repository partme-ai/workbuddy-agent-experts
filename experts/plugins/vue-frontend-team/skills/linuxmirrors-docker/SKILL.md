---
name: linuxmirrors-docker
license: Apache-2.0
description: 为 Linux 主机规划 LinuxMirrors Docker Engine 安装、Docker CE 软件源更换和 Docker Registry Mirror 配置，覆盖版本选择、已有安装、仅换 Registry、多镜像地址、daemon.json 合并、服务验证与回滚。用户提到 docker.sh、DockerInstallation.sh、Docker 拉取加速或 `--only-registry` 时使用；普通系统软件源更换不使用本技能。
---

# LinuxMirrors Docker 安装与换源

## Quick Start

先区分三条路径：全新安装 Docker Engine、替换 Docker CE 软件包仓库、仅配置 Registry Mirror。三者影响面不同，不要把“安装源”和“镜像拉取加速”混写。

可直接使用：

- “为 Rocky Linux 9 规划 Docker Engine 安装和验证，先不要执行。”
- “Docker 已安装，只用 LinuxMirrors 更换 Registry Mirror。”
- “安全合并多个 registry-mirrors 到现有 daemon.json，并给回滚步骤。”

只读确认 Docker 状态：

```bash
docker version 2>/dev/null || true
```

检查当前 Mirror，不修改配置：

```bash
docker info 2>/dev/null | sed -n '/Registry Mirrors/,+5p'
```

检查 Compose V2：

```bash
docker compose version 2>/dev/null || true
```

## 什么时候使用

当用户要安装 Docker Engine、更换 Docker CE 软件包仓库、配置 Registry Mirror 或排查 `docker.sh`/`--only-registry` 时使用。普通系统软件源、Docker Desktop、containerd/Kubernetes 全局镜像配置不适用。

## 适用用户

- 新手：先区分全新安装、CE 仓库和 Registry 三种模式。
- 运维人员：重点保护 repo、daemon.json、服务状态与容器数据。
- 平台工程师：使用显式版本、固定脚本提交、批次验证和回滚门禁。

## 前置条件

必须知道发行版、版本、架构、Docker 是否已安装、init 系统、现有 daemon.json 和维护授权。

## 使用方式

### Step 1：预检
读取[预检清单](references/operations/preflight.md)，确认发行版、版本、架构、root、Docker 状态、init 系统和现有配置。

### Step 2：选路径
全新安装/修复 CE 仓库/`--only-registry` 三选一，参考[模式差异](references/official/modes.md)。

### Step 3：定参数
从[参数参考](references/official/command-options.md)选择源、Registry、版本及语言参数。

### Step 4：保护现场
备份 `/etc/docker/daemon.json` 和 Docker CE repo 文件，记录当前 Docker 版本与服务状态。

### Step 5：先确认再执行
展示影响面；默认不关闭防火墙，不在未知生产机直接运行。

### Step 6：验证
检查 repo、`docker version`、服务状态、`docker info` Registry Mirrors 与实际拉取。

### Step 7：回滚
按[回滚指南](references/operations/rollback.md)恢复 JSON/repo 备份并重启或恢复原服务状态。

## 能力边界与不适用场景

### ✅ 擅长处理

1. Debian 系和 Red Hat 系 Linux 上的 Docker Engine 安装及 Docker CE 仓库换源规划。
2. 已安装 Docker 的 `--only-registry`、单个/多个 Registry Mirror 和 `daemon.json` 合并。
3. 指定版本、内网源、服务验证、失败排查和配置回滚。

### ⚠️ 需要条件

1. 实际安装需要 root、受支持发行版、网络、维护窗口和包管理器可用。
2. 指定 `--designated-version` 需要先查询仓库实际提供的完整版本。
3. 现有 `daemon.json` 含代理、日志驱动、私有仓库等配置时必须做 JSON 级合并而非覆盖。

### ❌ 超出范围（给替代方案）

1. Docker Desktop、Windows 或 macOS → 使用 Docker Desktop 官方设置与企业策略。
2. Rootless Docker、无兼容包管理器的独立发行版 → 参考 Docker 官方二进制或 rootless 文档。
3. Kubernetes/containerd 全局镜像配置 → 使用对应运行时与集群配置流程，不能只改 Docker。

## 资料路由

- 完整选项：读[参数参考](references/official/command-options.md)。
- 支持范围：读[兼容性](references/official/compatibility.md)。
- 三种工作模式：读[模式差异](references/official/modes.md)。
- 主脚本与 Lite：读[脚本选择](references/official/script-variants.md)。
- 运行前：读[预检清单](references/operations/preflight.md)。
- JSON 安全合并：读[daemon.json 指南](references/operations/daemon-json.md)。
- 恢复配置：读[回滚指南](references/operations/rollback.md)。
- 报错排查：读[故障排查](references/operations/troubleshooting.md)。

## 安全与隐私

本技能不收集或上传用户数据，不要求主机密码、SSH 私钥或 Registry 凭据。先审查远程脚本再运行。默认保留防火墙，只有用户明确授权并理解暴露面时才讨论 `--close-firewall true`。不要覆盖未知的 `daemon.json`，不要把私有 Registry 凭据写入示例。

## Rules

1. 禁止混淆 Docker CE 软件源和 Registry Mirror。
2. 禁止臆造安装版本、仓库路径、镜像地址或验证结果。
3. 默认不关闭防火墙，不覆盖现有 daemon.json，不删除容器数据。
4. 服务启动失败先验证 JSON 和日志，再决定恢复备份。

## 信息不足时

> 先按“Docker 已安装、只更换 Registry、systemd、保留现有 daemon.json、不关闭防火墙、只生成方案”给出安全示例。请补充：发行版与版本、架构、Docker 是否已安装、目标是 CE 软件源还是 Registry、init 系统、现有 daemon.json、是否有私有仓库或代理。

## 验证清单

- 是否明确选择安装、CE 仓库或仅 Registry 路径？
- 参数是否存在于当前 `DockerInstallation.sh --help`？
- `daemon.json` 是否先通过 `jq`/JSON 解析校验并备份？
- 是否保持防火墙默认不变？
- 是否同时验证服务状态、`docker info` 和实际拉取？

## Gotchas

1. Docker CE 软件源决定软件包下载，Registry Mirror 决定镜像拉取，二者不可互换。
2. `--only-registry` 检测不到 Docker Engine 时会退出，不能当作安装命令。
3. 直接重写 `daemon.json` 会丢失日志、代理、data-root 等现有配置；必须合并。
4. Registry Mirror 可访问不代表 Docker CE 软件仓库可访问，反之亦然。
5. `--close-firewall true` 影响主机安全边界，不得作为默认“安装优化”。
6. 指定版本只写 `28.0.0` 仍可能受发行版包版本格式影响，先查询仓库列表。

## FAQ

**Q1：只想加速拉镜像怎么办？** Docker 已安装时使用 `--only-registry`，并通过 `--source-registry` 指定一个或多个地址。

**Q2：多个地址怎么写？** 使用英文逗号分隔，并验证每个地址；顺序代表尝试优先级而非自动测速。

**Q3：Compose 需要单独安装吗？** 当前脚本集成 Docker Compose V2 插件，使用 `docker compose`，不要默认依赖旧的 `docker-compose`。

**Q4：如何确认 Mirror 生效？** `docker info` 查看 Registry Mirrors，再拉取公开小镜像并观察错误与耗时。

**Q5：可以覆盖 daemon.json 吗？** 只有确认文件不存在或内容可全部替换时；默认应解析、合并、校验和备份。

**Q6：脚本支持所有 Linux 吗？** Docker 脚本主要面向 Debian 系和 Red Hat 系及衍生版；独立发行版要改用官方安装方式。
