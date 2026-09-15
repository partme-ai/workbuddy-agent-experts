# std.dynamic_library

Cross-platform dynamic library loading (dlopen/LoadLibrary). Works on Linux, macOS, Windows, and BSD.

## Quick Reference

```zig
const std = @import("std");
const DynLib = std.DynLib;
```

## Main API

### Open and Close

```zig
// Open a dynamic library (path must be null-terminated)
const lib = try DynLib.open("/usr/lib/libfoo.so");
// or with an explicit null-terminated path:
const lib = try DynLib.openZ("/usr/lib/libfoo.so\0");
// Must close when done
defer lib.close();
```

### Lookup Symbols

```zig
// Look up a function by name
const func = lib.lookup(*const fn (i32) i32, "my_function") orelse {
    std.debug.print("symbol not found\n", .{});
    return;
};
const result = func(42);

// Look up a global variable
const global = lib.lookup(*i32, "my_global") orelse return;
_ = global.*;
```

## Platform-Specific

### POSIX (dlopen)

```zig
const lib = try std.DynLib.DlDynLib.open("libm.so.6");
defer lib.close();
const sin_func = lib.lookup(*const fn (f64) f64, "sin") orelse return;
_ = sin_func(1.0);

// Error diagnostics
const err = std.DynLib.DlDynLib.getError();
if (err) |msg| std.debug.print("dl error: {s}\n", .{msg});
```

### Windows (LoadLibrary)

```zig
const lib = try std.DynLib.WindowsDynLib.open("user32.dll");
defer lib.close();
const msg_box = lib.lookup(*const fn (usize, [*:0]const u8, [*:0]const u8, u32) i32, "MessageBoxA") orelse return;

// With custom flags
const lib = try std.DynLib.WindowsDynLib.openEx("mylib.dll", .{ .load_with_altered_search_path = true });
```

## Error Handling

```zig
const lib = DynLib.open("missing.so") catch |err| switch (err) {
    error.FileNotFound => {
        std.debug.print("Library not found\n", .{});
        return;
    },
    error.InvalidExe => {
        std.debug.print("Not a valid dynamic library\n", .{});
        return;
    },
    error.IsDir => {
        std.debug.print("Path is a directory\n", .{});
        return;
    },
    error.UnknownUnknown => {
        std.debug.print("Unknown error\n", .{});
        return;
    },
    else => |e| return e,
};
defer lib.close();
```

## Internal Use (ElfDynLib)

```zig
// Access the program's own dynamic section
const dyn = std.DynLib.get_DYNAMIC();

// Iterate loaded libraries (Linux)
var it = try std.DynLib.linkmap_iterator();
while (it.next()) |entry| {
    std.debug.print("Loaded: {s}\n", .{entry.name});
}
```

## Gotchas

1. **Path must be a valid shared library** — format differs by platform (.so, .dylib, .dll).
2. **`lookup` returns `?T`** — returns `null` if the symbol is not found.
3. **Cross-platform prefer `DynLib`** — use the `DynLib` top-level struct for portable code; platform-specific variants (`ElfDynLib`, `WindowsDynLib`, `DlDynLib`) for platform-specific features.
4. **Warning: trust the file** — the API docs explicitly warn "Malicious file will be able to execute arbitrary code."
5. **`openZ` for null-terminated paths** — use `openZ` if your path is already `[:0]` terminated (avoids an extra allocation).
