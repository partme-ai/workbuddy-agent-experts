# FILES= 注入语义逐条解析（files-injection-semantics）

依据：上游 `include/rootfs.mk` `prepare_rootfs` 宏（基线 25.12.5，走读 2026-09-02）与 `rules.mk` `file_copy` 宏。行号引用均指基线源码。

## 1. 覆盖层如何进 rootfs（rootfs.mk:72-74 → rules.mk:475-488）

```make
$(call prepare_rootfs,$(TARGET_DIR),$(USER_FILES),$(DISABLED_SERVICES))
# prepare_rootfs 内部：
$(if $(2),@if [ -d '$(2)' ]; then $(call file_copy,$(2)/.,$(1)); fi)
```

`file_copy` 两步：
1. 遍历目标 rootfs 中与覆盖层同路径的**符号链接**并 `rm -f`（"Removing symlink"），防止 cp 跟随链接写穿（rules.mk:480-486）；
2. `$(CP)` 把覆盖层拷入 rootfs：同路径覆盖、其余合并。

**结论**：FILES= 是"合并覆盖"。想删掉 rootfs 里某个既有文件，FILES= 做不到（它只增改不删）——替代方案：用 `-包名` 移除所属包，或 UCI 覆盖其行为。

## 2. postinst 重放（rootfs.mk:84-94）

opkg 包的 `usr/lib/opkg/info/*.postinst` 在装包阶段可能因 offline-root 未执行成功，`prepare_rootfs` 用 bash 逐个重放（`IPKG_INSTROOT=$(1)`）；**任一脚本非零退出 → 整个镜像构建失败**（"postinst script ... has failed"）。

排查含义：构建在此报错时，先看是哪个包的 postinst，通常是覆盖层破坏了它要配置的文件（如同名 UCI 文件语法错）。

## 3. init.d 自动 enable / DISABLED_SERVICES（rootfs.mk:104-113）

对 rootfs 内每个 `/etc/init.d/*`：
- 无 `#!/bin/sh /etc/rc.common` shebang → 跳过（不会自启）；
- basename 不在 `DISABLED_SERVICES` → 执行 `rc.common <script> enable`（生成 `/etc/rc.d/Sxx…` 链接）；
- 在 `DISABLED_SERVICES` → `disable`。

**结论**：覆盖层只放 `/etc/init.d/xxx`，不要手放 `/etc/rc.d/`。要"默认不自启"：`make image DISABLED_SERVICES="xxx"`。

## 4. 装包与 opkg 选项（rootfs.mk:35-44 + IB Makefile:93-97）

IB 的包安装走 `opkg --offline-root $(TARGET_DIR) --force-postinstall --add-dest root:/ --add-arch all:100 --add-arch <ARCH>:200`，源是 `repositories.conf`。**IB 输入是 ipk，不是 rootfs tar 包**。

## 5. 构建期清理（rootfs.mk:116-123）

镜像收尾会删除：`/boot`、`/tmp/*`、postinst 文件、`usr/lib/opkg/lists/*`、`/var/lock/*.lock`、VCS 目录。覆盖层放进这些路径的内容不会存活（除 `/etc` 外放临时物请三思）。

## 6. opkg status 修正与 SOURCE_DATE_EPOCH（rootfs.mk:97-102, 126）

- 非 IB 全量构建时把 status 中 `user` 标记改为 `ok`（IB 下跳过）；
- 设了 `SOURCE_DATE_EPOCH` 时，`Installed-Time` 全部改写为固定值，且所有文件 `touch -hcd @epoch` → 可复现构建（见 reproducible-build.md）。

## 7. uci-defaults 的首启执行（运行时，非构建期）

覆盖层放进 `/etc/uci-defaults/` 的脚本在设备**首次启动**时由 `etc/init.d/boot`（`uci_apply_defaults`）逐个 source 执行，成功后删除。因此 uci-defaults 不需要 +x，但**必须幂等且以 `exit 0` 结尾**——非零退出会阻止删除并在下次启动重放。首启配置语义详见 `openwrt-uci-defaults`。

## 8. 权限位审计（生产模板 build-template.sh:135-146）

`$(CP)` 为 `cp -a` 语义，保留源权限。构建前审计：`etc/init.d`、`etc/hotplug.d`、`www/cgi-bin`、`usr/bin` 下文件缺 `+x` 即 fail（`etc/uci-defaults` 豁免——由 sh source）。

## 9. 常见症状对照

| 症状 | 根因（对应上文条目） |
|---|---|
| 文件没出现在镜像里 | 路径拼错/放错层（§1）；或被 §5 清理掉 |
| 服务没自启 | init.d 缺 rc.common shebang（§3）；或被 DISABLED_SERVICES disable |
| 构建失败 postinst failed | §2：覆盖层破坏了包脚本依赖的文件 |
| uci-defaults 反复执行 | §7：缺 `exit 0` 或非幂等 |
| 镜像里出现意外符号链接残留 | §1：file_copy 只清覆盖路径上的链接，其他位置的链接不动 |

## postinst 失败的收敛操作法

最小二分定位：① `PACKAGES=` 只留 `libc kernel base-files` 复跑（基线必过）→ ② 按包列表二分追加，首个失败点即问题包 → ③ 对嫌疑包做“无 FILES= 复跑”区分包自身 vs 覆盖层冲突。**禁止**为出镜像删除失败日志、跳过门禁或强推半验证产物——失败是发布门禁在工作。
