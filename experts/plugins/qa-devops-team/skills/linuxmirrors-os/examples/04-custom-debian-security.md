# 示例：Debian 主源与 security 分离

**用户**：主源走校内镜像，security 走官方源。

**处理**：核验 codename 与两个仓库路径，分别使用 `--source/--branch` 和 `--source-security/--branch-security`，或官方源开关。

**验证**：检查生成条目组件和 suites，运行 `apt-get update`。

**回滚**：恢复 `.sources.bak`/`sources.list.bak`；不要用禁用签名绕过错误。
