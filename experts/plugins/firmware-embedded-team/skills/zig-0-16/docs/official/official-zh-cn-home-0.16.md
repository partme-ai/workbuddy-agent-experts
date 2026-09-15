# Zig 中文主页（0.16.0）提炼

来源：https://ziglang.org/zh-CN/

## 官方定位

Zig 是一种通用的编程语言和工具链，用于维护健壮、高效、可重用的软件。

相关入口：

- 立即开始：https://ziglang.org/zh-CN/learn/getting-started/
- 文档：https://ziglang.org/documentation/0.16.0/
- 变化（release notes）：https://ziglang.org/download/0.16.0/release-notes.html

## 三个核心卖点（主页原文结构）

### 1) 一种简单的语言

- 没有隐式控制流
- 没有隐式内存分配
- 没有预处理器，没有宏

### 2) 编译期代码执行

- 编译期调用任意函数
- 在没有运行时开销的情况下，将类型作为值进行操作
- 编译期模拟目标架构

### 3) 用 Zig 维护代码（语言 + 工具链）

- Zig 作为零依赖、开箱即用交叉编译的 C/C++ 编译器
- 利用 `zig build` 在所有平台上创建一致的开发环境
- 在 C/C++ 项目中添加 Zig 编译单元，跨语言 LTO 默认启用

## 主页示例（index.zig）

这个示例强调：

- `test` 是一等公民
- 使用 `std.testing.allocator` 做测试分配器
- 容器用 `.empty` 初始化
- 用 `defer` 确保释放

```zig
const std = @import("std");
const parseInt = std.fmt.parseInt;

test "parse integers" {
    const input = "123 67 89,99";
    const gpa = std.testing.allocator;

    var list: std.ArrayList(u32) = .empty;
    defer list.deinit(gpa);

    var it = std.mem.tokenizeAny(u8, input, " ,");
    while (it.next()) |num| {
        const n = try parseInt(u32, num, 10);
        try list.append(gpa, n);
    }

    const expected = [_]u32{ 123, 67, 89, 99 };
    for (expected, list.items) |exp, actual| {
        try std.testing.expectEqual(exp, actual);
    }
}
```

运行方式（主页示例）：

```bash
zig test index.zig
```

## 社区与基金会（主页信息提炼）

- Zig 社区是去中心化的：没有“官方/非官方”概念，每个社区空间都有自己的版主和规则。
- Zig 源码仓库（主页链接）：https://codeberg.org/ziglang/zig
- 贡献者行为准则（主页链接）：https://github.com/ziglang/zig/blob/master/.github/CODE_OF_CONDUCT.md
- Zig 软件基金会（ZSF）：501(c)(3) 非营利组织，旨在支持语言发展（主页：/zh-CN/zsf/）。

## 对标本仓库 references

- 语言与语义：`../../references/language.md`
- 测试：`../../references/std-testing.md`
- 内存与容器：`../../references/std-allocators.md`、`../../references/std-arraylist.md`、`../../references/std-mem.md`
- 格式化与解析：`../../references/std-fmt.md`
