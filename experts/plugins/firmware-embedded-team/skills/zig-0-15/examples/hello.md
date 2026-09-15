# Zig 0.15 示例

## Hello World
```zig
const std = @import("std");

pub fn main() !void {
    var buf: [4096]u8 = undefined;
    var stdout_writer = std.fs.File.stdout().writer(&buf);
    const stdout = &stdout_writer.interface;
    try stdout.print("Hello, Zig 0.15!\n", .{});
    try stdout.flush();
}
```

## 测试
```zig
const std = @import("std");
const testing = std.testing;

test "basic test" {
    try testing.expectEqual(42, 42);
}
```
