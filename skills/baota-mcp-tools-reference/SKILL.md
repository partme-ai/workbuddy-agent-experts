---
name: baota-mcp-tools-reference
description: 宝塔 Linux 面板 13.0 的 MCP 协议 98 个工具速查表。按 19 个分类（基础/网站/网络/数据库/服务/Docker/系统/软件/防火墙/Java/Node/Python/Go/反代/HTML/SSH/安全/计划任务/通知）组织，每行标注工具名、风险等级、一句话功能、关键参数、WorkBuddy 通用工具映射。当 Agent 在 8765/bt-mcp 通道下需要选择合适工具时使用本表。
metadata:
  category: 运维工具参考
  target: 宝塔面板 13.0 MCP 工具集
  count: 98
---

# 宝塔面板 MCP 工具速查表（98 工具）

## 通用约定

- **返回结构**：`{"status": bool, "msg": string, ...}`，失败 `status=false`
- **风险等级**：
  - `low` 只读查询（绿色）
  - `medium` 有副作用（黄色）
  - `high` 高危操作（红色，删除/覆盖/执行命令）
- **基础工具**：仅对非本机部署的客户端开放（Agent 远程连面板时才可用）
- **本页分类**：按功能域 19 类，工具总数 98

---

## 一、基础工具（10 个）

> 仅供远程 Agent 调用，本机已用 file/shell 工具时不走 MCP。

| 工具 | 风险 | 一句话功能 | 关键参数 | WorkBuddy 通用工具映射 |
|------|------|----------|---------|---------------------|
| `Read` | low | 读取文本文件 | `file_path`, `offset`, `limit` | `Read` |
| `Edit` | high | 精确修改文件 | `file_path`, `old_string`, `new_string`, `replace_all` | `Edit` |
| `Write` | high | 写入/覆盖文件 | `file_path`, `content` | `Write` |
| `Glob` | low | 按名称查找文件 | `pattern`, `path`, `offset`, `limit` | `Glob` |
| `Grep` | low | 内容搜索（正则） | `pattern`, `path`, `glob`, `offset`, `limit` | `Grep` |
| `LS` | low | 列出目录子项 | `path`, `offset`, `limit` | `LS` |
| `Bash` | high | 执行 Shell 命令 | `command`, `timeout`, `run_in_background` | `Bash` |
| `BashStatus` | low | 查询后台任务 | `task_id`, `wait`, `timeout` | `BashStatus` |
| `BashStop` | medium | 终止后台任务 | `task_id` | `BashStop` |
| `Upload` | medium | 客户端上传文件 | `file_name`, `size`, `sha256`, `file_id` | （专用） |

---

## 二、网站（15 个）

| 工具 | 风险 | 功能 | 关键参数 |
|------|------|------|---------|
| `SiteList` | low | 网站列表 | `search`, `page`, `page_size` |
| `SiteGetConfig` | low | 站点配置 | `site_name` |
| `SiteLogs` | low | 访问日志 | `site_name` |
| `SiteTraffic` | low | 站点流量 | `site_name` |
| `SiteCreate` | medium | 创建网站 | `domain`, `site_path`, `port`, `php_version` |
| `SiteDelete` | **high** | 删除网站 | `site_name`, `delete_path`, `ftp`, `database`, `confirm` |
| `OneClickDeploy` | medium | 一键部署 CMS | `site_name`, `app` |
| `TrafficAnalysis` | low | 全站流量分析 | 无 |
| `SiteCertList` | low | 证书库列表 | `search`, `status_filter`, `force_refresh` |
| `SiteSSLDeploy` | medium | 部署 SSL | `site_name`, `ssl_hash`/`certificate`/`key` |
| `SiteSSLApply` | medium | 申请 SSL | `site_name`, `domains`, `validation` |
| `DomainManage` | **high** | 域名增删 | `site_name`, `operation`, `domains` |
| `SiteConfig` | medium | PHP 版本/伪静态 | `site_name`, `action`, `value` |
| `SiteControl` | medium | 启停站点 | `site_name`, `action` |
| `SiteBackup` | medium | 备份站点 | `site_name` |

