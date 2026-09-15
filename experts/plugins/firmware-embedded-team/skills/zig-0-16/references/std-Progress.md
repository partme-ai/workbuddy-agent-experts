# std.Progress

Terminal progress reporting — show multi-level progress bars for long-running operations.

## Quick Start

```zig
const std = @import("std");

pub fn main() void {
    const root = std.Progress.start(.{
        .root_name = "Processing",
        .estimated_total_items = 100,
    });
    defer root.end();

    for (0..100) |i| {
        const node = root.start("file_{d}", .{i}, 0);
        defer node.end();
        std.time.sleep(10 * std.time.ns_per_ms);
        root.setCompletedItems(i + 1);
    }
}
```

## Types

### Status

```zig
pub const Status = enum {
    working,
    success,
    failure,
    failure_working,
};
```

### Options

```zig
pub const Options = struct {
    draw_buffer: []u8 = &default_draw_buffer,
    refresh_rate_ns: u64 = 80 * std.time.ns_per_ms,
    initial_delay_ns: u64 = 200 * std.time.ns_per_ms,
    estimated_total_items: usize = 0,
    root_name: []const u8 = "",
    disable_printing: bool = false,
};
```

## API

### Global Control

```zig
// Initialize progress tracking
const root = std.Progress.start(.{ .root_name = "Build" });

// Set global status indicator
std.Progress.setStatus(.working);

// Lock/unlock stderr for intermixing progress with output
std.Progress.lockStdErr();
std.Progress.unlockStdErr();

// Lock and get a writer
const w = std.Progress.lockStderrWriter(&buffer);
defer std.Progress.unlockStderrWriter();
```

### Node Operations

```zig
// Create child node
const child = root.start("Compiling", .{}, estimated_total);

// Update node state
child.setCompletedItems(50);
child.setEstimatedTotalItems(100);
child.increaseEstimatedTotalItems(10);

// Rename node
child.setName("Linking");

// Mark complete
child.end();
```

## Progress Tree Example

```zig
const root = std.Progress.start(.{ .root_name = "Build" });
defer root.end();

// Phase 1
const compile_node = root.start("Compile", .{}, 3);
for (0..3) |i| {
    const file_node = compile_node.start("file.zig", .{}, 0);
    defer file_node.end();
    std.time.sleep(50 * std.time.ns_per_ms);
    compile_node.setCompletedItems(i + 1);
}
compile_node.end();

// Phase 2
const link_node = root.start("Link", .{}, 1);
std.time.sleep(30 * std.time.ns_per_ms);
link_node.completeOne();
link_node.end();
```

## Gotchas

1. **`initial_delay_ns`** — progress display only appears after this delay (default 200ms). Quick operations don't flash the terminal.
2. **Thread-safe** — all Node methods are thread-safe. Use from worker threads.
3. **`disable_printing`** — set to `true` to suppress all progress output (for non-interactive use).
4. **IPC support** — on POSIX, child processes can send progress updates to the parent via `setIpcFd()`.
