# std.once

One-time initialization — runs a function exactly once, thread-safely.

## API

```zig
// Wrap a function into a one-time guard
pub fn once(comptime f: fn () void) Once(f)

// The returned type
pub fn Once(comptime f: fn () void) type
```

## Example

```zig
const std = @import("std");

var initialized = std.once(initGlobalState);

fn initGlobalState() void {
    // Runs exactly once, even if call() is invoked from multiple threads
    std.log.info("Global state initialized", .{});
}

pub fn main() void {
    // Thread-safe: multiple calls, but initGlobalState runs once
    initialized.call();
    initialized.call();  // no-op
}
```

## Fields

```zig
pub fn Once(comptime f: fn () void) type {
    return struct {
        done: bool = false,
        mutex: std.Thread.Mutex = .{},

        pub fn call(self: *@This()) void {
            if (!self.done) {
                self.mutex.lock();
                if (!self.done) {
                    f();
                    self.done = true;
                }
                self.mutex.unlock();
            }
        }
    };
}
```

Uses double-checked locking: the `done` flag check avoids the mutex in the common case (already initialized).

## Use Cases

- Global singleton initialization
- Lazy-loaded configuration
- One-time registration (signal handlers, TLS callbacks)

## Gotchas

1. **The function must take no arguments** — `once()` wraps a `fn () void`. For parameterized init, use `once` with a closure or pre-set globals.
2. **Panics in `f` leave `done = false`** — if the init function panics, `call()` will retry on next invocation.
3. **Not async-safe** — the mutex is a regular `std.Thread.Mutex`. Do not hold it across async suspension points.
