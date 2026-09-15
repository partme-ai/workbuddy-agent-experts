---
name: linuxmirrors-os
license: Apache-2.0
description: 为 GNU/Linux 主机规划和指导 LinuxMirrors 系统软件源更换，覆盖发行版识别、国内/教育网/海外/官方源、交互与无人值守参数、EPEL 与 EOL 场景、备份、验证、故障排查和回滚。用户明确要换 apt/yum/dnf/pacman/zypper/apk/portage/Nix 软件源时使用；Docker CE 与 Registry Mirror 改用 Docker 专项流程。
---

# LinuxMirrors 系统软件源换源

## Quick Start

不要立即给一键命令。先收集系统、网络、权限、当前源和回滚条件，再生成“预检 → 计划 → 确认 → 执行 → 验证 → 回滚”的方案。

可直接使用：

- “为 Ubuntu 24.04 服务器制定 LinuxMirrors 换源与回滚方案。”
- “生成适合 CI 的非交互式系统换源命令，但先不要执行。”
- “CentOS 7 已 EOL，如何用 LinuxMirrors 处理 vault 和 EPEL？”

## 什么时候使用

当用户明确要更换 GNU/Linux 系统软件源、恢复官方源、处理 EPEL/vault/EOL 或生成换源自动化方案时使用。Docker CE 仓库、Registry Mirror、Docker Desktop 与容器运行时配置不适用。

## 适用用户

- 新手：采用交互式方案和默认备份，避免自定义 branch。
- 运维人员：采用固定提交、显式参数、diff、维护窗口与回滚验证。
- CI/CD 维护者：采用无人值守参数、停止条件和构建日志留存。

## 前置条件

必须知道发行版、版本、架构、网络区域、root/授权状态和回滚通道；缺少信息时只输出安全假设方案。

## 使用方式

### Step 1：预检
读取[预检清单](references/operations/preflight.md)，确认发行版、版本、架构、root、网络区域和包管理器。

### Step 2：选模式
依据[源模式](references/official/source-modes.md)选择大陆、`--edu`、`--abroad` 或 `--use-official-source true`。

### Step 3：定参数
从[参数参考](references/official/command-options.md)选择最少参数，不臆造开关。

### Step 4：拟计划
明确被修改文件、备份位置、包索引刷新、验证与维护窗口。

### Step 5：先确认
展示命令但不代替用户授权；禁止在未知生产环境直接运行。

### Step 6：执行后验证
检查源文件、包管理器刷新结果与目标域名，不以脚本退出码代替全部验证。

### Step 7：失败回滚
按[回滚指南](references/operations/rollback.md)恢复 `.bak` 或目录备份并重新刷新缓存。

## 能力边界与不适用场景

### ✅ 擅长处理

1. Debian/Ubuntu、Red Hat 系、openSUSE、Arch、Alpine、Gentoo、NixOS 等已支持系统的换源规划。
2. 交互式选择、无人值守参数、EPEL、security、vault、底层系统源与自定义镜像路径。
3. 备份、`--print-diff`、验证、失败诊断和官方源回退。

### ⚠️ 需要条件

1. 实际执行需要 root shell、变更授权、网络连通和维护窗口。
2. EOL 或衍生系统需要核验版本代号、仓库路径和镜像站是否仍同步。
3. 自定义 `--source`/`--branch` 需要先验证完整 URL、Release/repodata 等元数据可用。

### ❌ 超出范围（给替代方案）

1. Docker CE 软件源或 Docker Hub 加速 → 使用 Docker 换源专项流程。
2. 未被当前脚本识别的独立发行版 → 读取该发行版官方仓库文档并手工规划。
3. 在无授权生产机上代执行换源 → 只输出审阅版计划、命令和回滚清单。

## 资料路由

- 完整参数：读[参数参考](references/official/command-options.md)。
- 支持系统：读[系统矩阵](references/official/system-matrix.md)。
- 大陆/教育网/海外/官方源：读[源模式](references/official/source-modes.md)。
- 主脚本与 Lite：读[脚本选择](references/official/script-variants.md)。
- 运行前：读[预检清单](references/operations/preflight.md)。
- CI/CD：读[自动化指南](references/operations/automation.md)。
- 恢复配置：读[回滚指南](references/operations/rollback.md)。
- 报错排查：读[故障排查](references/operations/troubleshooting.md)。

## 安全与隐私

本技能不收集或上传用户数据。不得索要主机密码、SSH 私钥或云凭据。远程脚本先下载、检查来源与哈希/内容，再由用户在 root shell 中执行；不要写成 `sudo bash <(curl ...)`。默认保留备份，不主动使用 `--ignore-backup-tips`。

## Rules

1. 禁止臆造参数、版本代号、仓库路径与镜像可用性。
2. 默认备份、默认不升级全部软件包、默认不清理缓存。
3. 包索引刷新失败立即停止，不继续安装或升级。
4. 多主机任务先在代表性节点验证，再按批次推广。

## 信息不足时

> 先按“Ubuntu 24.04、x86_64、中国大陆、只生成方案、不执行、保留备份、不升级软件包”给出安全示例。请补充：发行版与版本、架构、网络区域、当前源是否可用、是否需要 EPEL/security/vault、是否允许升级软件包。

## 验证清单

- `cat /etc/os-release` 与包管理器是否匹配？
- 命令参数是否存在于当前 `ChangeMirrors.sh --help`？
- 备份路径和恢复命令是否明确？
- 是否避免默认升级全部软件包和清理缓存？
- 是否验证目标仓库元数据与包索引刷新？

## Gotchas

1. `sudo bash <(curl ...)` 可能因进程替换权限/文件描述符行为失败；先进入 root shell。
2. `--source` 只指定主机部分时仍需正确的 `--branch`；多级路径必须整体核验。
3. Debian/Ubuntu 的 security 源可能需要独立 `--source-security` 与 `--branch-security`。
4. CentOS/AlmaLinux EOL 仓库可能需要 vault；不能继续使用普通主仓库路径。
5. `--ignore-backup-tips` 的含义是忽略覆盖提示并不备份，不适合作为默认自动化参数。
6. 包索引刷新失败时不要继续升级软件包；先回滚或修复 DNS/TLS/版本代号。

## FAQ

**Q1：脚本会备份吗？** 主脚本默认备份，常见形式是在原路径后加 `.bak`；仍要在执行前确认磁盘与已有备份。

**Q2：如何不升级软件包？** 在自动化方案中显式使用 `--upgrade-software false`，并核验当前脚本支持该选项。

**Q3：如何恢复官方源？** 优先使用 `--use-official-source true` 重新生成；失败时从备份恢复。

**Q4：curl 都装不上怎么办？** 使用 Python、wget、浏览器或可信本地副本获取脚本，先审查再运行。

**Q5：如何选教育网源？** 中国大陆教育网场景使用 `--edu`，并先确认目标镜像支持该系统版本。

**Q6：如何确认换源成功？** 检查源文件目标域名，运行对应包管理器刷新命令，并确认没有 Release/repodata、签名或 TLS 错误。
