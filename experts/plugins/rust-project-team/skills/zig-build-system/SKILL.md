---
name: zig-build-system
license: Apache-2.0
description: Zig 构建系统专项技能。涉及 build.zig 和 build.zig.zon 的编写、模块管理、依赖配置、交叉编译、C/C++ 集成、自定义构建步骤和测试配置。在需要配置或调试项目构建时调用。
---

# Zig 构建系统

> 基于 std.Build 的构建脚本编写指南（Zig 0.16.0）。

## Capability Boundaries

### ✅ 强项
1. 编写 `build.zig` 构建脚本（可执行文件、库、对象文件）
2. 配置 `build.zig.zon` 包元数据与依赖管理
3. 模块创建、导入、依赖注入
4. 交叉编译与自定义目标配置
5. C/C++ 源代码集成与系统库链接
6. 构建选项、自定义构建步骤、代码生成
7. 测试配置与聚合

### ⚠️ 前置要求
1. 确认目标 Zig 版本（`zig version`）
2. 项目根目录包含 `build.zig`

### ❌ 不适用范围
1. 项目结构初始化 → 使用 `zig-project-structure` 技能
2. 项目合规检查 → 使用 `zig-project-structure` 技能
3. Zig 语言基础 → 使用 `zig-0.16` 技能

## 何时使用

- "帮我写一个 build.zig"
- "如何配置交叉编译到 wasm？"
- "如何在 build.zig 中添加 C 源文件？"
- "我想把项目拆成多模块"
- "添加一个第三方依赖"

## Data Privacy

本技能不收集、存储或传输任何用户数据。

## Workflow

步骤 1. **确认版本** — `zig version` 确认 0.16.0
步骤 2. **明确目标** — 可执行文件/库/多模块/测试？
步骤 3. **配置 build.zig.zon** — 名称、版本、依赖
步骤 4. **编写 build.zig** — 创建模块、链接、安装
步骤 5. **配置运行/测试步骤** — `zig build run` / `zig build test`
步骤 6. **验证** — `zig build` 确认编译通过

## 核心模式

### 最小可执行文件

```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const exe = b.addExecutable(.{
        .name = "myapp",
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
    const run_step = b.step("run", "运行应用");
    run_step.dependOn(&run_cmd.step);
}
```

### 多模块库

```zig
pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const core_mod = b.createModule(.{
        .root_source_file = b.path("core/src/root.zig"),
        .target = target,
        .optimize = optimize,
    });
    const harness_mod = b.createModule(.{
        .root_source_file = b.path("harness/src/root.zig"),
        .target = target,
        .optimize = optimize,
    });
    harness_mod.addImport("core", core_mod);

    const core_lib = b.addLibrary(.{ .linkage = .static, .name = "core", .root_module = core_mod });
    core_lib.linkLibC();
    b.installArtifact(core_lib);

    // 测试聚合
    const test_step = b.step("test", "运行所有测试");
    for ([_]*std.Build.Module{ core_mod, harness_mod }) |mod| {
        const tests = b.addTest(.{ .root_module = mod });
        tests.linkLibC();
        test_step.dependOn(&b.addRunArtifact(tests).step);
    }
}
```

### 静态/动态库

```zig
// 静态库（默认）
const lib = b.addLibrary(.{
    .name = "mylib",
    .linkage = .static,
    .root_module = b.createModule(.{ .root_source_file = b.path("src/root.zig"), .target = target, .optimize = optimize }),
});

// 动态库
const dylib = b.addLibrary(.{
    .name = "mylib",
    .linkage = .dynamic,
    .root_module = b.createModule(.{ .root_source_file = b.path("src/root.zig"), .target = target, .optimize = optimize }),
    .version = .{ .major = 1, .minor = 0, .patch = 0 },
});
```

## build.zig.zon 配置

### 基础
```zig
.{
    .name = "my_project",
    .version = "0.1.0",
    .minimum_zig_version = "0.16.0",
    .dependencies = .{},
    .paths = .{ "build.zig", "build.zig.zon", "src" },
}
```

### 带依赖
```zig
.{
    .name = "my_project",
    .version = "0.1.0",
    .minimum_zig_version = "0.16.0",
    .dependencies = .{
        .@"zig-network" = .{
            .url = "https://github.com/ziglibs/zig-network/archive/v1.0.0.tar.gz",
            .hash = "1220abc...",
        },
        .local_lib = .{ .path = "../local-lib" },
    },
    .paths = .{ "build.zig", "build.zig.zon", "src" },
}
```

```bash
# 获取依赖 hash
zig fetch https://github.com/user/repo/archive/v1.0.0.tar.gz
```

## 模块与依赖

### 创建内部模块
```zig
const helper_mod = b.createModule(.{
    .root_source_file = b.path("src/helper.zig"),
    .target = target,
    .optimize = optimize,
});
exe.root_module.addImport("helper", helper_mod);
```

### 使用第三方依赖
```zig
const dep = b.dependency("zig-network", .{ .target = target, .optimize = optimize });
exe.root_module.addImport("network", dep.module("zig-network"));
exe.linkLibrary(dep.artifact("net"));
```

### 懒依赖（平台选择性）
```zig
// build.zig.zon 中标记 .lazy = true
// build.zig 中：
const dawn_dep = switch (target.result.os.tag) {
    .windows => b.lazyDependency("dawn-windows", .{}),
    .linux => b.lazyDependency("dawn-linux", .{}),
    else => null,
};
if (dawn_dep) |dep| exe.addLibraryPath(dep.path("lib"));
```

