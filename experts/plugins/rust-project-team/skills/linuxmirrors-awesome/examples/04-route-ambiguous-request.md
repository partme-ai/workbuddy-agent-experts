# 示例：模糊需求路由

**用户**：帮我换 Docker 源。

**安全假设**：先按“Docker 已安装，只更换 Registry，不执行”给示例。

**待补充**：OS/版本、Docker 状态、CE 软件源还是镜像拉取、现有 daemon.json、目标 Registry。

**路由**：若是包安装慢进入 CE 仓库流程；若 `docker pull` 慢进入 Registry 流程；若未安装进入完整安装流程。