---

## 三、网络（3 个）

| 工具 | 风险 | 功能 |
|------|------|------|
| `WebFetch` | low | 抓取网页 Markdown（`url`, `prompt`） |
| `ServerIP` | low | 获取内外网 IP（无参数） |
| `Upload` | medium | 客户端上传文件（见基础工具） |

---

## 四、数据库（6 个）

| 工具 | 风险 | 功能 | 关键参数 |
|------|------|------|---------|
| `DatabaseList` | low | 数据库列表 | `search` |
| `DatabaseCreate` | medium | 创建数据库 | `name`, `db_user`, `password`, `codeing`, `address`, `ps` |
| `DatabaseDelete` | **high** | 删除数据库 | `name` |
| `DatabaseBackup` | medium | 备份数据库 | `name` |
| `MysqlQuery` | low | 只读 SQL | `sql`, `database`, `params`, `limit` |
| `MysqlExecute` | **high** | 写 SQL | `sql`, `database`, `params`, `confirm` |

---

## 五、服务（2 个）

| 工具 | 风险 | 功能 | 关键参数 |
|------|------|------|---------|
| `ServiceStatus` | low | 服务状态 | `service_names` |
| `ServiceControl` | medium | 启停服务 | `service_names`, `action` |

---

## 六、Docker（10 个）

| 工具 | 风险 | 功能 | 关键参数 |
|------|------|------|---------|
| `ContainerList` | low | 容器列表 | 无 |
| `ContainerLogs` | low | 容器日志 | `container`, `lines` |
| `ContainerInspect` | low | 容器详情 | `container` |
| `ComposeList` | low | compose 项目 | 无 |
| `ImageList` | low | 镜像列表 | 无 |
| `VolumeList` | low | 存储卷 | 无 |
| `NetworkList` | low | docker 网络 | 无 |
| `ContainerControl` | medium | 启停容器 | `container`, `action` |
| `ContainerDelete` | **high** | 删除容器 | `container` |
| `ImagePull` | medium | 拉取镜像 | `image`, `registry`, `username`, `password` |

---

## 七、系统（1 个）

| 工具 | 风险 | 功能 |
|------|------|------|
| `SystemInfo` | low | CPU/内存/磁盘/负载/运行时长/系统版本（无参数） |

---

## 八、软件商店（3 个）

| 工具 | 风险 | 功能 | 关键参数 |
|------|------|------|---------|
| `SoftwareList` | low | 软件商店清单 | `search`, `page`, `page_size` |
| `SoftwareInstall` | medium | 安装软件 | `name`, `version`, `type` |
| `SoftwareUninstall` | **high** | 卸载软件 | `name`, `version`, `type` |

---

## 九、防火墙（5 个）

| 工具 | 风险 | 功能 | 关键参数 |
|------|------|------|---------|
| `FirewallStatus` | low | 防火墙状态 | 无 |
| `FirewallPortList` | low | 端口规则 | `chain`, `search`, `page`, `page_size` |
| `FirewallIpList` | low | IP 规则 | `chain`, `search`, `page`, `page_size` |
| `FirewallPortSet` | **high** | 端口规则增删 | `operation`, `port`, `protocol`, `address`, `strategy` |
| `FirewallIpSet` | **high** | IP 规则增删 | `operation`, `address`, `strategy`, `chain`, `family` |

---

## 十、Java 项目（6 个）

| 工具 | 风险 | 功能 |
|------|------|------|
| `JavaJdk` | medium | 管理 JDK（`action`, `version`, `jdk_path`） |
| `JavaProjectCreate` | medium | 创建 Java 项目 |
| `JavaProjectInfo` | low | 查看 Java 项目（`project_name`） |
| `JavaProjectControl` | medium | 启停 |
| `JavaProjectModify` | medium | 修改配置/域名 |
| `JavaProjectDelete` | **high** | 删除 |

