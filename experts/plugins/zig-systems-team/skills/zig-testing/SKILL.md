---
name: zig-testing
license: Apache-2.0
description: Zig 测试与调试技能。涉及 std.testing 的断言、测试组织、内存泄漏检测、以及 std.debug 的日志、堆栈回溯。在需要编写测试、调试代码、诊断问题时调用。
---

# Zig 测试与调试

> 基于 std.testing 和 std.debug 的质量保障工具（Zig 0.16.0）。

## Capability Boundaries

### ✅ 强项
1. 单元测试编写与断言
2. 测试组织（test 声明、doctest、测试过滤器）
3. 内存泄漏检测
4. 日志输出（std.log）
5. 调试工具（panic、断言、堆栈回溯、hex dump）

### ⚠️ 前置要求
1. 确认 Zig 版本（`zig version`）

### ❌ 不适用范围
1. 构建系统测试配置 → 使用 `zig-build-system` 技能
2. 集成测试框架 → 使用 `zig-0.16` 技能
3. 性能基准测试 → 暂不涉及（Zig 尚未内置 benchmark）

## 何时使用

- "帮我写单元测试"
- "调试这个函数的输出"
- "检查内存泄漏"

## Data Privacy

本技能不收集、存储或传输任何用户数据。

## Workflow — 测试

步骤 1. **声明测试** — `test "name" { ... }`
步骤 2. **使用断言** — `expect`, `expectEqual`, `expectEqualStrings`
步骤 3. **运行测试** — `zig test src/main.zig` 或 `zig build test`
步骤 4. **检查结果** — 通过/失败/泄漏

## 断言速查

| 断言 | 用途 |
|------|------|
| `expect(bool)` | 条件为真 |
| `expectEqual(expected, actual)` | 浅相等（peer type） |
| `expectEqualDeep(expected, actual)` | 深相等（递归比较） |
| `expectEqualStrings(expected, actual)` | 字符串相等（带 diff） |
| `expectEqualSlices(T, expected, actual)` | 切片相等 |
| `expectError(error, result)` | 返回特定错误 |
| `expectApproxEqAbs(expected, actual, eps)` | 浮点近似（绝对误差） |
| `expectApproxEqRel(expected, actual, eps)` | 浮点近似（相对误差） |
| `expectFmt(expected, template, args)` | 格式化输出匹配 |
| `expectStringStartsWith(actual, prefix)` | 字符串前缀 |
| `expectStringEndsWith(actual, suffix)` | 字符串后缀 |

## 基本断言

```zig
test "basic assertions" {
    try std.testing.expect(true);

    try std.testing.expectEqual(@as(u32, 42), @as(u32, 42));

    try std.testing.expectEqualStrings("hello", "hello");

    try std.testing.expectEqualSlices(u8, &[_]u8{ 1, 2 }, &[_]u8{ 1, 2 });

    try std.testing.expectEqualDeep(
        struct{ x: i32, y: i32 }{ .x = 1, .y = 2 },
        struct{ x: i32, y: i32 }{ .x = 1, .y = 2 },
    );
}
```

### 浮点比较
```zig
test "float comparison" {
    try std.testing.expectApproxEqAbs(@as(f32, 1.0), 1.0001, 0.001);
    try std.testing.expectApproxEqRel(@as(f64, 100.0), 99.5, 0.01);
}
```

### 错误检查
```zig
test "error handling" {
    const result: anyerror!i32 = error.SomeError;
    try std.testing.expectError(error.SomeError, result);
}
```

## 测试组织

### 内联测试
```zig
const std = @import("std");
const expect = std.testing.expect;

test "inline test" {
    try expect(1 + 1 == 2);
}
```

### doctest（文档中的测试）
```zig
/// Adds two numbers.
///
/// ```
/// const result = add(2, 3);
/// try std.testing.expectEqual(@as(i32, 5), result);
/// ```
fn add(a: i32, b: i32) i32 {
    return a + b;
}
```

### 测试过滤器
```bash
# 运行名称包含 "http" 的测试
zig test src/main.zig --test-filter "http"

