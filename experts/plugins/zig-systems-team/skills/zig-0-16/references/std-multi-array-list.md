# std.MultiArrayList

Struct-of-Arrays (SoA) container — stores each struct field in a separate contiguous array. Cache-efficient for field-focused access patterns.

## When to Use

- Often access only some fields of many structs
- Cache-friendly column processing
- Tagged unions (tags and data stored separately)

## Initialization

```zig
const Item = struct { id: u32, name: []const u8, score: f32 };

var list: std.MultiArrayList(Item) = .{};
defer list.deinit(allocator);

try list.ensureTotalCapacity(allocator, 100);
```

## Basic Operations

```zig
try list.append(allocator, .{ .id = 1, .name = "foo", .score = 0.5 });
list.appendAssumeCapacity(.{ .id = 2, .name = "bar", .score = 0.8 });

const item = list.get(0);        // full struct
list.set(0, new_item);           // set full struct

// Field arrays (MAIN BENEFIT — contiguous per field)
const ids = list.items(.id);       // []u32
const scores = list.items(.score); // []f32
list.items(.score)[0] = 1.0;

const last = list.pop();  // ?Item
const n = list.len;
```

## Slice API

```zig
const slices = list.slice();
// Reuse for multiple accesses without recomputing offsets
for (slices.items(.id), slices.items(.score)) |id, score| { _ = .{id, score}; }
```

## Removal

```zig
list.swapRemove(index);       // O(1), order NOT preserved
list.orderedRemove(index);    // O(n), order preserved
list.orderedRemoveMany(&.{ 1, 5, 7 });  // must be sorted ascending
```

## Tagged Union Support

```zig
const Value = union(enum) { int: i64, float: f64, string: []const u8 };

var values: std.MultiArrayList(Value) = .{};
try values.append(allocator, .{ .int = 42 });
try values.append(allocator, .{ .float = 3.14 });

const tags = values.items(.tags);  // []meta.Tag(Value)
const data = values.items(.data);  // untagged union data
```

## Sorting

```zig
list.sort(struct {
    scores: []const f32,
    fn lessThan(ctx: @This(), a: usize, b: usize) bool {
        return ctx.scores[a] < ctx.scores[b];
    }
}{ .scores = list.items(.score) });
```

## Capacity

```zig
try list.ensureTotalCapacity(allocator, 100);
try list.ensureUnusedCapacity(allocator, 10);
try list.resize(allocator, new_len);
list.shrinkAndFree(allocator, new_len);
list.clearAndFree(allocator);
```

## Memory Layout

```
AoS: [id0][name0][s0][id1][name1][s1]...  (padding between fields)
SoA: [id0][id1][id2]...  [name0][name1]...  [s0][s1][s2]...
```

## Gotchas

1. **`items(.field)` — field name in parentheses**, not dot access.
2. **`list.len` is a raw field** — read/write directly.
3. **Sorting swaps field arrays** — use MultiArrayList's `sort` method, not `std.sort`.
