# C Interop Workflows

Offline examples for common Zig 0.16 C interoperability tasks.

## 1. Import a C header

```zig
const c = @cImport({
    @cInclude("stdio.h");
    @cInclude("string.h");
});

pub fn main() void {
    _ = c.printf("hello from C interop\n");
}
```

## 2. Build with a local C source file

### `build.zig`
```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const exe = b.addExecutable(.{
        .name = "c-mixed",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/main.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });

    exe.root_module.linkLibC();
    exe.root_module.addIncludePath(b.path("c-src"));
    exe.root_module.addCSourceFile(.{
        .file = b.path("c-src/helper.c"),
        .flags = &.{},
    });

    b.installArtifact(exe);
}
```

### `c-src/helper.h`
```c
#ifndef HELPER_H
#define HELPER_H

int add_numbers(int a, int b);

#endif
```

### `c-src/helper.c`
```c
#include "helper.h"

int add_numbers(int a, int b) {
    return a + b;
}
```

### `src/main.zig`
```zig
const c = @cImport({
    @cInclude("helper.h");
});
const std = @import("std");

pub fn main() !void {
    var buf: [256]u8 = undefined;
    var stderr_writer = std.fs.File.stderr().writer(&buf);
    const stderr = &stderr_writer.interface;

    try stderr.print("{}\n", .{c.add_numbers(2, 3)});
    try stderr.flush();
}
```

## 3. Export a Zig function to C

```zig
export fn add_numbers(a: c_int, b: c_int) c_int {
    return a + b;
}
```

## 4. Build a static library for C consumers

```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const lib = b.addStaticLibrary(.{
        .name = "mathlib",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/root.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });

    lib.root_module.linkLibC();
    b.installArtifact(lib);
}
```

## 5. Generate a simple C header manually

If the public surface is small, keep a matching header:

```c
#ifndef MATHLIB_H
#define MATHLIB_H

int add_numbers(int a, int b);

#endif
```

## 6. ABI rules to remember

- Use `export fn` for symbols meant for C callers.
- Use C-compatible parameter and return types such as `c_int`, `c_uint`, or pointer types.
- Avoid exposing Zig slices, error unions, or optionals directly across a C ABI.
- Link libc when consuming normal C code or headers that require it.
- Keep memory ownership rules explicit when passing buffers across the boundary.
