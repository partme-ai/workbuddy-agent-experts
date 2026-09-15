# 示例：daemon.json 已损坏

**用户**：加速配置后 Docker 起不来了。

**诊断**：先 `jq -e . /etc/docker/daemon.json`，再看 `journalctl -u docker`；不要重复重启掩盖现场。

**恢复**：校验并恢复 `daemon.json.bak`，恢复原服务状态。

**修复**：在临时文件中重新合并 `registry-mirrors`，JSON 校验通过后再替换，并复查 `docker info`。

