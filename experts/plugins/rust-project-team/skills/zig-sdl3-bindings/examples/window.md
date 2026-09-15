# SDL3 示例

## 窗口初始化
```zig
const sdl3 = @import("sdl3");

pub fn main() !void {
    try sdl3.init(.{ .video = true });
    defer sdl3.quit();

    const win = try sdl3.Window.create("Hello SDL3", 800, 600, .{ .resizable = true });
    defer win.destroy();
}
```
