# 示例：多个 Mirror

**用户**：配置两个 Registry 地址作为容错。

**计划**：核验两个 HTTPS 地址，在 `--source-registry` 中用英文逗号分隔；顺序是配置优先级，不宣称自动测速。

**保护**：JSON 级合并并保留其他 daemon 配置，临时文件通过 `jq -e` 后原子替换。

**验证**：`docker info`、服务日志和拉取测试；单地址故障时记录实际 fallback 行为。
