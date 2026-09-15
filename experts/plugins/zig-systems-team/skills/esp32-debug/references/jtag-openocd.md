# JTAG / OpenOCD 设置要点

走读 2026-09-02。机制事实出自 ESP-IDF 基线 §10（官方 jtag-debugging 文档，高置信）；**接线、频率、板级参数：以板与探测器件实测**（官方未逐板抓取，不编造）。

## 1. 前提事实（基线高置信）

- OpenOCD **随 IDF 安装**，无需另装；启动形如 `openocd -f board/<目标板>.cfg`。
- **经典 ESP32 无内置 USB-Serial/JTAG**：JTAG 需外部适配器（如 ESP-Prog）。
- **不支持 SWD**——排任何"SWD 调 ESP32"的任务都属误导，走 JTAG。
- 能力：经 JTAG 烧录与 GDB 调试（对应工具为 Xtensa/RISC-V 目标的 GDB）。
- board cfg 文件名以随 IDF 安装的 OpenOCD 脚本目录实际列表为准（`find` 运行时查），不凭记忆写。

## 2. 硬件连接（纪律优先）

| 项 | 规则 |
|---|---|
| 探测器 | ESP-Prog 类外部 JTAG 探测器；型号与目标板先核对 |
| 接线 | JTAG 信号组（TCK/TMS/TDI/TDO/TRSTn/SRSTn 类）按**探测器件与目标板的官方引脚文档**对照，逐根复核；引脚定义本文件不列（防编造） |
| 电平 | 目标板 I/O 电平与探测器设置必须一致；不确定先量后接 |
| 频率（TCK 等） | 从保守值起试，**以板与探测器件实测**为准；出现不稳定先降频再排查 |
| 共地 | 探测器与目标板必须共地；供电关系（谁给谁供电）按板文档确认 |

## 3. 软件流程

1. **运行时核验环境**：

```bash
idf.py --version
# board cfg 以本地 OpenOCD 脚本目录实际列表为准：
openocd -f board/your-board.cfg   # cfg 名查本地 scripts/board/ 目录
```

2. GDB 连接后验证三件事：断点命中、单步、变量查看（Validation Gate 4）。
3. 断点行为异常：先怀疑接线/TCK 频率/供电，再怀疑工具链版本。
4. 不需要 JTAG 硬件时：运行时 GDB stub（CONFIG_ESP_SYSTEM_GDBSTUB_RUNTIME，基线高置信）可作串口 GDB 手段——其专用文档页基线未抓到（UNVERIFIED），配置以 menuconfig 内 Kconfig 描述为准。

## 4. JTAG vs Coredump vs 串口（选型）

| 情形 | 选 |
|---|---|
| 崩溃随机、无法实时盯 | coredump（flash 优先） |
| 已有现场，只需事后分析 | `idf.py coredump-info` / `coredump-debug` |
| 逻辑问题可稳定复现，要断点单步 | JTAG/OpenOCD |
| 没有探测器，临时要 GDB | 运行时 GDB stub |
| 只想看日志 | `idf.py monitor` |

## 5. 反幻觉边界

- 本文件不提供：任何具体板的 JTAG 排针引脚号、TCK 具体频率数值、board cfg 文件名清单——逐板回答 = 查官方板文档或实测（Pending HIL），拒绝凭记忆给值。
- S/C 系列芯片内置 USB-Serial/JTAG 的支持情况按各芯片官方文档运行时核验；经典 ESP32 的"需外部适配器 + 不支持 SWD"为基线高置信可直接引用。
