# Host Mocking — 宿主级单测模式（env-var fixture 注入）

> 原则：测逻辑用宿主，不碰设备；断言要独立于实现；证据分层汇报（宿主单测 < boot 冒烟 < 真机 HIL）。

## 1. 模式：脚本自带"数据源覆盖"变量

被测脚本（OpenWrt 用户态 shell/CGI/工具）在生产路径读真实系统位置（`/proc`、`/sys`、`/etc/...`、挂载点）；为可测试，实现时留一个**环境变量根路径覆盖**：变量有值 → 从该目录读；无值 → 默认真实路径（生产行为不变，注入只发生在测试）。

命名模式：`<PROJECT>_<域>_ROOT` 之类前缀变量（真实例为实测项目中的 `TINYNAS_SYSINFO_ROOT` / `TINYNAS_SHARE_ROOT` / `TINYNAS_MACHINE_ID` 覆盖）。真实例位置（编写时实例，仅作模式溯源，不构成通用包产物）：`<PROJECT-overlay>/tests/`（`run-lint.sh` = 静态门禁总入口；`test-machine-id.sh` = fixture 注入 + 独立期望值行为测试）。

## 2. 测试脚本骨架

```sh
#!/bin/sh
# 行为测试：fixture 注入 + 独立生成的期望值断言
HERE=$(cd "$(dirname "$0")" && pwd)
export MYAPP_SYSINFO_ROOT="$HERE/fixtures/sysinfo"     # 注入假数据源
OUT=$("$HERE/../usr/bin/myapp-tool" --display)
# 期望值独立生成（注明日期+算法），不复制被测实现
[ "$OUT" = "EXPECTED-16-HEX" ] || { echo "FAIL display=$OUT"; exit 1; }
echo "PASS"
```

要点：

1. **golden 期望值独立生成**（手算/独立实现/记录生成日期与算法），不从被测代码抄——否则测试只是复读实现。
2. **负向用例必配**：路径穿越（`path=/../etc` 必须得到 forbidden 类拒绝）、坏输入、空 fixture——真实例即含穿越防护断言。
3. **格式断言 + 精确断言并用**：先验输出形态（正则），再验关键精确值。
4. **静态门禁并列**：`sh -n` 全量语法、uci-defaults 末行 `exit 0`、禁手放 `/etc/rc.d/`、CGI 禁 `eval`、无私钥入库——一个入口全绿退出 0（模式见真实例 run-lint.sh）。
5. fixture 一律显式构造的假数据（假 MAC/假序列号），**禁止真实凭据/密钥入 fixtures**。

## 3. ESP32 固件逻辑层（无板先证逻辑）

1. **HAL 抽象自 mock**：把业务逻辑编成宿主可编译单元（不含 esp 头文件的核心模块），外设访问收敛到接口；测试注入自写 mock 断言调用序列与返回处理。断言范围=逻辑与错误处理，**不含外设时序**。
2. **mock 组件（运行时核验）**：社区存在 esp-idf mock 类组件——在组件注册表（components.espressif.com）以 "mock" 检索；**存在性与维护状态需运行时核验**，确认可用才引入，否则走自 mock，不臆测其 API。
3. 汇报口径：宿主测试全绿 = 逻辑层证据；标注"未覆盖外设与时序"，上板验收 → `fw-hil-testing`。

## 4. 证据分层（汇报必带）

| 层 | 工具 | 能宣称 | 标注 |
|---|---|---|---|
| L0 宿主单测 | 本模式 | 业务逻辑/错误处理正确 | Host Test Only |
| L1 系统级 boot 冒烟 | QEMU（见 qemu-openwrt.md） | 镜像可引导、用户态活着 | Build/Boot Verification Only |
| L2 真机 HIL | `fw-hil-testing` | 硬件可用/外设行为/性能 | 真机证据 |

任何跨层宣称（拿 L0/L1 结论说 L2 的事）都是越级，拒绝。

> 真实例溯源：`tiny-nas/tinynas-openwrt-imagebuilder`（GitHub 公开仓）`common/tinynas-files/tests/` —— `run-lint.sh`（静态门禁总入口）与 `test-machine-id.sh`（fixture 注入 + 独立期望值行为测试）。
