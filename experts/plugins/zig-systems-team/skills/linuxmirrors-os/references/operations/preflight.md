# 换源预检

只读收集：

```bash
cat /etc/os-release
uname -m
id -u
command -v apt-get dnf yum zypper pacman apk emerge nix-env 2>/dev/null
```

随后检查：

1. 当前源文件与目录、磁盘空间和已有 `.bak`。
2. DNS、系统时间、CA 证书与目标镜像 HTTPS。
3. 网络区域、代理/内网地址和维护窗口。
4. 是否允许刷新索引、升级软件包、安装 EPEL 或清理缓存。
5. 带外控制台或 SSH 断开后的恢复通道。

预检不满足时停止变更，只输出修复或手工替代方案。
