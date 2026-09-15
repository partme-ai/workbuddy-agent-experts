# std.ArrayList

Dynamic array (vector) — contiguous, growable sequence of elements. The most commonly used data structure in Zig.

**Note:** `std.ArrayListUnmanaged` is now deprecated in Zig 0.15+ — use `std.ArrayList` (unmanaged is now the default, the old `ArrayList` alias was removed).

## Initialization

### Empty List
```zig
var list: std.ArrayList(u32) = .empty;
defer list.deinit(allocator);
```

### With Pre-allocated Capacity
```zig
var list = try std.ArrayList(u32).initCapacity(allocator, 100);
defer list.deinit(allocator);
// list.items.len == 0, list.capacity >= 100
```

### From Existing Slice (ownership transfer)
```zig
const existing = try allocator.alloc(u32, 10);
var list = std.ArrayList(u32).fromOwnedSlice(existing);
// list now owns the memory, will free on deinit
```

### Stack-allocated Buffer (no heap allocator needed)
```zig
var buffer: [8]i32 = undefined;
var stack = std.ArrayList(i32).initBuffer(&buffer);
// Operations will panic if capacity (8) exceeded
```

### Replicate a Value N Times
```zig
var list = try std.ArrayList(u32).initWithCapacity(allocator, 5);
list.appendNTimesAssumeCapacity(42, 5); // [42, 42, 42, 42, 42]
```

## Basic Operations

### Append
```zig
// May allocate — slower but safe
try list.append(allocator, 42);
try list.appendSlice(allocator, &[_]u32{1, 2, 3});

// No allocation — asserts enough capacity
list.appendAssumeCapacity(42);
list.appendSliceAssumeCapacity(&[_]u32{1, 2, 3});
```

### Access
```zig
const items = list.items;  // []T — the underlying slice
const first = list.items[0];
const last = list.getLast();      // returns ?T
const popped = list.pop();        // returns ?T, removes last
const first_or_null = list.getFirst();  // returns ?T
```

### Insert
```zig
// Insert at index — shifts elements right, O(n)
try list.insert(allocator, 2, value);
try list.insertSlice(allocator, 2, &[_]u32{10, 20});
```

### Remove
```zig
// O(n) — preserves order, shifts elements left
const removed = list.orderedRemove(index);

// O(1) — swaps with last then pops, order NOT preserved
const removed = list.swapRemove(index);

// Remove range — O(n), shifts remaining left
list.replaceRange(2, 3, &.{}); // removes 3 items at index 2

// Remove last N
list.shrinkRetainingCapacity(list.items.len - n);
```

### Replace Range
```zig
// Replace 2 items at index 1 with 3 new items
try list.replaceRange(1, 2, &[_]u32{10, 20, 30});
// If new_len > old_len: shifts remaining right
// If new_len < old_len: shifts remaining left
```

### Resize
```zig
// Grow or shrink to exact length
try list.resize(allocator, 100); // fills new slots with undefined

// Resize and fill new slots with a value
try list.resize(allocator, 100, 0); // fills with 0
```

## Capacity Management

```zig
// Reserve space for N MORE items
try list.ensureUnusedCapacity(allocator, 10);

// Reserve TOTAL capacity of at least N
try list.ensureTotalCapacity(allocator, 100);
try list.ensureTotalCapacityPrecise(allocator, 100); // exact

// Shrink allocated memory to fit current length
list.shrinkAndFree(allocator, list.items.len);  // keep first N, free rest

// Clear
list.clearRetainingCapacity();  // len=0, memory kept
list.clearAndFree(allocator);   // len=0, memory freed
```

## Ownership Transfer

```zig
// Take ownership of items (list becomes empty)
const owned = try list.toOwnedSlice(allocator);
defer allocator.free(owned);  // caller must free

// Null-terminated slice (for C interop)
const z = try list.toOwnedSliceSentinel(allocator, 0);
defer allocator.free(z);

// Allocator-agnostic ownership transfer
const slice = try list.toOwnedSlice();
// Uses the allocator stored in the ArrayList
```

## Sorting & Searching

```zig
// Sort in place
std.sort.block(u32, list.items, {}, comptime std.sort.asc(u32));
std.sort.block(u32, list.items, {}, comptime std.sort.desc(u32));

// Custom sort key
std.sort.block(MyStruct, list.items, {}, struct {
    fn lessThan(_: void, a: MyStruct, b: MyStruct) bool {
        return a.key < b.key;
    }
}.lessThan);

// Binary search (requires sorted data)
const index = std.sort.lowerBound(u32, list.items, 42);
```

## Iteration Patterns

```zig
// Read-only
for (list.items) |item| { _ = item; }

// Mutable
for (list.items) |*item| { item.* += 1; }

// With index
for (list.items, 0..) |item, i| { _ = .{ item, i }; }

// Reverse iteration
var i: usize = list.items.len;
while (i > 0) {
    i -= 1;
    // process list.items[i]
}

// While popping (consumes list)
while (list.pop()) |item| { _ = item; }

// Remove while iterating (backwards)
var i: usize = list.items.len;
while (i > 0) {
    i -= 1;
    if (shouldRemove(list.items[i])) {
        _ = list.swapRemove(i);
    }
}
```

