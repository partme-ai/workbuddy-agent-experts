# 示例：CI 无人值守

**用户**：生成自动换源命令，不要交互。

**安全假设**：只生成审阅版，固定 OS、镜像、branch，显式 `--backup true --upgrade-software false --clean-cache false --clean-screen false --print-diff --pure-mode`。

**执行前**：验证镜像元数据，固定脚本提交，将 stdout/diff 存档。

**失败处理**：包索引刷新非零立即停止流水线并恢复备份，不继续安装依赖。
