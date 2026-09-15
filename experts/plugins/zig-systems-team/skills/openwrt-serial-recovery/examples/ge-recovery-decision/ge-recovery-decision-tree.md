# GE · 串口救砖三级梯度决策树（openwrt-serial-recovery 黄金示例）

**徽章**：`B0 Build Verification Only`（文档类，需硬件验证）

---

## Level 1：U 盘 / SD 卡恢复（软件级，无需硬件改造）

**适用条件**：设备仍可从 U 盘/SD 卡启动（Amlogic 设备插靠 HDMI 的 USB 口优先识别）

**操作**：
1. 下载官方或 ophub 的 N1 专用镜像（`openwrt_s905d_n1_*.img.gz`）
2. BalenaEtcher 写入 U 盘
3. 设备断电 → 插入 U 盘 → 通电 → 自动从 U 盘启动
4. SSH 登录后执行 `openwrt-install-amlogic` 或 `armbian-install` 重新写入 eMMC

**预期**：U 盘启动后浏览器 192.168.1.1 可访问 → 写入 eMMC → 拔盘重启恢复

**证据**：SSH 日志 + 浏览器截图

---

## Level 2：TTL 串口进入 U-Boot 命令行（需硬件，USB-TTL 适配器）

**适用条件**：U 盘启动无效，但串口有输出（Amlogic S905 系列默认 UART 波特率 115200 8N1，**以板实测为准**）

**硬件准备**：
- USB-TTL 适配器（CH340/CP2102/FT232，3.3V 电平）
- 杜邦线 3 根（GND、TX、RX——交叉连接：适配器 TX→设备 RX，适配器 RX→设备 TX）

**操作**：
1. 连接 TTL 线，打开串口终端（`minicom -D /dev/ttyUSB0 -b 115200` 或 PuTTY）
2. 设备断电 → 通电 → 立即观察串口输出
3. 若出现 `Hit any key to stop autoboot` → 按回车进入 U-Boot 命令行
4. 在 U-Boot 中执行 `usb start` → `fatload usb 0 0x01080000 uImage` → `bootm`（从 U 盘加载内核）

**预期**：U-Boot 命令行可用 → 手动引导内核 → 进系统后修复

**证据**：串口日志（minicom capture / screen log）

**Pending HIL**：具体引脚位置以板原理图或 ophub 文档为准（Amlogic S905D N1 串口位置已有社区实测）

---

## Level 3：编程器 / 短接（硬件级，超出本技能范围）

**适用条件**：Level 1/2 均无效（设备无串口输出/无 U 盘响应）

**操作**：
- 使用 USB Burning Tool（Amlogic 官方工具）通过 USB 线刷回原厂固件
- 需要 Amlogic 芯片进入刷机模式（部分设备需短接特定触点）

**本技能声明**：Level 3 操作超出本通用技能覆盖范围——短接点位置、编程器参数、原厂固件来源均为设备专属事实，**禁止编造**，路由官方原理图/ophub tools/fw-hil-testing 实测。

---

## 先软后硬原则

| 阶段 | 操作 | 成本 |
|---|---|---|
| 1 | U 盘恢复 | 零成本，10 分钟 |
| 2 | 串口救援 | 适配器 ¥10-30，30 分钟 |
| 3 | 编程器/短接 | ¥50+工具，1-2 小时，**需实物验证** |

**核心规则**：每个 Level 失败后才升级到下一个；不要跳级操作（直接拆机短接）导致不必要的风险。

---

## 排障参考

| 现象 | 可能原因 | 优先操作 |
|---|---|---|
| 上电无任何输出 | 电源故障 / 硬件损坏 | 检查电源 12V/2A；Level 2 |
| 串口有输出但卡在 kernel panic | 内核/DTB 不匹配 | Level 1 重刷；Level 2 手动引导 |
| 系统正常但浏览器打不开 | 网络配置错误 | 串口登录改 UCI network |
| 频繁重启 | 供电不稳 / 硬盘短路 | 拔硬盘测试；换电源 |
