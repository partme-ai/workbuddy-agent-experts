# 无人值守与 CI/CD

自动化必须显式固定会改变结果的布尔值，例如：

```bash
bash ./ChangeMirrors.sh \
  --source mirrors.example.com \
  --branch ubuntu \
  --backup true \
  --upgrade-software false \
  --clean-cache false \
  --clean-screen false \
  --print-diff \
  --pure-mode
```

这是结构示例，不是通用可执行答案。执行前替换并核验 OS、仓库路径和镜像元数据。不要默认加入 `--ignore-backup-tips`。CI 应保存脚本版本、标准输出、diff 和包索引刷新结果。
