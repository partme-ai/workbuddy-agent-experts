# 主脚本与 Lite

`DockerInstallation.sh` 提供完整交互、安装、版本选择、CE 软件源和 Registry 配置。

`DockerInstallationLite.sh` 是精简版本；使用前检查其当前 `--help` 与源码，确认发行版、指定版本和 Registry 模式是否满足需求。

生产环境建议下载固定提交的脚本到受控位置，经 Shell 审查后执行。不要把官网短地址在每次部署时无版本固定地直接运行。
