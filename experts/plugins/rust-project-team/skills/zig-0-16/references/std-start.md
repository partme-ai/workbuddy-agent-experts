# std.start

Program startup/runtime — Zig's internal entry point logic.

## Quick Reference

```zig
const std = @import("std");
const start = std.start;
```

## Public API

### `callMain()`

```zig
pub inline fn callMain() u8
```

Calls the root module's `main` function and returns the exit code:

```zig
// What happens internally:
// - If main returns void → exit code 0
// - If main returns !void → 0 on success, 1 on error
// - If main returns u8 → returned directly
// - If main returns noreturn → never returns
```

### `simplified_logic`

```zig
pub const simplified_logic: bool
```

`true` when the Zig backend uses simplified startup (stage2 backends that can't handle the full start logic).

### `call_wWinMain()` (Windows only)

```zig
pub fn call_wWinMain() std.os.windows.INT
```

Calls the root module's `wWinMain` function for Windows GUI applications. Handles retrieving `HINSTANCE`, `lpCmdLine`, and `nShowCmd` from the PEB (Process Environment Block).

## How It Works

The Zig startup process:

```
_start (arch-specific assembly)
  → std.start.callMain() or std.start.call_wWinMain()
    → root.main() or root.wWinMain()
  → exit with return code
```

On POSIX systems, `_start` is provided by the Zig compiler in the CRT (C Runtime). On Windows, it uses the Win32 entry point.

## Gotchas

1. **Not user-facing** — `std.start` is an internal module used by the Zig compiler's runtime. Most users should never call it directly.
2. **`callMain` handles various return types** — `void`, `!void`, `u8`, `noreturn`, and error unions are all supported.
3. **Windows GUI vs console** — `wWinMain` is used for `/subsystem:windows` builds; `main` for `/subsystem:console`.
4. **`simplified_logic` is backend-dependent** — the startup path differs between self-hosted and bootstrap backends.