---

## 十一、NodeJS 项目（6 个）

| 工具 | 风险 | 功能 |
|------|------|------|
| `NodeVersion` | medium | 管理 Node 版本（`action`, `version`, `install_pm2/yarn`） |
| `NodeProjectCreate` | medium | 创建项目 |
| `NodeProjectInfo` | low | 查看项目 |
| `NodeProjectControl` | medium | 启停 |
| `NodeProjectModify` | medium | 修改配置 |
| `NodeProjectDelete` | **high** | 删除 |

---

## 十二、Python 项目（8 个）

| 工具 | 风险 | 功能 |
|------|------|------|
| `PythonVersion` | medium | 管理 Python 版本（`action`, `version`, `is_pypy`） |
| `PythonEnv` | medium | 虚拟环境/pip |
| `PythonProjectCreate` | medium | 创建项目 |
| `PythonProjectInfo` | low | 查看项目（含 `include_packages`） |
| `PythonProjectControl` | medium | 启停 |
| `PythonProjectService` | medium | 关联进程管理 |
| `PythonProjectModify` | medium | 修改配置/域名/反代 |
| `PythonProjectDelete` | **high** | 删除 |

---

## 十三、Go 项目（6 个）

| 工具 | 风险 | 功能 |
|------|------|------|
| `GoVersion` | medium | 管理 Go SDK（`action`, `version`, `goproxy`） |
| `GoProjectCreate` | medium | 创建项目 |
| `GoProjectInfo` | low | 查看项目 |
| `GoProjectControl` | medium | 启停 |
| `GoProjectModify` | medium | 修改配置 |
| `GoProjectDelete` | **high** | 删除 |

---

## 十四、反向代理（5 个）

| 工具 | 风险 | 功能 |
|------|------|------|
| `ProxyProjectCreate` | medium | 创建反代 |
| `ProxyProjectInfo` | low | 查看反代 |
| `ProxyProjectModify` | medium | 修改反代（`remark/start/stop/add_domain/remove_domain/force_https`） |
| `ProxyWriteConfig` | medium | 编辑 nginx conf |
| `ProxyProjectDelete` | **high** | 删除反代 |

---

## 十五、HTML 静态项目（4 个）

| 工具 | 风险 | 功能 |
|------|------|------|
| `HtmlProjectInfo` | low | 查看静态项目 |
| `HtmlProjectCreate` | medium | 创建静态项目 |
| `HtmlProjectModify` | medium | 修改配置/域名 |
| `HtmlProjectDelete` | **high** | 删除 |

---

## 十六、SSH（3 个）

| 工具 | 风险 | 功能 | 关键参数 |
|------|------|------|---------|
| `SSHInfo` | low | SSH 状态/配置 | 无 |
| `SSHConfig` | **high** | 密钥/重启 sshd | `action`（`key`/`key_off`/`restart`）, `value` |
| `SSHIntrusion` | low | 异常登录统计 | 无 |

---

## 十七、安全（1 个）

| 工具 | 风险 | 功能 |
|------|------|------|
| `SecurityCheck` | low | 安全评分、10 项检查、SSH 危险命令历史 |

---

## 十八、计划任务（2 个）

| 工具 | 风险 | 功能 | 关键参数 |
|------|------|------|---------|
| `GetCrontab` | low | 任务列表 | `search`, `category`, `page`, `page_size` |
| `ManageCrontab` | **high** | add/del | `action`, `id`, `name`, `schedule`, `task` |

---

## 十九、通知（3 个）

| 工具 | 风险 | 功能 | 关键参数 |
|------|------|------|---------|
| `GetChannel` | low | 通道列表 | `refresh` |
| `ManageChannel` | **high** | add/del/status/test | `action`, `id`, `type`, `title`, `data` |
| `SendMessage` | medium | 发消息 | `channel_id`, `content`, `title` |

---

## 风险等级速查

### 只读查询（low，可直接调用）

