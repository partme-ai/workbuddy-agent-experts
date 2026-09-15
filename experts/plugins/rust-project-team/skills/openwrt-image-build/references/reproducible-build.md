# 可复现构建：SOURCE_DATE_EPOCH（reproducible-build）

read-when：CI 需要可校验、可复现的镜像产物，或两次构建 sha256 不一致需要定位时。

## 1. 上游机制（基线 25.12.5，rootfs.mk）

`prepare_rootfs` 中两处受 `SOURCE_DATE_EPOCH` 控制：

- `Installed-Time` 改写：opkg status 数据库中所有包的安装时间统一替换为该 epoch 值（rootfs.mk:102）；
- 全量时间戳归一：rootfs 内所有文件 `find ... -execdir touch -hcd "@$(SOURCE_DATE_EPOCH)" {} +`（rootfs.mk:126，`-h` 连符号链接本身一起改）。

此外收尾清理（rootfs.mk:116-123）本就移除了 postinst、opkg 索引等易变内容——这些是镜像字节级差异的主要来源之一。

## 2. 用法

```bash
export SOURCE_DATE_EPOCH=$(git log -1 --format=%ct)   # 或固定发布日期
make image PROFILE=... PACKAGES=... FILES=...
```

IB 自身亦导出 `SOURCE_DATE_EPOCH`（IB Makefile:31），未设置时镜像内时间戳取构建时刻，两次构建产物不同。

## 3. 验证可复现性

```bash
SOURCE_DATE_EPOCH=1700000000 make image PROFILE=... FILES=... BIN_DIR=out1
SOURCE_DATE_EPOCH=1700000000 make image PROFILE=... FILES=... BIN_DIR=out2
sha256sum out1/* out2/* | sort   # 同类产物哈希应一致
```

不一致时的排查顺序：环境差异（不同 host 工具版本）→ 覆盖层是否带时间戳内容（日志、构建号）→ 包索引版本漂移（repositories.conf 指向的 ipk 是否固定版本）。

## 4. 生产约束

- 覆盖层中不要写入构建时刻（`date`）、随机 ID；运行时标识（版本/档位）用固定值写入（生产模板 build-template.sh:116-123 将 brand/tier/version/channel/build 写入 `/etc/tinynas/`，其中 build 日期由外部固定传入而非构建瞬间生成）；
- 发布门禁（`fw-release-gate`）要求产物 + `.sha256` 成对交付；复现性验证属发布前 Gate；
- 无法复现时如实标注，不得声称"deterministic"。

## 5. 边界

可复现性以"同一 IB 目录 + 同一 ipk 仓库快照 + 同一覆盖层 + 同一 epoch"为前提；上游不承诺跨 host 的字节一致。OpenWrt 官方对 reproducible builds 的支持范围以官方文档为准，本文件只覆盖 IB 侧机制。
