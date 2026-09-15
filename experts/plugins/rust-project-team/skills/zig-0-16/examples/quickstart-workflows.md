# Zig 0.16 Quickstart Workflows

This file provides offline examples for the `zig-0.16` skill so it remains useful even when external docs are unavailable.

## 1. Minimal executable project

### `src/main.zig`
```zig
const std = @import("std");

pub fn main() !void {
    var buf: [1024]u8 = undefined;
    var stdout_writer = std.fs.File.stdout().writer(&buf);
    const stdout = &stdout_writer.interface;

    try stdout.print("Hello from Zig 0.16.0\n", .{});
    try stdout.flush();
}
```

### `build.zig`
```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const exe = b.addExecutable(.{
        .name = "hello-zig",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/main.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });

    b.installArtifact(exe);

    const run_cmd = b.addRunArtifact(exe);
    run_cmd.step.dependOn(b.getInstallStep());

    const run_step = b.step("run", "Run the app");
    run_step.dependOn(&run_cmd.step);
}
```

### Commands
```bash
zig build
zig build run
```

## 2. Unit test workflow

```zig
const std = @import("std");

test "parse comma separated integers" {
    const input = "123 67 89,99";
    const gpa = std.testing.allocator;

    var list: std.ArrayList(u32) = .empty;
    defer list.deinit(gpa);

    var it = std.mem.tokenizeAny(u8, input, " ,");
    while (it.next()) |num| {
        const n = try std.fmt.parseInt(u32, num, 10);
        try list.append(gpa, n);
    }

    try std.testing.expectEqual(@as(usize, 4), list.items.len);
    try std.testing.expectEqual(@as(u32, 123), list.items[0]);
    try std.testing.expectEqual(@as(u32, 99), list.items[3]);
}
```

Run it with:

```bash
zig test src/main.zig
```

## 3. JSON parse and stringify

```zig
const std = @import("std");

const Config = struct {
    host: []const u8,
    port: u16,
    debug: bool,
};

test "json config roundtrip" {
    const gpa = std.testing.allocator;
    const input =
        \\{"host":"127.0.0.1","port":8080,"debug":true}
    ;

    const parsed = try std.json.parseFromSlice(Config, gpa, input, .{});
    defer parsed.deinit();

    try std.testing.expectEqualStrings("127.0.0.1", parsed.value.host);
    try std.testing.expectEqual(@as(u16, 8080), parsed.value.port);

    var out = std.ArrayList(u8).empty;
    defer out.deinit(gpa);
    try std.json.stringify(parsed.value, .{}, out.writer(gpa));
}
```

## 4. Child process workflow

```zig
const std = @import("std");

pub fn main() !void {
    const gpa = std.heap.page_allocator;

    var child = std.process.Child.init(&.{ "zig", "version" }, gpa);
    child.stdin_behavior = .Ignore;
    child.stdout_behavior = .Pipe;
    child.stderr_behavior = .Inherit;

    try child.spawn();
    const output = try child.stdout.?.readToEndAlloc(gpa, 1024);
    defer gpa.free(output);

    _ = try child.wait();
    std.debug.print("compiler version: {s}\n", .{output});
}
```

## 5. HTTP client sketch

```zig
const std = @import("std");

pub fn main() !void {
    var gpa_state: std.heap.DebugAllocator(.{}) = .init;
    defer _ = gpa_state.deinit();
    const gpa = gpa_state.allocator();

    var client = std.http.Client{ .allocator = gpa };
    defer client.deinit();

    const uri = try std.Uri.parse("https://ziglang.org/");
    var server_header_buffer: [16 * 1024]u8 = undefined;
    var req = try client.open(.GET, uri, .{
        .server_header_buffer = &server_header_buffer,
    });
    defer req.deinit();

    try req.send();
    try req.finish();
    try req.wait();
}
```

## 6. Review checklist seeds

When reviewing Zig 0.16 code, check these first:

- Is it using `root_module` instead of legacy `root_source_file` fields?
- Is it using `std.Io` style reader or writer code instead of stale `std.io` snippets?
- Are containers initialized with `.empty` or `.init` rather than `.{}`?
- Does code pair allocation or acquisition with `defer` or `errdefer` cleanup?
- Are build imports attached through `root_module.addImport(...)`?
