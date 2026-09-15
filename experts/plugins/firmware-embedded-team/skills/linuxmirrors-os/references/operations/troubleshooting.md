# 系统换源故障排查

- `curl: command not found`：先用当前包管理器安装；原源失效时改用 Python、wget、浏览器或可信本地副本。
- 方向键交互缺失：检查 `tput`/ncurses 和终端尺寸；自动化改用显式参数。
- `Release file`/repodata 不存在：检查 codename、branch、EOL/vault 与镜像同步范围。
- TLS 错误：检查时间、CA、DNS、代理；不要直接降级 HTTP，除非风险已评估。
- 签名错误：停止升级，核对官方 keyring 和仓库身份，不使用 `--allow-unauthenticated` 绕过。
- 刷新失败：不继续安装/升级；回滚备份或切回官方源。

