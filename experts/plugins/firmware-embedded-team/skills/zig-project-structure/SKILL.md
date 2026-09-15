---
name: zig-project-structure
license: Apache-2.0
description: Zig 项目结构全生命周期管理。创建项目骨架（exe/lib/多模块/带依赖）或检查已有项目的目录结构、文件命名、构建配置合规性，输出结构化报告。
---

# Zig 项目结构管理

> 涵盖项目**创建**（生成标准骨架）与**检查**（验证合规性）全流程。

## Capability Boundaries

### ✅ 强项
1. 生成标准 Zig 项目骨架（`build.zig` + `build.zig.zon` + `src/`）
2. 支持四种项目模板：基础 exe、基础 lib、多模块分层项目、带第三方依赖项目
3. 检查项目目录结构是否符合 Zig 官方布局
4. 验证文件命名是否符合 `TitleCase.zig` / `snake_case.zig` 规范
5. 检查 `build.zig` API 是否使用了已移除的语法（如 `root_source_file`）
6. 检查 `build.zig.zon` 字段完整性（name、version、paths、minimum_zig_version）
7. 检测非标准目录/文件命名（TigerStyle 禁止的模糊命名如 `utils/`、`misc.zig`）
8. 输出结构化合规报告（错误/警告/信息三级）

### ⚠️ 前置要求
1. 已安装 Zig 编译器（推荐 ≥ 0.16.0）
2. 创建时确认目标 Zig 版本（运行 `zig version`）
3. 检查时项目根目录需包含 `build.zig` 或 `build.zig.zon`

### ❌ 不适用范围（替代方案）
1. 不用于编写项目逻辑代码 → 使用 `zig-0.16` 技能
2. 不用于代码逻辑/风格审查 → 使用 `zig-code-review` 或 `zig-tiger-style` 技能
3. 不用于游戏/图形开发 → 使用 `zig-raylib` 或 `zig-sdl3-bindings` 技能

## 何时使用

创建场景：
- "创建一个新的 Zig 项目"
- "创建一个多模块的 Zig 库项目"
- "帮我生成标准的 build.zig 和 build.zig.zon"
- "添加一个第三方依赖到项目"

检查场景：
- "检查我的 Zig 项目结构是否规范"
- "验证我的目录组织和文件命名是否符合 Zig 标准"
- "帮我审查 build.zig 和 build.zig.zon 的配置"
- "审计我的 Zig 项目合规性"

## Data Privacy

本技能不收集、存储或传输任何用户数据。所有代码生成和检查在本地完成。

---
# 第一部分：项目生成
## Workflow

步骤 1. **确认需求** — 项目名称？exe/lib？Zig 版本？是否需要依赖？
步骤 2. **选择模板** — 根据项目类型选择对应模板
步骤 3. **生成骨架** — 输出目录结构、build.zig、build.zig.zon、入口文件

## 模板一：基础可执行项目

```text
{project-name}/
├── build.zig
├── build.zig.zon
├── src/
│   └── main.zig
├── .gitignore
└── README.md
```

### `build.zig.zon`
```zig
.{
    .name = "{project-name}",
    .version = "0.1.0",
    .minimum_zig_version = "0.16.0",
    .dependencies = .{},
    .paths = .{ "build.zig", "build.zig.zon", "src" },
}
```

### `build.zig`
```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const exe = b.addExecutable(.{
        .name = "{project-name}",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/main.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });
    b.installArtifact(exe);

    const run_cmd = b.addRunArtifact(exe);
    run_cmd.step.dependOn(b.getInstallStep());
    if (b.args) |args| run_cmd.addArgs(args);
    const run_step = b.step("run", "Run the application");
    run_step.dependOn(&run_cmd.step);
}
```

### `src/main.zig`
```zig
const std = @import("std");

pub fn main() void {
    std.debug.print("Hello from {s}!\n", .{"{project-name}"});
}

test "simple test" {
    try std.testing.expectEqual(2 + 2, 4);
}
```

## 模板二：库项目

使用 `src/root.zig` 作为公共 API 入口：

```text
{project-name}/
├── build.zig
├── build.zig.zon
├── src/
│   └── root.zig
├── .gitignore
└── README.md
```

### `build.zig`
```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const lib = b.addLibrary(.{
        .name = "{project-name}",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/root.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });
    b.installArtifact(lib);
}
```

