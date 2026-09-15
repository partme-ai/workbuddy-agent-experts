---
name: zig-json
license: Apache-2.0
description: Zig JSON 处理技能。涉及 std.json 和 std.zon 的解析、序列化、自定义序列化、流式处理。在需要处理 JSON/ZON 数据时调用。
---

# Zig JSON 处理

> 基于 std.json 和 std.zon 的数据序列化（Zig 0.16.0）。

## Capability Boundaries

### ✅ 强项
1. 解析 JSON 到 Zig 结构体
2. 序列化 Zig 结构体到 JSON
3. 动态 JSON 值处理（无类型场景）
4. 自定义序列化（`jsonStringify`、`jsonParseFromValue`）
5. 流式 JSON 处理（大文件场景）
6. ZON（Zig Object Notation）解析

### ⚠️ 前置要求
1. 确认 Zig 版本（`zig version`）

### ❌ 不适用范围
1. JSON 的网络传输 → 使用 `zig-http` 技能
2. ZON 用于 build.zig.zon → 使用 `zig-build-system` 技能

## 何时使用

- "解析这个 JSON 字符串"
- "将结构体序列化为 JSON"
- "处理动态 JSON 数据"

## Data Privacy

本技能不收集、存储或传输任何用户数据。

## Workflow

步骤 1. **确定输入** — 静态类型（结构体）还是动态（Value）
步骤 2. **解析** — `parseFromSlice` 或 `parseFromSliceLeaky`
步骤 3. **使用数据** — 访问字段/遍历
步骤 4. **清理** — `parsed.deinit()` 释放内存

## 解析 JSON

### 解析到结构体（推荐）
```zig
const Config = struct {
    name: []const u8,
    port: u16,
    enabled: bool = true,
};

const json_str = \\{"name": "server", "port": 8080};

const parsed = try std.json.parseFromSlice(Config, allocator, json_str, .{});
defer parsed.deinit();

const config = parsed.value;
// config.name == "server", config.port == 8080, config.enabled == true
```

### 解析选项
```zig
const parsed = try std.json.parseFromSlice(T, allocator, json_str, .{
    .duplicate_field_behavior = .@"error", // .use_first | .use_last
    .ignore_unknown_fields = true,
    .max_value_len = 4096,
    .parse_numbers = true,
});
```

### 支持的类型映射
| Zig 类型 | JSON 值 |
|---------|---------|
| `bool` | `true`, `false` |
| `i32`, `u64` 等 | number（或字符串，可选） |
| `f32`, `f64` | number |
| `[]const u8` | string |
| `[]T` | array |
| `struct` | object |
| `?T` | value 或 null |
| `union(enum)` | 带 tag 的对象 |
| `std.json.Value` | 任意 JSON |

### 指针类型处理
```zig
const Config = struct {
    name: []const u8,           // 引用了 parsed 的内存
    tags: []const []const u8,   // 同上
};
// ⚠️ parsed.deinit() 后这些字段不可用
// 如需长期持有：allocator.dupe()

// 使用 arena 简化生命周期
var arena = std.heap.ArenaAllocator.init(allocator);
defer arena.deinit();
const parsed = try std.json.parseFromSliceLeaky(Config, arena.allocator(), json_str, .{});
// arena.deinit() 一次性释放所有内存
```

## 序列化

### 结构体 → JSON 字符串
```zig
const Config = struct {
    name: []const u8,
    port: u16,
};

const config = Config{ .name = "server", .port = 8080 };

var buf: [256]u8 = undefined;
var writer: std.Io.Writer = .fixed(&buf);
try std.json.stringify(config, .{}, &writer);
const json = writer.buffered();
// {"name":"server","port":8080}
```

### 美化输出
```zig
try std.json.stringify(config, .{ .whitespace = .indent_2 }, &writer);
// {
//   "name": "server",
//   "port": 8080
// }
```

### 省略默认值
```zig
try std.json.stringify(value, .{ .emit_null_optional_fields = false }, &writer);
```

## 动态 JSON

### 无类型解析
```zig
const raw = \\{"users":[{"name":"Alice"}],"count":1};

const root = try std.json.parseFromSlice(std.json.Value, allocator, raw, .{});
defer root.deinit();

const obj = root.value.object;
const count = obj.get("count").?.integer;
const users = obj.get("users").?.array;
for (users) |user| {
    const name = user.object.get("name").?.string;
}
```

### 构建动态 JSON
```zig
var obj = std.json.ObjectMap.init(allocator);
try obj.put("name", std.json.Value{ .string = "Alice" });
try obj.put("age", std.json.Value{ .integer = 30 });

// 序列化
var buf: [256]u8 = undefined;
var writer: std.Io.Writer = .fixed(&buf);
try std.json.stringify(std.json.Value{ .object = obj }, .{}, &writer);
```

## 自定义序列化

### 对结构体自定义
```zig
const Point = struct {
    x: i32,
    y: i32,

    pub fn jsonStringify(self: Point, jws: *std.json.WriteStream(.{})) !void {
        try jws.beginObject();
        try jws.objectField("coordinates");
        try jws.beginArray();
        try jws.write(self.x);
        try jws.write(self.y);
        try jws.endArray();
        try jws.endObject();
    }
};
```

## ZON（Zig Object Notation）

```zig
const std = @import("std");

const Config = struct {
    name: []const u8,
    version: []const u8,
};

const zon_str =
    \\.{
    \\    .name = "myapp",
    \\    .version = "0.1.0",
    \\}
;

const parsed = try std.zon.parseFromSlice(Config, allocator, zon_str, .{});
defer parsed.deinit();
// parsed.value.name == "myapp"
```

## 流式处理（大文件）

```zig
// 逐 token 扫描（避免将整个 JSON 加载到内存）
const file = try std.fs.cwd().openFile("large.json", .{});
defer file.close();

var buf_reader = std.io.bufferedReader(file.reader());
const reader = buf_reader.reader();

var scan_state = std.json.Scanner.init(allocator, reader.any());
defer scan_state.deinit();

while (true) {
    const token = scan_state.next() orelse break;
    switch (token) {
        .object_begin => {},
        .string => |s| { /* handle string */ },
        .number => |n| { /* handle number */ },
        else => {},
    }
}
```

## Gotchas

1. **`parsed.deinit()` 释放引用内存** — 解析后 `[]const u8` 字段引用的是 parsed 内部内存，deinit 后不可用
2. **使用 Arena 简化生命周期** — `parseFromSliceLeaky` 配合 `ArenaAllocator` 省去逐字段拷贝
3. **大 JSON 用流式** — `parseFromSlice` 会加载整个 JSON，超大文件使用 `Scanner` 流式处理
4. **`integer` 字段注意符号** — `std.json.Value.integer` 是 `i64`，无符号大数需额外处理
5. **ZON 与 JSON 语法不同** — ZON 使用 `.field = value` 而非 `"field": value`，且键名不能加引号

## FAQ

**Q：`parseFromSlice` 和 `parseFromSliceLeaky` 区别？**
A：前者返回 `Parsed(T)` 需要手动 `deinit()`，后者使用 arena 一次性释放，适合短期使用。

**Q：如何处理超大 JSON？**
A：用 `std.json.Scanner` 逐 token 处理，或者用流式 Reader 边读边解析。

**Q：ZON 和 JSON 什么时候用哪个？**
A：Zig 项目配置用 ZON（build.zig.zon），外部 API 通信用 JSON。