## Common Patterns

### Collect from Iterator
```zig
var list: std.ArrayList(u8) = .empty;
for (some_iterator) |item| {
    try list.append(allocator, item);
}
```

### Build String
```zig
var buf: std.ArrayList(u8) = .empty;
try buf.appendSlice(allocator, "Hello ");
try buf.appendSlice(allocator, name);
const result = try buf.toOwnedSlice(allocator);
```

### Writer Interface
```zig
// ArrayList can be used as a writer
var buf: std.ArrayList(u8) = .empty;
const writer = buf.writer(allocator);
try writer.print("Hello {s}", .{name});
const result = try buf.toOwnedSlice(allocator);
```

### Batch Append with Ensure Capacity
```zig
// Pre-reserve to reduce allocations
try list.ensureTotalCapacityPrecise(allocator, known_count);
for (data) |item| {
    list.appendAssumeCapacity(item);
}
```

### Array of Structs Pattern
```zig
const Point = struct { x: f32, y: f32 };
var points: std.ArrayList(Point) = .empty;
try points.append(allocator, .{ .x = 1.0, .y = 2.0 });
```

## Reserve-First Pattern (Exception Safety)

When inserting into multiple containers, reserve capacity first so mutations are infallible:

```zig
// BAD — partial failure leaves invalid state
fn addItem(list: *std.ArrayList(u32), map: *std.AutoHashMap(u32, void), gpa: Allocator, value: u32) !void {
    try list.append(gpa, value);
    try map.put(gpa, value, {}); // If this fails, list has orphan entry!
}

// GOOD — reserve first, then mutate
fn addItem(list: *std.ArrayList(u32), map: *std.AutoHashMap(u32, void), gpa: Allocator, value: u32) !void {
    try list.ensureUnusedCapacity(gpa, 1);
    try map.ensureUnusedCapacity(gpa, 1);
    // Phase 2: Infallible mutations
    list.appendAssumeCapacity(value);
    map.putAssumeCapacity(value, {});
}
```

## BoundedArray Replacement

`std.BoundedArray` was removed in Zig 0.15.x:

```zig
// NEW — use initBuffer
var buffer: [64]u8 = undefined;
var arr = std.ArrayList(u8).initBuffer(&buffer);
try arr.appendBounded(value);  // returns error.OutOfMemory if full
```

## Memory Model

```
list.items  ┌────┬────┬────┬────┬────┬────┬────┬────┐
            │  0 │  1 │  2 │  3 │ .. │ .. │ .. │ .. │
            └────┴────┴────┴────┴────┴────┴────┴────┘
            └───────── items.len ──────────┘
            └─────────────── capacity ─────────────────┘
```

- `items.len` ≤ `capacity`
- `deinit()` frees `items[0..capacity]`
- Use `ensureTotalCapacity` / `ensureUnusedCapacity` to grow
- After `shrinkAndFree`, `capacity == items.len`

## Type Signature

```zig
pub fn ArrayList(comptime T: type) type {
    return struct {
        items: []T = &.{},
        capacity: usize = 0,
        allocator: Allocator = undefined,
        // ...
    };
}
```

The struct stores the allocator so convenience methods like `toOwnedSlice()` and `writer()` can use it without passing one each call.

## Gotchas

1. **Use `.empty` not `.{ }`** — `var list: ArrayList(u32) = .{}` does NOT initialize correctly. Use `= .empty`
2. **`deinit(allocator)` frees the buffer** — call before the allocator goes out of scope
3. **`appendAssumeCapacity` asserts** — will panic in safe modes if capacity is insufficient
4. **`items` is borrowed** — after `deinit`, `items` is a dangling pointer
5. **`append` may reallocate** — this invalidates any previously held pointers into `items`
6. **`initBuffer` has fixed capacity** — operations that exceed the buffer size will panic
7. **`shrinkAndFree` reallocates** — the `items` pointer changes after this call

## Quick Reference

| Method | Allocates? | Returns |
|--------|-----------|---------|
| `append(alloc, item)` | Yes | `!void` |
| `appendAssumeCapacity(item)` | No | `void` |
| `appendSlice(alloc, items)` | Yes | `!void` |
| `insert(alloc, i, item)` | Yes | `!void` |
| `orderedRemove(i)` | No | `T` |
| `swapRemove(i)` | No | `T` |
| `pop()` | No | `?T` |
| `getLast()` | No | `?T` |
| `initCapacity(alloc, n)` | Yes | `!Self` |
| `ensureUnusedCapacity(alloc, n)` | Yes | `!void` |
| `shrinkAndFree(alloc, n)` | Yes | `void` |
| `toOwnedSlice(alloc)` | No | `![]T` |
| `writer(alloc)` | No | `Writer` |
