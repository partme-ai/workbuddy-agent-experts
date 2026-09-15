# std.HashMap / std.AutoHashMap

Hash maps for key-value storage. Several variants for different use cases.

## Types Overview

```zig
// AutoHashMap — automatic hash/eql for simple keys (most common)
std.AutoHashMap(KeyType, ValueType)        // stores allocator internally
std.AutoHashMapUnmanaged(KeyType, ValueType) // no stored allocator

// StringHashMap — optimized for []const u8 keys
std.StringHashMap(ValueType)
std.StringHashMapUnmanaged(ValueType)

// ArrayHashMap — preserves insertion order with indexed access
std.ArrayHashMap(K, V, Context, store_hash)
std.AutoArrayHashMap(K, V)             // like AutoHashMap but ordered
std.StringArrayHashMap(V)              // like StringHashMap but ordered

// Full generic HashMap — custom context, configurable load factor
std.HashMap(K, V, Context, store_hash)
```

## AutoHashMap (Simple Keys)

```zig
var map = std.AutoHashMap(u32, []const u8).init(allocator);
defer map.deinit();

// Insert / update
try map.put(42, "answer");
try map.put(42, "updated");  // overwrites

// Get
const val = map.get(42);       // ?[]const u8
const ptr = map.getPtr(42);    // ?*[]const u8 (for modification)
if (ptr) |p| p.* = "changed";

// Remove
const kv = map.fetchRemove(42);  // ?KV — returns removed entry
const found = map.remove(42);    // bool — true if existed

// Check
const exists = map.contains(42);
const n = map.count();           // number of entries
const cap = map.capacity();      // current capacity
```

## StringHashMap (String Keys)

```zig
var map = std.StringHashMap(i32).init(allocator);
defer map.deinit();

try map.put("foo", 123);
try map.put("bar", 456);
const val = map.get("foo");  // ?i32

// Duplicate keys (if key lifetime matters)
const key_copy = try allocator.dupe(u8, external_key);
errdefer allocator.free(key_copy);
try map.put(key_copy, value);  // map now owns the key
```

## getOrPut Pattern (Most Efficient)

Single lookup for insert-or-update:

```zig
const gop = try map.getOrPut(key);
if (gop.found_existing) {
    gop.value_ptr.* += 1;
} else {
    gop.value_ptr.* = 1;
}
```

## Unmanaged Variant

No stored allocator — pass to each method. Lighter struct, explicit ownership:

```zig
var map: std.AutoHashMapUnmanaged(u32, []const u8) = .empty;
defer map.deinit(allocator);

try map.put(allocator, 42, "answer");
const val = map.get(42);
_ = map.remove(42);
```

## Capacity Management

```zig
try map.ensureTotalCapacity(allocator, 100);  // reserve for N entries
map.clearRetainingCapacity();  // keep memory, remove entries
map.clearAndFree(allocator);   // free memory
```

## Iteration

```zig
// Iterator (entries in arbitrary order)
var it = map.iterator();
while (it.next()) |entry| {
    _ = entry.key_ptr.*;    // *K
    _ = entry.value_ptr.*;  // *V
}

// Keys and values as slices
for (map.keys()) |key| { _ = key; }
for (map.values()) |val| { _ = val; }
```

## Custom Context

For custom hash/equality, non-standard key types, or performance tuning:

```zig
const MyContext = struct {
    seed: u64,

    pub fn hash(self: MyContext, key: MyKey) u64 {
        return std.hash.xxhash.hash64(std.mem.asBytes(&key)) ^ self.seed;
    }
    pub fn eql(self: MyContext, a: MyKey, b: MyKey) bool {
        return @as(u64, @bitCast(a)) == @as(u64, @bitCast(b));
    }
};

var map = std.HashMap(MyKey, Value, MyContext, 80).initContext(
    allocator,
    MyContext{ .seed = 42 },
);
defer map.deinit();
```

Parameters of `std.HashMap(K, V, Context, store_hash)`:
- `K` — key type
- `V` — value type
- `Context` — struct with `hash` and `eql` methods
- `store_hash` — `bool`: if true, stores hash alongside key for faster rehash (more memory)

## ArrayHashMap (Ordered)

Preserves insertion order, supports index access:

```zig
var map = std.AutoArrayHashMap(u32, []const u8).init(allocator);
defer map.deinit();

try map.put(2, "second");
try map.put(1, "first");

// Insertion order: 2→"second", 1→"first"
for (map.keys(), map.values()) |k, v| {
    std.debug.print("{d}:{s}\n", .{k, v});
}

// Index access
const first_key = map.keys()[0];     // 2
const first_val = map.values()[0];   // "second"

// Swap remove (O(1), changes order)
map.swapRemove(2);

// Ordered remove (O(n), preserves order)
map.orderedRemove(1);

// Sort by key or value
map.sort(std.sort.asc(u32));
```

## Common Patterns

### Word Frequency Counter

```zig
var counts = std.StringHashMap(usize).init(allocator);
defer counts.deinit();

for (words) |word| {
    const gop = try counts.getOrPut(word);
    gop.value_ptr.* = if (gop.found_existing) gop.value_ptr.* + 1 else 1;
}
```

### Cache with Owned Keys

```zig
var cache = std.StringHashMap(Data).init(allocator);
defer {
    // Free all keys and values
    var it = cache.iterator();
    while (it.next()) |entry| {
        allocator.free(entry.key_ptr.*);
        entry.value_ptr.*.deinit();
    }
    cache.deinit();
}

pub fn insert(allocator: Allocator, key: []const u8, data: Data) !void {
    const key_copy = try allocator.dupe(u8, key);
    errdefer allocator.free(key_copy);
    try cache.put(key_copy, data);
}
```

### Index Map (Dense Keys)

```zig
// AutoHashMap is overkill for dense integer keys — use ArrayList instead
// AutoHashMap is best for sparse keys or non-integer types
```

### EnsureUnusedCapacity for Batch Insert

```zig
try map.ensureUnusedCapacity(allocator, items.len);
for (items) |item| {
    map.putAssumeCapacity(item.key, item.value);  // no alloc, asserts capacity
}
```

## Memory Model

```
HashMap stores:
  keys[]: [K|K|K|K|_|_|_|_]     — key slots
  values[]: [V|V|V|V|_|_|_|_]   — value slots (parallel array)

Load factor: entries / capacity. When exceeds max, grows and rehashes.
Default max load: 80% (0.80). Configurable via the HashMap type parameter.
```

## Gotchas

1. **`put` allocates** — may trigger resize/rehash. Use `ensureUnusedCapacity` + `putAssumeCapacity` for batch inserts.
2. **Iteration order is undefined** — use `AutoArrayHashMap` for insertion-order preservation.
3. **`getOrPut` is the most efficient lookup-modify** — avoids double hash for insert-then-modify.
4. **String keys are not duplicated** — `StringHashMap` stores the pointer you pass. If the key memory is temporary, duplicate it.
5. **`fetchRemove` returns the key-value pair** — you're responsible for freeing owned keys after removal.
6. **`.empty` for Unmanaged** — `var map: AutoHashMapUnmanaged(K,V) = .empty`, never `= .{}`.
7. **Context `store_hash` parameter** — setting `true` uses more memory but makes rehashing faster. Good for large maps.