## 模板三：大型多模块项目（生产级模式）

参考真实生产 Zig 项目（如 AgentScope-Zig，1400+ 文件）的分层架构：

```text
{project-name}/
├── build.zig                          # 单一根构建脚本
├── build.zig.zon                      # 单一根依赖
│
├── {module-core}/                     # 核心库（基础类型、消息、状态）
│   └── src/
│       ├── root.zig                   # 公共 API 入口（显式 re-export）
│       ├── agent/                     # 智能体类型
│       ├── message/                   # 消息基元
│       ├── session/                   # 会话管理
│       ├── memory/                    # 记忆管理
│       ├── model/                     # 模型适配器
│       ├── formatter/                 # 格式化器
│       ├── event/                     # 事件系统
│       ├── state/                     # 状态管理
│       ├── tool/                      # 工具定义
│       ├── skill/                     # 技能系统
│       ├── middleware/                # 中间件
│       ├── credential/                # 凭证提供者
│       ├── util/                      # 工具类
│       └── tracing/                   # 追踪系统
│
├── {module-harness}/                  # 基础设施库（依赖 core）
│   └── src/
│       ├── root.zig
│       ├── agent/filesystem/          # 文件系统抽象
│       ├── agent/middleware/          # 服务端中间件
│       ├── agent/sandbox/             # 沙箱接口
│       ├── agent/store/               # 持久化存储
│       ├── agent/subagent/            # 子智能体管理
│       ├── agent/workspace/           # 工作区管理
│       └── main/main.zig
│
├── {module-extensions}/               # 扩展插件（独立包，无 build.zig）
│   ├── {ext-database}/src/root.zig
│   ├── {ext-cache}/src/root.zig
│   └── {ext-storage}/src/root.zig
│
├── examples/{agent}/src/root.zig
├── tests/integration/{test}.zig
├── .gitignore
└── README.md
```

### 多模块 `build.zig`
```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    // 模块 1：core 库
    const core_mod = b.createModule(.{
        .root_source_file = b.path("{module-core}/src/root.zig"),
        .target = target,
        .optimize = optimize,
    });
    const core_lib = b.addLibrary(.{ .linkage = .static, .name = "core", .root_module = core_mod });
    core_lib.linkLibC();
    b.installArtifact(core_lib);

    // 模块 2：harness 库（依赖 core）
    const harness_mod = b.createModule(.{
        .root_source_file = b.path("{module-harness}/src/root.zig"),
        .target = target,
        .optimize = optimize,
    });
    harness_mod.addImport("core", core_mod);
    const harness_lib = b.addLibrary(.{ .linkage = .static, .name = "harness", .root_module = harness_mod });
    harness_lib.linkLibC();
    b.installArtifact(harness_lib);

    // 聚合测试
    const test_step = b.step("test", "运行所有单元测试");
    for ([_]*std.Build.Module{ core_mod, harness_mod }) |mod| {
        const tests = b.addTest(.{ .root_module = mod });
        tests.linkLibC();
        test_step.dependOn(&b.addRunArtifact(tests).step);
    }
}
```

### 模块入口约定（`{module-core}/src/root.zig`）

每个模块的 `root.zig` 是唯一公共 API 门面，按域分组显式 re-export：

```zig
//! {module-core} 模块入口

pub const Msg = @import("message/msg.zig");
pub const Session = @import("session/session.zig").Session;
pub const Agent = @import("agent/agent.zig").Agent;
pub const AgentBase = @import("agent/agent_base.zig").AgentBase;
pub const ModelConfig = @import("agent/config/model_config.zig").ModelConfig;
pub const JsonCodec = @import("util/json_codec.zig").JsonCodec;
```

### 多模块关键设计原则

| 原则 | 说明 |
|------|------|
| **单根 build.zig** | 不拆分子 build.zig，统一在根文件中用 `createModule` 管理 |
| **模块即目录** | 每个模块是顶层目录，拥有自己的 `src/` + `root.zig` |
| **显式 import** | `harness_mod.addImport("core", core_mod)` 而非隐式路径引用 |
| **静态库链接** | `.linkage = .static`，通过 `linkLibC()` 链接 C 库 |
| **扩展插件** | 独立目录 + 自己的 `root.zig`，不参与根构建（独立编译或运行时加载） |

