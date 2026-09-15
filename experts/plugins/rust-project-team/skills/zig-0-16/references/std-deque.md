# std.deque

Double-ended queue backed by a ring buffer. Supports O(1) push/pop at both ends.

## Type Signature

```zig
pub fn Deque(comptime T: type) type
```

Returns a struct type for a double-ended queue of `T`.

## Initialization

```zig
// Empty deque
var deque: std.Deque(u32) = .empty;

// With capacity
var deque = try std.Deque(u32).initCapacity(allocator, 100);
defer deque.deinit(allocator);

// Fixed buffer (stack allocated, no heap)
var buffer: [64]u32 = undefined;
var deque = std.Deque(u32).initBuffer(&buffer);
```

## Push Operations

```zig
// Push to front — O(1)
try deque.pushFront(allocator, 1);
deque.pushFrontAssumeCapacity(2);  // No allocation
deque.pushFrontBounded(value);     // Returns error if full

// Push to back — O(1)
try deque.pushBack(allocator, 3);
deque.pushBackAssumeCapacity(4);
deque.pushBackBounded(value);
```

## Pop Operations

```zig
const first = deque.popFront();  // returns ?T
const last = deque.popBack();    // returns ?T
```

## Access

```zig
const first = deque.front();  // returns ?T
const last = deque.back();    // returns ?T

// Direct index access
const item = deque.at(2);     // panics if out of bounds
```

## Iteration

```zig
var it = deque.iterator();
while (it.next()) |item| {
    // process item
}
```

## Capacity Management

```zig
try deque.ensureTotalCapacity(allocator, 200);
try deque.ensureTotalCapacityPrecise(allocator, 200);
try deque.ensureUnusedCapacity(allocator, 10);
```

## Use Cases

```zig
// FIFO queue (push back, pop front)
try deque.pushBack(allocator, task);
while (deque.popFront()) |task| { process(task); }

// LIFO stack (push back, pop back)
try deque.pushBack(allocator, item);
while (deque.popBack()) |item| { process(item); }

// Work-stealing deque
try deque.pushFront(allocator, high_priority_task);
try deque.pushBack(allocator, low_priority_task);
```

## Memory Model

Ring buffer layout:

```
      head
       ↓
    ┌───┬───┬───┬───┬───┬───┬───┬───┐
    │ 3 │ 4 │ 1 │ 2 │   │   │   │   │
    └───┴───┴───┴───┴───┴───┴───┴───┘
    └─── items[head..head+len] ──────┘
         (wraps around buffer boundary)
```

- `buffer` — underlying ring buffer slice
- `head` — index of first element in buffer
- `len` — number of elements in deque

## Gotchas

1. **Not contiguous** — unlike ArrayList, deque elements are NOT contiguous in memory. Cannot pass to C APIs expecting arrays.
2. **`initBuffer` has fixed capacity** — operations exceeding buffer size will panic in safe modes.
3. **`pushFrontAssumeCapacity`** asserts capacity — ensure via `ensureUnusedCapacity` first.
4. **Ring buffer wrap-around** — when head+len exceeds buffer length, data wraps to the beginning. This is transparent to the API.

## Quick Reference

| Method | Allocates? | Complexity |
|--------|-----------|------------|
| `pushFront(alloc, item)` | Yes | O(1) amortized |
| `pushBack(alloc, item)` | Yes | O(1) amortized |
| `pushFrontAssumeCapacity(item)` | No | O(1) |
| `pushBackAssumeCapacity(item)` | No | O(1) |
| `popFront()` | No | O(1) |
| `popBack()` | No | O(1) |
| `front()` | No | O(1) |
| `back()` | No | O(1) |
| `at(index)` | No | O(1) |
| `initCapacity(alloc, n)` | Yes | O(n) |
