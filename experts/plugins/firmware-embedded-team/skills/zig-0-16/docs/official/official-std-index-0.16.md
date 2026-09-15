# Zig 0.16 Standard Library Index (Official Distillation)

Source: https://ziglang.org/documentation/0.16.0/std/

This page is the canonical entry to the Zig standard library API documentation. It lists:

- Top-level public types (e.g. `std.ArrayList`, `std.Build`, `std.Io`, `std.Thread`)
- Namespaces (e.g. `std.mem`, `std.fs`, `std.http`, `std.json`, `std.crypto`)
- Global variables and values such as `std.options`

## How to navigate the official std index

- Treat the std index as the authoritative "what exists" list.
- Use it to confirm names and locate the real API docs for a symbol.
- Use the local `../../references/std-*.md` files for curated, copyable patterns and offline guidance.

## Major modules (high-frequency)

This is a practical grouping aligned with the official index:

### Build and tooling

- `std.Build` -> see `../../references/std-build.md`
- `std.zig` -> see `../../references/std-zig.md`
- `std.zon` -> see `../../references/std-zon.md`

### I/O, filesystem, process, OS

- `std.Io` -> see `../../references/std-io.md`
- `std.fs` -> see `../../references/std-fs.md`
- `std.process` -> see `../../references/std-process.md`
- `std.os` -> see `../../references/std-os.md`
- `std.c` -> see `../../references/std-c.md`

### Data formats and networking

- `std.http` -> see `../../references/std-http.md`
- `std.net` -> see `../../references/std-net.md`
- `std.Uri` -> see `../../references/std-uri.md`
- `std.json` -> see `../../references/std-json.md`

### Memory and text

- `std.heap` -> see `../../references/std-allocators.md`
- `std.mem` -> see `../../references/std-mem.md`
- `std.fmt` -> see `../../references/std-fmt.md`
- `std.ascii` -> see `../../references/std-ascii.md`
- `std.unicode` -> see `../../references/std-unicode.md`
- `std.base64` -> see `../../references/std-base64.md`

### Concurrency and atomics

- `std.Thread` -> see `../../references/std-thread.md`
- `std.atomic` -> see `../../references/std-atomic.md`

### Containers

- `std.ArrayList` -> see `../../references/std-arraylist.md`
- `std.HashMap` / `std.AutoHashMap` -> see `../../references/std-hashmap.md`
- `std.ArrayHashMap` -> see `../../references/std-array-hash-map.md`
- `std.MultiArrayList` -> see `../../references/std-multi-array-list.md`
- `std.StaticStringMap` -> see `../../references/std-static-string-map.md`
- `std.bit_set` -> see `../../references/std-bit-set.md`
- `std.PriorityQueue` -> see `../../references/std-priority-queue.md`
- `std.PriorityDequeue` -> see `../../references/std-priority-dequeue.md`

### Algorithms and security

- `std.sort` -> see `../../references/std-sort.md`
- `std.math` -> see `../../references/std-math.md`
- `std.hash` -> see `../../references/std-hash.md`
- `std.crypto` -> see `../../references/std-crypto.md`
- `std.Random` -> see `../../references/std-random.md`

## `std.options`

The index documents `std.options` as compile-time known settings overridable by the root source file.

Practical usage:

- Treat it as part of the compilation configuration surface.
- Prefer build options for user-tunable configuration and `std.options` for compile-time-known settings.
