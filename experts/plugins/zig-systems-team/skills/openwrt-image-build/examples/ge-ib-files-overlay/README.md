# GE-2 · Image Builder FILES= 覆盖层注入验证（openwrt-image-build 黄金示例）

**结论徽章**：`Build Verified`（执行日期 2026-09-02）+ **注入语义端到端实证**
**验证技能**：本技能 Workflow 全链路 + `references/files-injection-semantics.md` 的全部 5 条语义
**附带产出**：回答了 TinyNAS 项目悬置的 POC P1（见下"关键发现"）

## 被测物

| 项 | 值 |
|---|---|
| Image Builder | `openwrt-imagebuilder-25.12.5-armsr-armv8.Linux-x86_64.tar.zst`（官方，sha256 OK） |
| 运行环境 | Docker 命名卷（ge2vol）内 `ubuntu:24.04`——**必须用卷而非 host 挂载**：OpenWrt 构建要求大小写敏感文件系统，Docker Desktop 的 macOS bind mount 是不敏感 APFS（踩坑实录） |
| 构建命令 | `make image PROFILE=generic PACKAGES="curl jq" FILES=/work/files` |
| 覆盖层 | `files/etc/golden-marker`（内容 GOLDEN-OK）+ `files/etc/init.d/golden-boot`（rc.common shebang + START=99） |

## 关键发现（对链路 B / TinyNAS POC P1 的答案）

**armsr/armv8 的 IB 默认产出 `*-rootfs.tar.gz`**（实测产物列表：`generic-rootfs.tar.gz` 5.7MB + `generic-targz-rootfs.tar.gz`）。ophub remake 所需输入**无需任何 .config 调整**即天然存在——TinyNAS POC P1 **通过**。

## 注入验证证据（injection-verify.txt，经 rootfs.tar.gz 直读）

| 断言（对应 files-injection-semantics.md） | 证据 |
|---|---|
| FILES= 覆盖合并：覆盖层文件落入 rootfs | `tar -xzOf … ./etc/golden-marker` → `GOLDEN-OK` |
| init.d 自动 enable：含 rc.common shebang 的脚本生成 `/etc/rc.d/S<NN>` 链接 | `tar -tzf` → `./etc/rc.d/S99golden-boot` |
| 脚本原样进入 init.d | `./etc/init.d/golden-boot` 头两行 = `#!/bin/sh /etc/rc.common` / `START=99` |
| 产物完整性 | `sha256sums` 随产物生成 |

## 踩坑记录（供技能演进）

1. Docker Desktop macOS：host bind mount 大小写不敏感 → `make image` 报 "OpenWrt can only be built on a case-sensitive filesystem"。**解法：命名卷**。
2. 验证 rootfs 内容用 `rootfs.tar.gz` 直读（tar -tzf/-xzOf）比 debugfs 读 ext4 更简单——且注意别把 `.img.gz` 当裸 img 喂 debugfs。
