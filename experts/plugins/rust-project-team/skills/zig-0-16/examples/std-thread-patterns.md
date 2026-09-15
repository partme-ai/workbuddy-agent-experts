# `std.Thread` Patterns

Offline examples for common Zig 0.16 threading workflows.

## 1. Spawn and join a thread

```zig
const std = @import("std");

fn worker(id: usize) void {
    std.debug.print("worker {} started\n", .{id});
}

test "spawn and join" {
    const thread = try std.Thread.spawn(.{}, worker, .{1});
    thread.join();
}
```

## 2. Protect shared state with a mutex

```zig
const std = @import("std");

const SharedCounter = struct {
    mutex: std.Thread.Mutex = .{},
    value: usize = 0,

    fn increment(self: *SharedCounter) void {
        self.mutex.lock();
        defer self.mutex.unlock();
        self.value += 1;
    }
};

fn bump(counter: *SharedCounter) void {
    var i: usize = 0;
    while (i < 1000) : (i += 1) {
        counter.increment();
    }
}

test "mutex protected counter" {
    var counter = SharedCounter{};

    const t1 = try std.Thread.spawn(.{}, bump, .{&counter});
    const t2 = try std.Thread.spawn(.{}, bump, .{&counter});

    t1.join();
    t2.join();

    try std.testing.expectEqual(@as(usize, 2000), counter.value);
}
```

## 3. Coordinate with `WaitGroup`

```zig
const std = @import("std");

fn doWork(wait_group: *std.Thread.WaitGroup) void {
    defer wait_group.finish();
}

test "wait group" {
    var wait_group: std.Thread.WaitGroup = .{};

    wait_group.start();
    const t1 = try std.Thread.spawn(.{}, doWork, .{&wait_group});

    wait_group.start();
    const t2 = try std.Thread.spawn(.{}, doWork, .{&wait_group});

    wait_group.wait();
    t1.join();
    t2.join();
}
```

## 4. Use atomics for simple counters

```zig
const std = @import("std");

const Counter = struct {
    value: std.atomic.Value(u32) = std.atomic.Value(u32).init(0),

    fn increment(self: *Counter) void {
        _ = self.value.fetchAdd(1, .seq_cst);
    }
};

fn atomicWorker(counter: *Counter) void {
    var i: usize = 0;
    while (i < 1000) : (i += 1) {
        counter.increment();
    }
}

test "atomic counter" {
    var counter = Counter{};
    const t1 = try std.Thread.spawn(.{}, atomicWorker, .{&counter});
    const t2 = try std.Thread.spawn(.{}, atomicWorker, .{&counter});

    t1.join();
    t2.join();

    try std.testing.expectEqual(@as(u32, 2000), counter.value.load(.seq_cst));
}
```

## 5. Guidance

- Use `std.Thread.spawn` for explicit thread creation.
- Use `Mutex` or `RwLock` for shared mutable state.
- Use `WaitGroup` to track task completion across multiple workers.
- Use atomics for small lock-free counters or flags.
- Pair thread creation with `join()` unless the lifecycle is intentionally detached.
