# `comptime` Patterns

Offline examples for common Zig 0.16 comptime workflows.

## 1. Generic printer with `anytype`

```zig
const std = @import("std");

pub fn printTypeName(value: anytype) void {
    const T = @TypeOf(value);
    std.debug.print("type = {s}\n", .{@typeName(T)});
}
```

## 2. Reflect over struct fields

```zig
const std = @import("std");

fn dumpFields(comptime T: type) void {
    const info = @typeInfo(T);
    switch (info) {
        .@"struct" => |s| inline for (s.fields) |field| {
            std.debug.print("{s}: {s}\n", .{
                field.name,
                @typeName(field.type),
            });
        },
        else => @compileError("expected a struct type"),
    }
}

test "dump fields compiles" {
    const User = struct {
        id: u64,
        name: []const u8,
    };
    dumpFields(User);
}
```

## 3. Generate a specialized type

```zig
fn Pair(comptime A: type, comptime B: type) type {
    return struct {
        first: A,
        second: B,
    };
}

test "pair type" {
    const IntStr = Pair(u32, []const u8);
    const v: IntStr = .{ .first = 1, .second = "ok" };
    _ = v;
}
```

## 4. Build enum lookup table at comptime

```zig
const std = @import("std");

const Token = enum {
    identifier,
    integer,
    eof,
};

const token_names = comptime blk: {
    var table: [@typeInfo(Token).@"enum".fields.len][]const u8 = undefined;
    inline for (@typeInfo(Token).@"enum".fields, 0..) |field, i| {
        table[i] = field.name;
    }
    break :blk table;
};

test "enum table" {
    try std.testing.expectEqualStrings("identifier", token_names[0]);
}
```

## 5. Inline loop for repetitive code generation

```zig
const std = @import("std");

fn sumTuple(tuple: anytype) u64 {
    var total: u64 = 0;
    inline for (tuple) |value| {
        total += value;
    }
    return total;
}

test "sum tuple" {
    try std.testing.expectEqual(@as(u64, 6), sumTuple(.{ 1, 2, 3 }));
}
```

## 6. Compile-time validation

```zig
fn requirePowerOfTwo(comptime n: usize) void {
    if (n == 0 or (n & (n - 1)) != 0) {
        @compileError("value must be a power of two");
    }
}

comptime {
    requirePowerOfTwo(64);
}
```

## 7. Practical guidance

- Prefer `comptime T: type` when generating type-specialized APIs.
- Use `inline for` when the loop body must be unrolled at compile time.
- Use `@typeInfo` for reflection-driven helpers.
- Use `@compileError` for strong developer feedback.
- Keep comptime helpers simple; move runtime work out unless zero-cost specialization is needed.
