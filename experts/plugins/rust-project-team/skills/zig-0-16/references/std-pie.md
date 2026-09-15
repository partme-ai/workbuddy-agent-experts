# std.pie

Position-Independent Executable relocation support.

## Quick Reference

```zig
const std = @import("std");
const pie = std.pie;
```

## Public API

### `relocate`

```zig
pub fn relocate() void
```

Processes PIE (Position-Independent Executable) relocations at program startup.

## How It Works

When a PIE binary is loaded, the kernel places it at a random base address. The `relocate()` function:

1. Reads the dynamic section to find the `DT_RELA` / `DT_REL` entries
2. Applies relative relocations (`R_*_RELATIVE`) to adjust absolute addresses
3. Makes the binary functional at its loaded address

This is called by `std.start` before `main()` is invoked.

```
Loader maps binary at random address
  → std.pie.relocate() fixes up absolute addresses
    → std.start.callMain() runs the program
```

## Gotchas

1. **Not user-facing** — `std.pie.relocate()` is called automatically by the startup code. Never call it directly.
2. **Only for PIE executables** — non-PIE executables have fixed base addresses and don't need relocation.
3. **Requires dynamic linking info** — relocations are stored in `.rela.dyn` / `.rel.plt` sections.
4. **Platform-specific** — used on ELF platforms (Linux, BSD) that support ASLR for executables.
5. **Must be called early** — before any code that uses absolute addresses (global variables with pointers, vtables, etc.).
