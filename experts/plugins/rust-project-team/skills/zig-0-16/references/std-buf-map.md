# std.BufMap / std.BufSet

String-owning maps and sets — automatically copy and free string memory.

## BufMap (String → String)

```zig
var map = std.BufMap.init(allocator);
defer map.deinit();  // frees all stored strings

// Put (copies both key and value)
try map.put("HOME", "/Users/alice");

// Get
if (map.get("HOME")) |home| { _ = home; }

// Update in place
if (map.getPtr("PATH")) |pp| { pp.* = try map.copy("/new/path"); }

// Remove (frees key + value)
map.remove("PATH");

// Move ownership (no copy)
const k = try allocator.dupe(u8, "KEY");
const v = try allocator.dupe(u8, "val");
try map.putMove(k, v);  // map now owns k and v

// Iteration
var it = map.iterator();
while (it.next()) |entry| {
    std.debug.print("{s}={s}\n", .{ entry.key_ptr.*, entry.value_ptr.* });
}
```

## BufSet (Unique Strings)

```zig
var set = std.BufSet.init(allocator);
defer set.deinit();

try set.insert("apple");
try set.insert("banana");
const has = set.contains("apple");  // true
set.remove("banana");  // frees string

// Iteration
var it = set.iterator();
while (it.next()) |key| { _ = key.*; }

// Clone
var copy = try set.clone();
var arena_copy = try set.cloneWithAllocator(arena.allocator());
```

## Use Cases

### Environment Variables

```zig
var env = std.BufMap.init(alloc);
try env.put("APP_NAME", "MyApp");
try env.put("DEBUG", "true");
// Print all
var it = env.iterator();
while (it.next()) |e| std.debug.print("{s}={s}\n", .{ e.key_ptr.*, e.value_ptr.* });
```

### Unique Word Counter

```zig
var words = std.BufSet.init(alloc);
var tokens = std.mem.tokenizeScalar(u8, text, ' ');
while (tokens.next()) |w| try words.insert(w);
std.debug.print("Unique: {}\n", .{words.count()});
```

## Memory Model

All strings are duplicated on insert, freed on remove/deinit. `putMove` transfers ownership instead of copying.

## Contrast with StringHashMap

| Aspect | StringHashMap | BufMap |
|--------|---------------|--------|
| Ownership | You manage | ✅ Automatic |
| Value type | Any | String only |
| Speed | Faster | Slower (copy) |

## Gotchas

1. **Strings are duplicated** — `put()` copies via `dupe`. For string literals, use `putMove` or store the pointer directly with StringHashMap.
2. **`remove` frees** — any previously returned pointers become invalid.
3. **Iteration order is undefined** — uses hash map internally.
