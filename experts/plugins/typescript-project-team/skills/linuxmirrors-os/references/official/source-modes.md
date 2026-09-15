# 软件源模式

- 中国大陆：默认模式，选择大陆镜像站。
- 中国大陆教育网：使用 `--edu`，只从教育网类型中选择。
- 境外及海外：使用 `--abroad`，避免默认大陆镜像选择。
- 官方源：使用 `--use-official-source true`；EPEL 可独立用 `--use-official-source-epel true`。
- 自定义源：组合 `--source` 与必要的 `--branch`，security/vault/EPEL 等使用各自参数。

“最快”不是静态结论。先以兼容和可用为条件，再在目标主机做 DNS、TLS、元数据和延迟验证。
