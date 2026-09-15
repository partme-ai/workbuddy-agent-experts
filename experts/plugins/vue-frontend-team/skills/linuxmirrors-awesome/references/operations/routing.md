# 任务路由

| 用户目标 | 路径 | 必要输入 |
|---|---|---|
| 了解项目、支持范围、最新变化 | 项目资料核验 | 问题主题、期望时点 |
| 更换 apt/yum/dnf 等系统源 | 系统换源 | OS、版本、架构、网络、权限 |
| 安装 Docker Engine | Docker 安装 | OS、版本、架构、已有 Docker |
| 更换 Docker CE 软件源 | Docker CE 仓库 | 包管理器、当前 repo、目标源 |
| 加速 `docker pull` | Registry Mirror | Docker 状态、daemon.json、目标地址 |

模糊请求先按“只读核验、不执行变更”回答，再列缺失信息。多任务按系统基础源 → Docker 安装源 → Registry 的依赖顺序规划。