# 在 build.zig 中过滤
const tests = b.addTest(.{
    .root_module = mod,
    .filters = &.{"specific_test"},
});
```

### 测试模块
```zig
// 在文件末尾使用 test 块
test "module tests" {
    // 引用当前模块
    _ = @import("main.zig");
    // 或者单独引用测试文件
    _ = @import("tests/tests.zig");
}
```

## 内存泄漏检测

### 使用 DebugAllocator
```zig
test "memory leak detection" {
    var gpa: std.heap.DebugAllocator(.{}) = .init;
    defer {
        const leaked = gpa.deinit();
        // leaked 为 true 表示有泄漏
        if (leaked) @panic("Memory leak detected!");
    }
    const allocator = gpa.allocator();

    const buf = try allocator.alloc(u8, 100);
    // ⚠️ 忘记 allocator.free(buf) 会导致泄漏
    // defer allocator.free(buf);
}
```

### 使用 testing.allocator
```zig
test "use testing allocator" {
    const allocator = std.testing.allocator;
    // testing.allocator 会自动检测泄漏
    const buf = try allocator.alloc(u8, 10);
    defer allocator.free(buf); // 不 free 会报告泄漏
}
```

### 检测日志
```
# 测试失败时输出泄漏信息
zig test src/main.zig
# Memory leak detected: 1 allocations remaining (100 bytes)
```

## 日志与调试

### 等级化日志
```zig
std.log.debug("debug message: {}", .{value});    // 编译时可用
std.log.info("info: {}", .{value});              // 默认显示
std.log.warn("warning: {}", .{value});           // 重要警告
std.log.err("error: {}", .{value});              // 错误
```

### 自定义日志作用域
```zig
const log = std.log.scoped(.http_client);
log.info("request to {s}", .{url});
// 输出: [http_client] request to https://example.com
```

### 运行时日志级别
```bash
# 设置日志级别（默认 .info）
zig build -Dlog-level=debug
# 或按作用域过滤
zig build -Dlog-scope-override=http_client=debug
```

### panic 和断言
```zig
// 调试断言（仅在安全模式下检查）
std.debug.assert(x > 0);

// 不可达（标记不可能执行的代码路径）
unreachable;

// 主动 panic
@panic("something went wrong");
```

### 堆栈回溯
```zig
// 在 panic 或断言失败时自动打印堆栈
// 手动打印：
std.debug.dumpCurrentStackTrace(null);
```

### Hex Dump
```zig
const bytes = [_]u8{ 0x48, 0x65, 0x6C, 0x6C, 0x6F };
std.debug.hexDump("data", &bytes);
// 输出:
// data:
// 00000000: 48 65 6C 6C 6F                                Hello
```

## 测试配置（build.zig）

### 标准测试步骤
```zig
const tests = b.addTest(.{
    .root_module = b.createModule(.{
        .root_source_file = b.path("src/main.zig"),
        .target = target,
        .optimize = optimize,
    }),
});

const run_tests = b.addRunArtifact(tests);
const test_step = b.step("test", "运行单元测试");
test_step.dependOn(&run_tests.step);
```

### 多模块测试聚合
```zig
const test_step = b.step("test", "运行所有测试");
for ([_]*std.Build.Module{ mod_a, mod_b, mod_c }) |mod| {
    const t = b.addTest(.{ .root_module = mod });
    test_step.dependOn(&b.addRunArtifact(t).step);
}
```

## Gotchas

1. **`expectEqual` 使用 peer type** — 两参数必须显式类型一致，推荐 `expectEqual(@as(u32, 42), value)`
2. **`testing.allocator` 只用于测试** — 它自动检测泄漏，但性能较差，生产环境用 `DebugAllocator`
3. **test 声明不能嵌套** — `test "..." { test "..." {} }` 不合法
4. **doctest 只验证不输出** — 文档中的代码块默认被测试，但如果 panic 不会显示详细信息
5. **`std.log.debug` 默认不显示** — 需要在构建时启用 `-Dlog-level=debug`

## FAQ

**Q：如何只运行特定的测试？**
A：命令行 `zig test src/main.zig --test-filter "http"`，或通过 build.zig 的 `filters` 选项。

**Q：测试依赖的初始化代码怎么写？**
A：在 `test` 块内部初始化，或创建一个全局的测试辅助函数 `fn testUtil() !void`。

**Q：Zig 有基准测试吗？**
A：Zig 标准库尚未内置 benchmark 工具。可以在测试中手动计时：`const start = std.time.Timer.start()?`。