## 模板四：带第三方依赖

### `build.zig.zon`
```zig
.{
    .name = "{project-name}",
    .version = "0.1.0",
    .minimum_zig_version = "0.16.0",
    .dependencies = .{
        .known_folders = .{
            .url = "https://github.com/ziglibs/known-folders/archive/refs/tags/v0.1.0.tar.gz",
            .hash = "1220...",
        },
    },
    .paths = .{ "build.zig", "build.zig.zon", "src" },
}
```

### `build.zig`（带依赖）
```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const dep = b.dependency("known_folders", .{ .target = target, .optimize = optimize });

    const exe = b.addExecutable(.{
        .name = "{project-name}",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/main.zig"),
            .target = target,
            .optimize = optimize,
            .imports = &.{
                .{ .name = "known-folders", .module = dep.module("known-folders") },
            },
        }),
    });
    b.installArtifact(exe);
}
```

---

# 第二部分：项目规范检查

## 检查 Workflow

步骤 1. **收集项目信息** — 获取目录路径，扫描文件树
步骤 2. **执行四维检查** — 目录结构 / 文件命名 / 构建配置 / 目录命名
步骤 3. **输出合规报告** — 按错误/警告/信息三级输出

## 检查一：目录结构

### 基础项目

| 检查项 | 规则 |
|--------|------|
| `build.zig` | 必需存在 |
| `build.zig.zon` | 推荐存在（0.14+ 项目应有） |
| `src/` 目录 | 必需存在 |
| `src/main.zig` | 可执行项目入口 |
| `src/root.zig` | 库项目入口约定命名 |
| `zig-out/` | 应在 `.gitignore` 中声明 |
| `.zig-cache/` | 应在 `.gitignore` 中声明 |

### 多模块项目

| 检查项 | 规则 |
|--------|------|
| 单一根 build.zig | **不应**在子模块中创建独立的 build.zig |
| 模块入口 | 每个模块目录应有 `src/root.zig` 作为公共 API |
| 模块命名 | 使用 `snake_case`（如 `agentscope-core`） |
| 模块依赖 | 在根 build.zig 中通过 `addImport` 显式声明 |
| 测试完整性 | 每个模块应有对应的 `addTest` |
| paths 覆盖 | `build.zig.zon` 的 `paths` 应包含所有模块目录 |

### `.gitignore` 检查

```
# 无前缀路径即可覆盖整个项目树
.zig-cache/
zig-out/
*.o
*.obj
*.dll
*.so
*.dylib
.DS_Store
```

## 检查二：文件命名

| 文件用途 | 命名规则 | 示例 |
|---------|---------|------|
| 类型定义 | `TitleCase.zig` | `User.zig`, `HttpResponse.zig` |
| 命名空间/模块 | `snake_case.zig` | `json.zig`, `http_client.zig` |
| exe 入口 | `main.zig` | 固定名称 |
| lib 入口 | `root.zig` | 固定名称 |

**错误命名检测：**
```
❌ user-service.zig     # 中划线不允许，应为 user_service.zig
❌ Utils.zig            # TigerStyle 禁止的模糊命名
❌ misc.zig             # 同上
❌ DataManager.zig      # "Manager" 是冗余词
```

## 检查三：构建配置

### `build.zig`

| 检查项 | 规则 |
|--------|------|
| `createModule` | **必须**使用 `root_module = b.createModule(...)`，`root_source_file` 已移除 |
| `standardTargetOptions` | 推荐使用 |
| `standardOptimizeOption` | 推荐使用 |
| `installArtifact` | 至少一个安装步骤 |
| 多模块测试 | 每个模块应有对应的 `addTest`，聚合到 `zig build test` |

```zig
// ❌ 已移除
b.addExecutable(.{ .root_source_file = b.path("src/main.zig") });

// ✅ 正确
b.addExecutable(.{ .root_module = b.createModule(.{
    .root_source_file = b.path("src/main.zig"),
})});
```

### `build.zig.zon`

| 字段 | 必需？ | 规则 |
|------|--------|------|
| `.name` | ✅ | 全小写字母、数字和连字符 |
| `.version` | ✅ 推荐 | semver 格式 `"0.1.0"` 或 `"2.0.0"` |
| `.minimum_zig_version` | ✅ 推荐 | 如 `"0.16.0"` |
| `.paths` | ✅ 推荐 | 显式声明，多模块需包含所有模块目录 |
| `.dependencies` | 可选 | 需有 `.url` 和 `.hash` |
| `.fingerprint` | 可选 | Zig 0.15+ 包指纹 |

