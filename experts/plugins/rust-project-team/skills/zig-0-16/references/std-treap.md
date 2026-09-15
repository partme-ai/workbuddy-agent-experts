# std.Treap

Randomized binary search tree — ordered key storage with O(log n) average operations. Self-balancing via random priorities.

## When to Use

- Need ordered key storage with in-order iteration
- Min/max and predecessor/successor queries
- HashMap doesn't support ordering

## Initialization

```zig
const MyTreap = std.Treap(u64, std.math.order);
var treap: MyTreap = .{};  // no allocator needed (intrusive)
```

## Node Structure

Nodes are user-managed (intrusive design):

```zig
var nodes: [100]MyTreap.Node = undefined;
// Node fields: key, priority, parent, children[2]
```

## Insert via Entry API

```zig
var entry = treap.getEntryFor(key);
if (entry.node == null) {
    entry.set(&nodes[i]);  // assign pre-allocated node
}
```

## Remove / Replace

```zig
var entry = treap.getEntryFor(key);
entry.set(null);  // removes node

// Replace with new node (same key)
entry.set(&new_node);
```

## Lookup

```zig
var entry = treap.getEntryFor(key);
if (entry.node) |node| { _ = node.key; }
```

## Min / Max

```zig
if (treap.getMin()) |n| { _ = n.key; }
if (treap.getMax()) |n| { _ = n.key; }
```

## Predecessor / Successor

```zig
if (node.next()) |s| { /* key > node.key */ }
if (node.prev()) |p| { /* key < node.key */ }
```

## In-Order Iteration

```zig
var iter = treap.inorderIterator();
while (iter.next()) |node| { _ = node.key; }
```

## Custom Comparator

```zig
fn cmp(a: []const u8, b: []const u8) std.math.Order {
    return std.mem.order(u8, a, b);
}
const StringTreap = std.Treap([]const u8, cmp);
```

## Complete Example

```zig
const Treap = std.Treap(u64, std.math.order);

var treap: Treap = .{};
var nodes: [10]Treap.Node = undefined;

for (0..10) |i| {
    treap.getEntryFor(@intCast(i)).set(&nodes[i]);
}

// Find key 5 and its neighbors
var entry = treap.getEntryFor(5);
if (entry.node) |node| {
    if (node.prev()) |p| std.debug.print("prev: {}\n", .{p.key});
    if (node.next()) |n| std.debug.print("next: {}\n", .{n.key});
}

// In-order traversal: 0 1 2 3 4 5 6 7 8 9
var iter = treap.inorderIterator();
while (iter.next()) |node| std.debug.print("{} ", .{node.key});
```

## Gotchas

1. **Intrusive design** — you manage node memory. The treap never allocates.
2. **`node.priority == 0` means not in treap** — the treap's balancing uses randomized priorities.
3. **Entry API is atomic** — `getEntryFor` + `set` allows safe check-and-modify.
4. **Comparator must be deterministic** — non-deterministic comparison breaks the tree.
