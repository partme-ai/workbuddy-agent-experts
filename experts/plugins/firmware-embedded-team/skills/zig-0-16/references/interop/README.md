# interop/ — 构建系统与 C 互操作

Zig 0.16.0 构建系统（`build.zig` / `build.zig.zon`）与 C 互操作深入参考。

| 文件 | 内容 |
|------|------|
| `../std-build.md` | `std.Build` 完整 API 与模式 |
| `../build-mode.md` | Debug / ReleaseSafe / ReleaseFast / ReleaseSmall |
| `../c-interop.md` | C 语言互操作（@cImport、build.zig 里 linkLibC） |

> 历史原因：原计划用 `build/` 目录名，但 zig-skills 的 .gitignore 排除 `build/`（Java/Maven 约定），改为 `interop/`。文件路径不变。
