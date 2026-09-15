# `build.zig.zon` Workflows

Offline examples for package metadata, dependencies, and project structure in Zig 0.16.

## 1. Minimal executable package

Recommended layout:

```text
my-app/
├── build.zig
├── build.zig.zon
└── src/
    └── main.zig
```

### `build.zig.zon`
```zig
.{
    .name = "my-app",
    .version = "0.1.0",
    .minimum_zig_version = "0.16.0",
    .dependencies = .{},
    .paths = .{
        "build.zig",
        "build.zig.zon",
        "src",
    },
}
```

## 2. Executable with dependency

When adding a dependency, Zig prints the content hash the first time a build fails to resolve it. Paste that hash into `build.zig.zon`.

### `build.zig.zon`
```zig
.{
    .name = "http-demo",
    .version = "0.1.0",
    .minimum_zig_version = "0.16.0",
    .dependencies = .{
        .known_folders = .{
            .url = "git+https://github.com/ziglibs/known-folders#main",
            .hash = "known after first resolve attempt",
        },
    },
    .paths = .{
        "build.zig",
        "build.zig.zon",
        "src",
    },
}
```

### `build.zig`
```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const known_folders_dep = b.dependency("known_folders", .{
        .target = target,
        .optimize = optimize,
    });

    const exe = b.addExecutable(.{
        .name = "http-demo",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/main.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });

    exe.root_module.addImport(
        "known-folders",
        known_folders_dep.module("known-folders"),
    );

    b.installArtifact(exe);
}
```

## 3. Library-first package

For a reusable library, prefer `src/root.zig` as the public entry:

```text
my-lib/
├── build.zig
├── build.zig.zon
└── src/
    ├── root.zig
    └── parser.zig
```

### `src/root.zig`
```zig
pub const Parser = @import("parser.zig").Parser;
pub const parse = @import("parser.zig").parse;
```

### `build.zig`
```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const lib = b.addLibrary(.{
        .name = "my-lib",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/root.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });

    b.installArtifact(lib);
}
```

## 4. Common package rules

- Use `src/main.zig` for executables.
- Use `src/root.zig` for libraries.
- Keep `paths` explicit so package exports are predictable.
- Put external packages in `build.zig.zon`; wire them into modules in `build.zig`.
- Use `zig build --help` after changing build steps or options.
