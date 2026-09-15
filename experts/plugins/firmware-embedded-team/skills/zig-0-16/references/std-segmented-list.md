# std.SegmentedList

Dynamic list with **stable pointers** — appending never invalidates existing element pointers. Uses exponential segment growth.

## When to Use

- Pointers to elements must survive appends
- Arena allocator backing
- Non-copyable element types

## Trade-offs

- O(log n) random access (vs O(1) for ArrayList)
- Elements not fully contiguous
- Higher per-element overhead

## Initialization

```zig
// No prealloc
var list = std.SegmentedList(i32, 0){};
defer list.deinit(allocator);

// With inline prealloc (must be power of 2)
var list = std.SegmentedList(i32, 16){};
defer list.deinit(allocator);
```

## Basic Operations

```zig
try list.append(allocator, 42);
try list.appendSlice(allocator, &[_]i32{1, 2, 3});

const ptr = list.at(0);   // *i32 — STABLE pointer
ptr.* = 100;

const new_ptr = try list.addOne(allocator);  // append + get pointer
new_ptr.* = 42;

const last = list.pop();  // ?i32
const n = list.count();
```

## Iteration

```zig
// Mutable
var it = list.iterator(0);
while (it.next()) |ptr| { ptr.* += 1; }

// Const
var it = list.constIterator(0);
while (it.next()) |ptr| { _ = ptr.*; }

// Bidirectional
while (it.prev()) |ptr| { _ = ptr.*; }

// Peek / jump
if (it.peek()) |ptr| { _ = ptr.*; }
it.set(50);
```

## Capacity

```zig
try list.growCapacity(allocator, 100);
try list.setCapacity(allocator, 100);
list.shrinkRetainingCapacity(new_len);
list.clearAndFree(allocator);
```

## Copy to Contiguous Slice

```zig
var dest: [100]i32 = undefined;
list.writeToSlice(&dest, 0);      // copy from index 0
list.writeToSlice(dest[50..], 50); // copy from index 50
```

## Memory Layout

Segments grow exponentially: 1, 2, 4, 8, 16... elements per segment.

## Use Case: Object Pool with Stable References

```zig
const Object = struct { data: [1024]u8, next: ?*Object };

var pool = std.SegmentedList(Object, 64){};

const obj1 = try pool.addOne(allocator);
const obj2 = try pool.addOne(allocator);
obj1.next = obj2;  // safe — pointers never invalidated
```

## Gotchas

1. **`at(i)` returns `*T`** — modifies the list directly.
2. **O(log n) random access** — slower than ArrayList for index-heavy patterns.
3. **Elements are not fully contiguous** — can't pass to C APIs as a slice.
