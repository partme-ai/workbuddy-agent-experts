# GE · amlogic-n1-build（openwrt-amlogic-remake 黄金示例）

**徽章**：`B0 Build Verification Only`（命令文档，需 Linux root 环境验证）

## 被测物

| 文件 | 验证点 |
|---|---|
| `ge-amlogic-n1-build.md` | 完整 N1 镜像构建序列、remake 参数表、5 条关键事实（含行号）、踩坑记录 |

## 与 SKILL.md 映射

- §Workflow: 全链路步骤（rootfs 输入 → remake → rename）
- §Mandatory Contracts: "board id = s905d 不是 n1" → L52 引用
- §Mandatory Contracts: "DTB = meson-gxl-s905d-phicomm-n1.dtb" → model_database.conf L52
- §Mandatory Contracts: "eMMC 安装不自研" → L551-566 luci-app-amlogic 注入
- §Pitfalls: "-b n1 报错" → 参数说明 + 踩坑
