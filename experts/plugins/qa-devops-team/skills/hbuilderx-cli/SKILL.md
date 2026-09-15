---
name: hbuilderx-cli
license: Apache-2.0
description: HBuilderX CLI 命令行工具技能。当用户需要通过命令行启动 uni-app 开发环境、查看运行日志、运行自动化测试、配置 HBuilderX CLI 环境，或在 npm scripts 中集成 HBuilderX 工作流时使用。覆盖 Web、Android、iOS、HarmonyOS、小程序等多平台开发。
---

# HBuilderX CLI Reference

本技能覆盖 HBuilderX CLI 命令行工具（`@dcloudio/hbuilderx-cli`）。当用户需要通过命令行启动 uni-app 开发环境、查看平台日志、运行自动化测试或配置 HBuilderX CLI 时使用本技能。

HBuilderX CLI 是 DCloud 官方提供的命令行工具包装器，让开发者可以通过 npm scripts 或终端命令直接使用 HBuilderX 的各种功能，无需手动操作 IDE。

## Capability Boundaries

### ✅ Strong Suits
1. 通过命令行启动 Web、Android、iOS、HarmonyOS、小程序等多平台开发环境
2. 实时查看各平台运行日志（logcat）
3. 运行 uni-app 自动化测试（Web/Android/iOS/HarmonyOS）
4. 在 npm scripts 和 CI/CD 流程中集成 HBuilderX 工作流
5. HBuilderX CLI 环境检测与配置（自动/手动）

### ⚠️ Requirements
1. 必须已安装 HBuilderX（CLI 会自动检测运行中的 HBuilderX 进程）
2. `uni-launch` 命令需要 HBuilderX 5.0+
3. `uni-logcat` 和 `uni-test` 命令需要 HBuilderX 4.87+
4. `uni-test` 需要先在 HBuilderX 中安装 uni-app 自动化测试插件
5. iOS 真机开发需要有效的 Apple 开发者证书

### ❌ Out of Scope（及替代方案）
1. HBuilderX IDE 本身的使用和配置 → 使用 HBuilderX 官方文档
2. uni-app 应用代码编写 → 使用对应的前端框架技能（vue3、vue2 等）
3. 原生插件开发 → 使用 HBuilderX 原生插件开发文档
4. 云端打包和发布 → 使用 uni-app 云端打包文档
5. 非 uni-app 项目的构建工具 → 使用对应的构建技能（webpack、vite 等）

## When to use this skill

当用户需要通过命令行启动 uni-app 开发、查看运行日志、运行测试、在 npm scripts 中集成 HBuilderX 工作流，或配置 HBuilderX CLI 环境时使用本技能。

**典型触发场景：**
- "怎么用命令行启动 uni-app 的 Web 开发？"
- "如何通过 npm scripts 运行 Android 模拟器？"
- "怎么查看 uni-app 的运行日志？"
- "uni-test 怎么配置？"
- "HBuilderX CLI 找不到怎么办？"

## Quick Start

**示例调用：**
```
用命令行启动 uni-app 的 Web 开发环境
配置 npm scripts 来运行 Android 和 iOS 开发
查看 Android 模拟器的运行日志
运行 uni-app 的 Web 自动化测试
解决 HBuilderX CLI 找不到的问题
```

## Workflow

Step 1. **确认环境** — 检查 HBuilderX 是否已安装并运行，确认版本满足要求

Step 2. **选择命令** — 根据需求选择 `hbuilderx`、`uni-launch`、`uni-logcat` 或 `uni-test`

Step 3. **配置平台参数** — 指定目标平台（web/app-android/app-ios/mp-weixin 等）和平台特有参数

Step 4. **执行与调试** — 运行命令，根据输出调整参数或排查问题

## Critical: Command Coverage Map

### `hbuilderx` — 通用 CLI 包装器

直接传递任意参数给 HBuilderX CLI。如果 HBuilderX 未运行，会自动启动。

```bash
# 检查版本
hbuilderx --version

# 打开项目
hbuilderx project open --path /path/to/project

# 启动 Web 开发
hbuilderx launch web --project /path/to/project

# 查看日志
hbuilderx logcat web --project /path/to/project
```

### `uni-launch` — 开发环境启动

> ⚠️ **需要 HBuilderX 5.0+**

启动各平台开发环境，自动处理项目打开和 HBuilderX 启动。

#### Web 平台
```bash
uni-launch web                          # 使用内置浏览器
uni-launch web --browser Chrome         # 指定 Chrome
uni-launch web --browser Safari         # 指定 Safari
uni-launch web --compile true           # 只编译不运行
```

#### Android 平台
```bash
uni-launch app-android                           # 默认设备
uni-launch app-android --deviceId emulator-5554  # 指定模拟器
uni-launch app-android --playground custom       # 自定义基座
uni-launch app-android --native-log true         # 显示原生日志
uni-launch app-android --continue-on-error true  # 编译错误后继续
```

#### iOS 平台
```bash
uni-launch app-ios --iosTarget device      # 真机
uni-launch app-ios --iosTarget simulator   # 模拟器
uni-launch app-ios --deviceId iPhone-15-Pro  # 指定设备
```

