# Version Pinning — 三版本轴与各平台锚定手段

> 目标：任何一台机器、CI 或新同事，按仓库里的锚定文件构建，产出与团队一致的产物。

## 1. 三版本轴（每条链路都适用）

| 轴 | 含义 | 确认方式 | 用途 |
|---|---|---|---|
| 本机轴 | 当前机器实际装了什么 | Preflight 实测命令 | 判断"这台机器现在能干什么" |
| 项目锁定轴 | 仓库锚定文件钉住的版本 | 锚定文件内容（§2） | **唯一构建依据** |
| 上游 latest 轴 | 官方当前最新 | 官方 release 页，引用必须带"截至 2026-09-02" | 升级评估，不自动采用 |

排障第一步永远是"三轴对表"：漂移的是哪根轴，就把哪根轴拉回项目锁定轴。

## 2. 各平台锚定手段

### ESP-IDF 链

- **`dependencies.lock`**（高置信，基线 §9）：组件管理器解析后生成，随仓库提交；损坏可用 `idf.py reconfigure` 恢复；`managed_components/` 勿手改。
- **固定 IDF 检出版本**（tag/commit）：CI 与文档写明；可复现构建 = 固定 IDF 检出 + 提交 `dependencies.lock`。
- 项目里如采用 `IDF_VERSION` 之类的锚定文件/变量约定钉 IDF 版本：以**项目仓库实际文件**为准（各项目约定不同——运行时核验），不要假设通用存在。

### OpenWrt 链

- **固定版本 IB tarball**：版本 pin 到具体号（基线 25.12.5，走读 2026-09-02），从官方下载站取 `.tar.zst`（旧版 `.tar.xz`），按版本目录缓存复用（获取命令模式见 `openwrt-image-build` Workflow 1）。
- **`SOURCE_DATE_EPOCH`**：固定时间戳变量参与构建，消除打包时间漂移——可复现构建语义详见 `openwrt-image-build/references/reproducible-build.md`。

### Rust / musl 链

- **`rust-toolchain.toml`**：钉 channel 与组件，随仓库提交；`rustup` 按它自动对齐本机轴。
- **固定 target**：`rustup target add <target>` 后把 target 列入文档与 CI；自定义 target JSON（如使用）入库并纳入评审——它就是"目标机器定义"，改动等同改 ABI。

## 3. 命令清单（对表用）

```bash
# 本机轴实测
rustc --version --verbose 2>/dev/null; rustup target list --installed 2>/dev/null
aarch64-linux-gnu-gcc --version 2>/dev/null | head -1
idf.py --version 2>/dev/null
ls "openwrt-imagebuilder-${VER}" 2>/dev/null          # IB 按版本缓存目录

# 项目锁定轴核对
cat rust-toolchain.toml 2>/dev/null
cat dependencies.lock 2>/dev/null | head -10
grep -r "SOURCE_DATE_EPOCH" build*.sh Makefile 2>/dev/null

# 产物可比对性
sha256sum <artifact> ; file <artifact>
```

## 4. 纪律

1. 锚定文件**必须入库**，改动走评审——它们是"构建 API"。
2. 升级评估（latest 轴）产出的是"升级建议 + 基线日期"，不是直接改锁定轴。
3. 任何"最新版本"表述必须带日期（截至 2026-09-02）并提示运行时核验。
4. 团队抽检：两台机器按锚定文件构建，sha256 应一致；不一致按本文件逐轴排查。
