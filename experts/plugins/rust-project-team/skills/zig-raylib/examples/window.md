# raylib 示例

## 窗口初始化
```zig
const rl = @import("raylib");

pub fn main() !void {
    rl.initWindow(800, 600, "Hello raylib");
    defer rl.closeWindow();

    while (!rl.windowShouldClose()) {
        rl.beginDrawing();
        defer rl.endDrawing();
        rl.clearBackground(rl.Color.white);
        rl.drawFPS(10, 10);
    }
}
```