- `SiteList` / `SiteGetConfig` / `SiteLogs` / `SiteTraffic` / `SiteCertList`
- `DatabaseList` / `MysqlQuery`
- `ServiceStatus`
- `ContainerList` / `ContainerLogs` / `ContainerInspect` / `ComposeList` / `ImageList` / `VolumeList` / `NetworkList`
- `SystemInfo`
- `SoftwareList`
- `FirewallStatus` / `FirewallPortList` / `FirewallIpList`
- `JavaProjectInfo` / `NodeProjectInfo` / `PythonProjectInfo` / `GoProjectInfo`
- `ProxyProjectInfo` / `HtmlProjectInfo`
- `SSHInfo` / `SSHIntrusion`
- `SecurityCheck`
- `GetCrontab` / `GetChannel`
- `TrafficAnalysis`

### 中等风险（medium，需说明但通常可执行）

- `SiteCreate` / `SiteSSLDeploy` / `SiteSSLApply` / `SiteConfig` / `SiteControl` / `SiteBackup` / `OneClickDeploy`
- `DatabaseCreate` / `DatabaseBackup`
- `ServiceControl`
- `ContainerControl` / `ImagePull`
- `SoftwareInstall`
- 所有 `*ProjectCreate` / `*ProjectControl` / `*ProjectModify`（除 Delete）
- `ProxyProjectCreate` / `ProxyProjectModify` / `ProxyWriteConfig` / `HtmlProjectCreate` / `HtmlProjectModify`
- `JavaJdk` / `NodeVersion` / `PythonVersion` / `PythonEnv` / `GoVersion`
- `BashStop`（已有任务时）
- `SendMessage`

### 高风险（high，**每次必须用户明确确认**）

- `Edit` / `Write`（文件覆盖）
- `Bash`（任意命令）
- `SiteDelete` / `DomainManage`
- `DatabaseDelete` / `MysqlExecute`
- `ContainerDelete`
- `SoftwareUninstall`
- `FirewallPortSet` / `FirewallIpSet`（防火墙变更可能锁死自己）
- 所有 `*ProjectDelete`
- `ProxyProjectDelete` / `HtmlProjectDelete`
- `SSHConfig`（重启 sshd 可能锁死）
- `ManageCrontab` / `ManageChannel`

---

## WorkBuddy 通用工具映射

| MCP 工具类别 | WorkBuddy 等价能力 |
|------------|------------------|
| `SiteList` / `DatabaseList` / `ContainerList` 等列表类 | 由 Bash + grep 实现，无需 MCP（除非面板在远端） |
| `ServiceStatus` | `systemctl status <svc>` |
| `SystemInfo` | `uptime; free -m; df -h; top` |
| `MysqlQuery` | `mysql -e "SELECT ..."` |
| `SiteCreate` / `DatabaseCreate` | 通用工具做不到（需面板内部 API） |
| `FirewallPortSet` | `firewall-cmd` / `ufw` / `iptables`（本机） |
| `SoftwareInstall` | `yum install` / `apt install`（本机） |

**结论**：本机操作时 90% 工具可由 WorkBuddy 通用工具替代；**远程跨主机操作、批量面板管理、多面板运维**才需要 MCP。

---

## 工具选择决策树

```
目标是什么？
├─ 只读查询
│  ├─ 本机 → 用 WorkBuddy 通用工具（更轻量）
│  └─ 远端 → MCP low 工具
├─ 创建资源（站点/数据库/项目）
│  ├─ 本机 → 用 WorkBuddy 通用工具 + 手工命令
│  └─ 远端 → MCP medium 工具（先确认）
└─ 修改/删除资源
   ├─ 本机 → 用 WorkBuddy 通用工具（高危，需授权）
   └─ 远端 → MCP high 工具（每次二次确认）
```

## 参考

- 完整工具签名：https://docs.bt.cn/ai-ops/mcp/tools-reference
- 安装与配置：参考 `baota-mcp-integration` skill
- 调用示例：`python3 scripts/build.py` 后的 plugin.json 中所有工具的具体 schema