## 交叉编译

### 自定义目标
```zig
const wasm_query: std.Target.Query = .{
    .cpu_arch = .wasm32,
    .os_tag = .freestanding,
};
const wasm_target = b.resolveTargetQuery(wasm_query);
```

### 主机目标（构建工具）
```zig
const tool = b.addExecutable(.{
    .name = "codegen",
    .root_module = b.createModule(.{
        .root_source_file = b.path("tools/codegen.zig"),
        .target = b.graph.host,
    }),
});
```

### 多目标构建
```zig
const targets = [_]std.Target.Query{
    .{ .cpu_arch = .x86_64, .os_tag = .linux },
    .{ .cpu_arch = .aarch64, .os_tag = .macos },
};
for (targets) |t| {
    const exe = b.addExecutable(.{
        .name = b.fmt("myapp-{s}-{s}", .{ @tagName(t.cpu_arch.?), @tagName(t.os_tag.?) }),
        .root_module = b.createModule(.{ .root_source_file = b.path("src/main.zig"), .target = b.resolveTargetQuery(t), .optimize = .ReleaseFast }),
    });
    b.installArtifact(exe);
}
```

## C/C++ 集成

```zig
// C 源文件
exe.root_module.addCSourceFiles(.{
    .root = b.path("src/c"),
    .files = &.{ "foo.c", "bar.c" },
    .flags = &.{ "-Wall", "-O2" },
});

// 头文件路径
exe.root_module.addIncludePath(b.path("include"));
exe.root_module.addSystemIncludePath(b.path("deps/include"));

// 宏定义
exe.root_module.addCMacro("DEBUG", "1");

// 系统库链接
exe.root_module.linkSystemLibrary("pthread", .{});
exe.root_module.link_libc = true;
exe.root_module.link_libcpp = true;

// 配置头文件
const config_h = b.addConfigHeader(.{ .style = .{ .cmake = b.path("config.h.in") } }, .{
    .HAVE_FEATURE = true,
    .VERSION_STRING = "1.0.0",
});
exe.addConfigHeader(config_h);
```

## 自定义构建步骤

```zig
// 字符串写入
const wf = b.addWriteFiles();
_ = wf.add("config.json", \\{ "version": "1.0" });

// 运行系统命令
const cmd = b.addSystemCommand(&.{ "git", "describe", "--tags" });
const version = cmd.captureStdOut();

// 代码生成工具
const gen_tool = b.addExecutable(.{ .name = "codegen", .root_module = b.createModule(.{ .root_source_file = b.path("tools/gen.zig"), .target = b.graph.host }) });
const gen_run = b.addRunArtifact(gen_tool);
gen_run.addFileArg(b.path("schema.json"));
const generated = gen_run.addOutputFileArg("generated.zig");
exe.root_module.addAnonymousImport("schema", .{ .root_source_file = generated });

// 格式化检查
const fmt_step = b.step("fmt", "检查格式");
fmt_step.dependOn(&b.addFmt(.{ .paths = &.{ "src/", "build.zig" }, .check = true }).step);

// 清理
const clean_step = b.step("clean", "清理产物");
clean_step.dependOn(&b.addRemoveDirTree(b.path("zig-out")).step);
```

## CLI 命令速查

```bash
zig build                    # 默认构建
zig build run                # 构建并运行
zig build test               # 运行测试
zig build --list-steps       # 列出可用步骤
zig build -Dtarget=x86_64-linux -Doptimize=ReleaseFast  # 指定目标
zig build --release=fast     # 发布构建
zig build --watch            # 文件变化自动重构建
zig build --fetch            # 拉取依赖
zig build -p /usr/local      # 自定义安装前缀
zig fetch <url>              # 获取依赖 hash
```

## Gotchas

1. **`root_source_file` 已移除** — 必须用 `root_module = b.createModule(...)`，不能直接传给 `addExecutable`
2. **模块导入用 `root_module.addImport`** — `exe.addModule()` 是旧 API，改用 `exe.root_module.addImport()`
3. **编译级方法已废弃** — `exe.addCSourceFiles()`、`exe.linkSystemLibrary()` 要改用 `exe.root_module.*` 版本
4. **`.name` 必须是 snake-case** — `build.zig.zon` 的 `.name` 只允许 `[a-z0-9-]` 字符
5. **懒依赖返回 `?*Dependency`** — `b.lazyDependency()` 返回 null 表示未拉取，构建系统会自动重试
6. **`paths` 要显式声明** — 发布包时，`paths` 决定哪些文件被打包，漏掉会导致模块不完整
7. **`b.addTest` 不再接受 `root_source_file`** — 同样需要使用 `root_module`

## FAQ

**Q：zig build 默认做什么？**
A：执行 `zig build` 会运行 `b.getInstallStep()`，即安装所有标记了 `b.installArtifact()` 的产物到 `zig-out/`。

**Q：如何为不同平台编译不同的代码？**
A：使用 `target.query` 或 `target.result.os.tag` 做条件判断，在 build.zig 中选择不同的源文件或模块。

**Q：`b.dependency` 和 `b.lazyDependency` 有什么区别？**
A：`b.dependency` 会立即拉取依赖，`b.lazyDependency` 只在被访问时才拉取。懒依赖适用于平台选择性依赖。

**Q：如何调试 build.zig 构建失败？**
A：使用 `zig build --verbose`、`zig build --verbose-link`、`zig build --verbose-cc` 逐步排查。