#### 小程序平台
```bash
uni-launch mp-weixin --runtime-log true    # 微信小程序
uni-launch mp-alipay --runtime-log true    # 支付宝小程序
uni-launch mp-toutiao --runtime-log true   # 抖音小程序
```

#### HarmonyOS 平台
```bash
uni-launch app-harmony                      # 默认设备
uni-launch app-harmony --deviceId emulator-5554  # 指定模拟器
```

### `uni-logcat` — 日志查看

> ⚠️ **需要 HBuilderX 4.87+**

查看各平台运行日志，自动处理项目打开和 HBuilderX 启动。

```bash
uni-logcat web                                    # Web 日志
uni-logcat app-android --deviceId emulator-5554   # Android 指定设备
uni-logcat app-ios --iosTarget device             # iOS 真机
uni-logcat app-ios --iosTarget simulator          # iOS 模拟器
uni-logcat mp-weixin                              # 微信小程序
```

### `uni-test` — 自动化测试

> ⚠️ **需要 HBuilderX 4.87+**
> ⚠️ **前置条件**：必须先在 HBuilderX 中安装 [uni-app 自动化测试插件](https://ext.dcloud.net.cn/plugin?id=5708)

```bash
# Web 测试（支持 Chrome/Safari/Firefox，默认 Chrome）
uni-test web --testcaseFile tests/login.test.js
uni-test web --browser Chrome --testcaseFile tests/login.test.js
uni-test web --browser Safari --testcaseFile tests/login.test.js
uni-test web --browser Firefox --testcaseFile tests/login.test.js

# Android 测试（支持真机和模拟器）
uni-test app-android --device_id emulator-5554

# iOS 测试（仅支持模拟器）
uni-test app-ios --device_id iPhone-15-Pro

# HarmonyOS 测试（支持真机和模拟器）
uni-test app-harmony --device_id emulator-5554
```

## Critical: Platform Support Matrix

| 平台 | uni-launch | uni-logcat | uni-test |
|------|:----------:|:----------:|:--------:|
| Web | ✅ | ✅ | ✅ Chrome/Safari/Firefox |
| Android | ✅ 真机+模拟器 | ✅ | ✅ 真机+模拟器 |
| iOS | ✅ 真机+模拟器 | ✅ | ⚠️ 仅模拟器 |
| HarmonyOS | ✅ 真机+模拟器 | ✅ | ✅ 真机+模拟器 |
| 微信小程序 | ✅ | ✅ | — |
| 支付宝小程序 | ✅ | ✅ | — |
| 抖音小程序 | ✅ | ✅ | — |

## Critical: Version Requirements

| 命令 | 最低 HBuilderX 版本 | 说明 |
|------|---------------------|------|
| `hbuilderx` | 任意版本 | 通用包装器，无版本限制 |
| `uni-launch` | **5.0+** | 开发环境启动命令 |
| `uni-logcat` | **4.87+** | 日志查看命令 |
| `uni-test` | **4.87+** | 自动化测试命令 |

检查 HBuilderX 版本：
```bash
cli --version
```

## Critical: Environment Configuration

### 自动检测（推荐）

HBuilderX CLI 会自动检测已启动的 HBuilderX 进程，无需额外配置。

### 手动配置

如果自动检测失败，设置 `HBUILDERX_CLI_PATH` 环境变量：

```bash
# macOS/Linux
export HBUILDERX_CLI_PATH="/Applications/HBuilderX.app/Contents/MacOS/cli"

# Windows (cmd)
set HBUILDERX_CLI_PATH="C:\Program Files\HBuilderX\cli.exe"

# Windows (PowerShell)
$env:HBUILDERX_CLI_PATH = "C:\Program Files\HBuilderX\cli.exe"
```

## Critical: npm scripts Integration

在 `package.json` 中配置常用命令：

```json
{
  "scripts": {
    "hbuilderx": "hbuilderx",
    "dev:web": "uni-launch web",
    "dev:app-android": "uni-launch app-android",
    "dev:app-ios": "uni-launch app-ios",
    "dev:mp-weixin": "uni-launch mp-weixin",
    "dev:mp-alipay": "uni-launch mp-alipay",
    "dev:mp-toutiao": "uni-launch mp-toutiao",
    "logcat:web": "uni-logcat web",
    "logcat:app-android": "uni-logcat app-android",
    "logcat:app-ios": "uni-logcat app-ios",
    "test:web": "uni-test web",
    "test:app-android": "uni-test app-android",
    "test:app-ios": "uni-test app-ios"
  }
}
```

使用 npm scripts：
```bash
npm run dev:web
npm run dev:app-android -- --deviceId emulator-5554
npm run logcat:web
npm run test:web -- --testcaseFile tests/login.test.js
```

## Installation

### 全局安装（推荐）
```bash
npm install -g @dcloudio/hbuilderx-cli
```
全局安装后可直接使用 `hbuilderx`、`uni-launch`、`uni-logcat`、`uni-test` 命令。

### 本地安装
```bash
npm install @dcloudio/hbuilderx-cli --save-dev
```
本地安装后通过 npm scripts 或 `npx` 使用。

## Quick Fixes

| 问题 | 解决方案 |
|------|----------|
| `command not found: hbuilderx` | 确认已全局安装 `npm install -g @dcloudio/hbuilderx-cli`，或检查 PATH |
| `找不到 HBuilderX` | 确保 HBuilderX 已启动，或手动设置 `HBUILDERX_CLI_PATH` 环境变量 |
| `uni-launch 命令不可用` | 升级 HBuilderX 到 5.0+ 版本 |
| `uni-logcat/uni-test 命令不可用` | 升级 HBuilderX 到 4.87+ 版本 |
| `uni-test 找不到测试插件` | 在 HBuilderX 中安装 uni-app 自动化测试插件 |
| `iOS 真机测试失败` | iOS 仅支持模拟器测试，不支持真机 |
| `Android 设备未找到` | 检查 ADB 连接：`adb devices`，确认模拟器已启动或真机已连接 |
| `HBuilderX 版本过低` | 通过 `cli --version` 检查版本，更新到最新版 |
| `npm scripts 参数传递失败` | npm scripts 中传递参数需要加 `--`，如 `npm run dev:web -- --browser Chrome` |
| `Windows 路径问题` | Windows 下 `HBUILDERX_CLI_PATH` 使用反斜杠或双引号包裹路径 |

## Official References

- [HBuilderX CLI 官方文档](https://hx.dcloud.net.cn/cli/README)
- [npm 包页面](https://www.npmjs.com/package/@dcloudio/hbuilderx-cli)
- [GitHub 仓库](https://github.com/dcloudio/hbuilderx-cli)
- [uni-app 自动化测试插件](https://ext.dcloud.net.cn/plugin?id=5708)
- [DCloud 官方文档](https://uniapp.dcloud.net.cn/)

## Audience

| 用户类型 | 使用方式 |
|----------|----------|
| **uni-app 开发者** | 通过命令行快速启动开发环境，替代手动操作 IDE |
| **CI/CD 工程师** | 在自动化流水线中集成 uni-app 构建和测试 |
| **团队协作** | 统一团队的开发启动命令，通过 npm scripts 标准化工作流 |
| **多平台开发者** | 一个工具链管理 Web/Android/iOS/小程序等多平台开发 |

自定义选项：
- 指定目标平台（web/app-android/app-ios/mp-weixin 等）
- 指定设备（deviceId/iosTarget）
- 指定浏览器（Chrome/Safari/Firefox）
- 配置日志级别和输出

## Gotchas

1. **必须先启动 HBuilderX** — CLI 依赖 HBuilderX 进程，确保 HBuilderX 已运行或设置 `HBUILDERX_CLI_PATH`
2. **版本要求不统一** — `uni-launch` 需要 5.0+，`uni-logcat` 和 `uni-test` 需要 4.87+，使用前确认版本
3. **iOS 测试仅支持模拟器** — `uni-test app-ios` 不支持真机，这是平台限制而非工具限制
4. **测试插件必须预装** — `uni-test` 需要先在 HBuilderX 中安装自动化测试插件，否则命令会失败
5. **npm scripts 参数传递** — 通过 `npm run` 传递 CLI 参数必须加 `--` 分隔符
6. **自动检测不可靠时手动配置** — 某些环境下自动检测可能失败（如多实例、非标准安装），此时必须设置 `HBUILDERX_CLI_PATH`
7. **Windows 路径注意转义** — Windows 下环境变量路径包含空格时需要用双引号包裹

## FAQ

**Q: `hbuilderx` 和 `uni-launch` 有什么区别？**
A: `hbuilderx` 是通用包装器，直接透传参数给 HBuilderX CLI；`uni-launch` 是专门的开发启动命令，自动处理项目打开和 HBuilderX 启动，且需要 HBuilderX 5.0+。推荐使用 `uni-launch` 进行日常开发。

**Q: 如何在 CI/CD 中使用？**
A: 全局安装 `@dcloudio/hbuilderx-cli`，确保 HBuilderX 已安装并在 PATH 中，设置 `HBUILDERX_CLI_PATH` 环境变量，然后在流水线脚本中调用 `uni-launch` 或 `uni-test`。

**Q: 支持哪些小程序平台？**
A: 支持微信小程序（mp-weixin）、支付宝小程序（mp-alipay）、抖音小程序（mp-toutiao）等主流小程序平台。

**Q: 如何查看特定设备的日志？**
A: 使用 `--deviceId` 参数指定设备，如 `uni-logcat app-android --deviceId emulator-5554`。iOS 使用 `--iosTarget` 参数区分真机和模拟器。

**Q: 可以同时运行多个平台的开发环境吗？**
A: 可以，每个平台命令独立运行。在不同的终端窗口中分别执行对应的 `uni-launch` 命令即可。

**Q: Windows 下如何设置环境变量？**
A: cmd 使用 `set HBUILDERX_CLI_PATH="C:\Program Files\HBuilderX\cli.exe"`，PowerShell 使用 `$env:HBUILDERX_CLI_PATH = "C:\Program Files\HBuilderX\cli.exe"`。建议将设置添加到系统环境变量中持久化。
