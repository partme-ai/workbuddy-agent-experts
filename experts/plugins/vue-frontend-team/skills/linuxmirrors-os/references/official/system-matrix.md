# 系统与包管理器矩阵

| 家族 | 代表系统 | 包管理器/验证 |
|---|---|---|
| Debian | Debian、Ubuntu、Kali、Mint、Deepin、Proxmox | `apt-get update` |
| Red Hat | RHEL、CentOS、Rocky、Alma、Fedora、openEuler | `dnf makecache` 或 `yum makecache` |
| SUSE | openSUSE | `zypper refresh` |
| Arch | Arch、Manjaro、EndeavourOS | `pacman -Sy` |
| Alpine | Alpine | `apk update` |
| Gentoo | Gentoo | `emerge --sync` |
| Nix | NixOS | 检查 `nix.conf` 并执行适合当前 Nix 版本的验证 |

最终支持性以官网版本范围、脚本识别分支和目标镜像同步状态三者共同决定。
