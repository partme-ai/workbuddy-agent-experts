# 板型数据库速查（model_database.conf）

来源：`make-openwrt/openwrt-files/common-files/etc/model_database.conf`（ophub/amlogic-s9xxx-openwrt HEAD `c593d56`，走读 2026-09-02）。**权威是你仓库里的该文件**，本文是带行号的摘录与解释。

## 15 列结构（conf L14-15）

| # | 列 | 说明 |
|---|----|------|
| 1 | ID | 行 id；标注 `[IDL]` 的行 ID 锁定（conf L45），安装/更新脚本依赖，不得改 |
| 2 | MODEL | 型号名，逗号并列多个别名（匹配用户口语） |
| 3 | SOC | SoC：s905d / s905x / s922x / rk3568 … |
| 4 | FDTFILE | 启动 DTB 文件名，必须由 ophub 内核 dtb 包提供，remake 不生成 |
| 5 | UBOOT_OVERLOAD | Amlogic 重载 u-boot（拷入 bootfs，如 `u-boot-n1.bin`）；Rockchip 语义为 TRUST_IMG（conf L17） |
| 6 | MAINLINE_UBOOT | 主线 u-boot（dd 进镜像头部）；`NA` 则回退第 7 列 |
| 7 | BOOTLOADER_IMG | 原厂 bootloader 镜像（dd 进镜像头部） |
| 8 | DESCRIPTION | 硬件要点（内存/网口/wifi 芯片） |
| 9 | KERNEL_TAGS | `tags/list` 语法，如 `stable/all`（解析规则见 kernel-lines.md） |
| 10 | PLATFORM | amlogic / rockchip / allwinner（remake L712 白名单） |
| 11 | FAMILY | u-boot/DTB 家族，如 meson-gxl |
| 12 | BOOT_CONF | `uEnv.txt` 或 `extlinux.conf`（remake L1015-1026 据此决定是否启用 extlinux） |
| 13 | CONTRIBUTORS | 贡献者 GitHub id |
| 14 | BOARD | **remake `-b` 参数用的板型 id**（≠ MODEL 别名） |
| 15 | BUILD | yes/no；`-b all` 只挑 yes 行（remake L311-317） |

## N1 行原文（conf L52，ID 101）

```text
101     :Phicomm-N1   :s905d   :meson-gxl-s905d-phicomm-n1.dtb   :u-boot-n1.bin
        :NA   :u-boot-2015-phicomm-n1.bin   :2GB-Mem,1Gb-Nic,brcm43455-wifi
        :stable/all   :amlogic   :meson-gxl   :uEnv.txt   :unifreq   :s905d   :yes
```

字段解读：

- `-b` 的值是第 14 列 **`s905d`**，不是 `n1` 也不是 `Phicomm-N1`；`-b` 多板用 `_` 连接（remake L360-362 去重）。
- FDTFILE=`meson-gxl-s905d-phicomm-n1.dtb`：由 ophub kernel 的 `dtb-amlogic-<ver>.tar.gz` 提供；ID 102 的 `-thresh` 变体是另一个 DTB（conf L53），别混。
- **双层 u-boot**：MAINLINE_UBOOT=`NA` → make_image 回退 dd `BOOTLOADER_IMG=u-boot-2015-phicomm-n1.bin`（remake L835-837）；`UBOOT_OVERLOAD=u-boot-n1.bin` 拷入 bootfs，5.10 内核路径还会复制为 `u-boot.ext`（remake L987-995）。
- KERNEL_TAGS=`stable/all`：stable 线全部内核可用（默认 6.12.y/6.18.y，见 kernel-lines.md）。

## `-b` 语法全集（conf L34-43，实现 remake L311-363）

| 写法 | 语义 |
|---|---|
| `-b all` | 所有 BUILD=yes 的板 |
| `-b first50` / `-b last50` | BUILD=yes 的前/后 50 块 |
| `-b range50_100` | BUILD=yes 第 51~100 块 |
| `-b amlogic` | 平台全选；`amlogic50` 前推 50；`amlogic50_100` 切片 |
| `-b s905d_s905x` | 指定 BOARD，`_` 分隔，忽略 BUILD 列，取每板第一匹配行（remake L687-691） |

## 查板流程

1. `grep -i "<型号或别名>" model_database.conf` 命中第 2 列 → 取第 14 列 BOARD、第 4 列 FDTFILE、第 9 列 KERNEL_TAGS、第 12 列 BOOT_CONF。
2. 命中多行（别名并列）→ 向用户确认具体硬件差异（第 8 列）。
3. **查无此板 → 停**。不要猜 BOARD，不要编 DTB 文件名。

## 新增板型流程（模式）

1. 上游 ophub/amlogic-s9xxx-openwrt 提 PR 修改 model_database.conf；FDTFILE 必须与 ophub/kernel 对应版本 dtb 包内实际文件一致（下载 `dtb-amlogic-<ver>.tar.gz` 核对文件名，运行时核验）。
2. 不允许只改本地 openwrt-files 后宣称"支持新板"（零 commit 纪律，SKILL.md Pitfalls）。
3. 新行需自填 CONTRIBUTERS 与 15 列；`[IDL]` 锁定 ID 不得复用。

## 查无此板的实例：小米盒子3（S905-H）

- conf 中**没有** s905h 专属行（`grep -i s905h` 无结果，走读 2026-09-02）。
- 存在通用 SOC=s905 行：conf L207 BOARD=`s905`（meson-gxbb 家族，FDTFILE=`meson-gxbb-p201.dtb`，BUILD=yes）——需要用 s905 世代盒子时以此为入口。
- S905-H 世代盒子社区普遍反馈 eMMC 写入受限、仅 U 盘启动可用；上游文档只保证"USB 启动优先于 eMMC"（documents/README.cn.md L671）。具体某台设备能否写 eMMC，以运行时核验（TTL 观察/短接/写入测试）为准，**不要替用户断言**。

## 排错补充：BOARD 查无匹配

`-b <board>` 在 `model_database.conf` 查无匹配行时，`remake` 的 `confirm_version`（上游 L687-692）报 `The [ x ] configuration not found!` 并退出——先核对拼写（N1 用 `s905d`，不是 `n1`），再查板型库。
