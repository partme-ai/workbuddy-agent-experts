# 兼容性摘要

官网在 2026-07-11 展示 27+ 操作系统，包括 Debian、Ubuntu、Kali、Linux Mint、Deepin、Zorin OS、Armbian、Proxmox VE、Raspberry Pi OS、RHEL、Fedora、CentOS、Rocky、AlmaLinux、Oracle Linux、openEuler、OpenCloudOS、openKylin、Anolis OS、openSUSE、Arch、Manjaro、EndeavourOS、Alpine、Gentoo、NixOS、Void Linux。

不要把列表等同于所有版本永久可用：

1. 先检查 `/etc/os-release`、版本和架构。
2. 再核验官网当前版本范围与脚本识别分支。
3. 检查目标镜像站是否同步该发行版与版本。
4. Docker 脚本的范围更窄，主要支持 Debian 系与 Red Hat 系及衍生版。