## 检查四：目录命名

| 检查项 | 规则 |
|--------|------|
| 目录名 | `snake_case`（小写+下划线） |
| 禁止中划线 | 目录名中不允许连字符 |
| 避免模糊命名 | 避免 `utils/`、`misc/`、`helpers/`、`common/` |
| 无 Java 式路径 | 不使用 `src/main/zig/io/company/`（除非 Java 转换遗留） |

---

# 共用参考：命名规范速查

| 元素 | 规范 | 示例 |
|------|------|------|
| 类型名 | `TitleCase` | `XmlParser`, `HashMap` |
| 命名空间 | `snake_case` | `std.json`, `std.mem` |
| 函数名 | `camelCase` | `readU32Be`, `parseJson` |
| 返回类型的函数 | `TitleCase` | `ArrayList`, `HashMap` |
| 变量/常量 | `snake_case` | `const_name`, `global_var` |
| 类型文件 | `TitleCase.zig` | `ArrayList.zig` |
| 命名空间文件 | `snake_case.zig` | `mem.zig`, `json.zig` |
| 目录名 | `snake_case` | `std/`, `hash_map/` |
| 项目名 | snake-case（全小写连字符） | `my-app` |

# 合规报告模板

```text
══════════════════════════════
 项目结构合规报告
══════════════════════════════

项目: {project-name}     Zig: {version}

──────────────────────────
🔴 错误（必须修复）
──────────────────────────
1. [DIR-001] 缺少 src/ 目录
   修复: mkdir src && mv *.zig src/

2. [BUILD-001] build.zig 使用了已移除的 root_source_file
   修复: 使用 root_module = b.createModule(...)

──────────────────────────
⚠️  警告（建议修复）
──────────────────────────
1. [FILE-001] 文件名不规范: data_manager_util.zig
   建议: 若导出类型 DataManagerUtil，应命名为 DataManagerUtil.zig

2. [DIR-002] 模糊命名目录: src/utils/
   建议: 使用更具语义化的名称

──────────────────────────
ℹ️  信息（可选改进）
──────────────────────────
1. [ZON-001] build.zig.zon 缺少 minimum_zig_version
   建议: 添加 .minimum_zig_version = "0.16.0"

2. [GIT-001] 缺少 .gitignore
   建议: 添加 .gitignore 包含 zig-out/ 和 .zig-cache/

──────────────────────────
📊 汇总: 🔴 错误 2 | ⚠️ 警告 3 | ℹ️ 信息 2
══════════════════════════
```

## Gotchas

1. **`root_source_file` 已移除** — 必须使用 `root_module = b.createModule(...)`
2. **包名只允许 snake-case** — `build.zig.zon` 的 `.name` 只能是 `[a-z0-9-]` 字符
3. **paths 要显式声明** — `build.zig.zon` 的 `paths` 控制打包范围，多模块需包含所有模块
4. **入口文件放 src/** — 根目录放 `main.zig` 是非标做法
5. **`zig-out/` 无前缀即可** — 根级别的 `zig-out/` 自动覆盖所有子模块目录
6. **扩展插件不参与根构建** — 多模块项目中，非核心模块可作为独立包（含 `root.zig` 但不含 `build.zig`）
7. **仅检查 `.zig` 文件** — `README.md`、`LICENSE` 等不受命名规范约束

## FAQ

**Q：为什么不用 `zig init` 而要使用本技能的生成功能？**
A：`zig init` 只生成最简骨架。本技能提供四种模板（exe/lib/多模块/带依赖）并内置命名规范验证和 `.gitignore`。

**Q：生成的是哪个 Zig 版本？**
A：默认 Zig 0.16.0。如需 0.15.x 可在交互时指定版本。

**Q：检查是否要求运行 `zig build`？**
A：不要求。通过静态分析 `build.zig` 文本来检测已移除 API 和配置问题。

**Q：TigerStyle 禁止的命名有哪些？**
A：`Value`、`Data`、`Context`、`Manager`、`utils`、`misc` 等——因为太通用，无法传达具体语义。
