# 备份与回滚

官网说明主脚本通常在原绝对路径后加 `.bak`。回滚前先确认备份确为变更前版本。

| 家族 | 常见恢复对象 | 恢复后验证 |
|---|---|---|
| Debian | `/etc/apt/sources.list(.bak)` 或 `.sources.bak` | `apt-get update` |
| Red Hat | `/etc/yum.repos.d(.bak)` | `dnf/yum makecache` |
| SUSE | `/etc/zypp/repos.d(.bak)` | `zypper refresh` |
| Arch | `/etc/pacman.d/mirrorlist.bak` | `pacman -Sy` |
| Alpine | `/etc/apk/repositories.bak` | `apk update` |

恢复步骤：停止升级 → 保存失败现场 → 校验备份 → 原子恢复 → 刷新索引 → 验证原域名。没有可信备份时改用系统官方仓库文档重建。
