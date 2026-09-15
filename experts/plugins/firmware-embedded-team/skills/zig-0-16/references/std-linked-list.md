# std.DoublyLinkedList / std.SinglyLinkedList

Intrusive linked lists for O(1) insertion/removal. Nodes are embedded in user structs and accessed via `@fieldParentPtr`.

## When to Use

✅ **Good for:**
- O(1) insertion/removal at known positions
- Elements that need to be in multiple lists simultaneously
- Pre-allocated or arena-allocated nodes
- No allocation needed on insert (nodes already exist)
- LRU caches, free lists, intrusive queues

❌ **Not ideal for:**
- Linear search — O(n) access by index
- Small lists where ArrayList is simpler
- Data that needs to be passed to C APIs (use ArrayList)

## DoublyLinkedList

Bidirectional traversal, O(1) removal of any node (if you have a pointer to it).

### Setup

```zig
const std = @import("std");

const Item = struct {
    data: u32,
    node: std.DoublyLinkedList.Node = .{},  // embed the node
};

var list: std.DoublyLinkedList = .{};

// Create items (you manage memory)
var a: Item = .{ .data = 1 };
var b: Item = .{ .data = 2 };
var c: Item = .{ .data = 3 };
```

### Insert

```zig
list.append(&a.node);          // add to end
list.prepend(&b.node);         // add to front
list.insertAfter(&a.node, &c.node);   // c after a
list.insertBefore(&c.node, &b.node);  // b before c
```

### Remove

```zig
list.remove(&a.node);          // O(1) — given node pointer
const last = list.pop();       // remove and return last node
const first = list.popFirst(); // remove and return first node
```

### Access

```zig
if (list.first) |node| {
    const item: *Item = @fieldParentPtr("node", node);
    std.debug.print("data: {}\n", .{item.data});
}

if (list.last) |node| {
    const item: *Item = @fieldParentPtr("node", node);
}
```

### Traversal

```zig
// Forward
var it = list.first;
while (it) |node| : (it = node.next) {
    const item: *Item = @fieldParentPtr("node", node);
}

// Backward
var it = list.last;
while (it) |node| : (it = node.prev) {
    const item: *Item = @fieldParentPtr("node", node);
}
```

### Bulk Operations

```zig
// Move all nodes from list2 to end of list1 (O(1))
list1.concatByMoving(&list2);

// Count (O(n) — consider tracking separately)
const n = list.len();
```

### Node Properties

```zig
node.prev   // ?*Node — previous node
node.next   // ?*Node — next node
```

## SinglyLinkedList

Forward-only, minimal memory (one pointer per node instead of two).

### Setup

```zig
const Item = struct {
    data: u32,
    node: std.SinglyLinkedList.Node = .{},
};

var list: std.SinglyLinkedList = .{};
var a: Item = .{ .data = 1 };
var b: Item = .{ .data = 2 };
```

### Insert

```zig
list.prepend(&a.node);         // add to front only
a.node.insertAfter(&b.node);   // insert b after a
```

### Remove

```zig
const first = list.popFirst();       // remove and return first
_ = a.node.removeNext();             // remove node after a (O(1))
list.remove(&b.node);                // O(n) — must find predecessor
```

### Traversal

```zig
var it = list.first;
while (it) |node| : (it = node.next) {
    const item: *Item = @fieldParentPtr("node", node);
}
```

### Node Methods

```zig
node.next                          // ?*Node
node.insertAfter(new_node)         // insert new_node after node
node.removeNext()                  // ?*Node — removes and returns next
node.findLast()                    // *Node — find tail from this node
node.countChildren()               // usize — count from this node forward
node.reverse(&optional_ptr)        // reverse list from this node
```

## Common Patterns

### LRU Cache

```zig
const Entry = struct {
    key: []const u8,
    value: Value,
    node: std.DoublyLinkedList.Node = .{},
};

var lru_list: std.DoublyLinkedList = .{};
var lookup: std.StringHashMap(*Entry) = .init(allocator);

fn access(key: []const u8) ?*Entry {
    const entry = lookup.get(key) orelse return null;
    // Move to front (most recently used)
    lru_list.remove(&entry.node);
    lru_list.prepend(&entry.node);
    return entry;
}

fn evictOldest() void {
    while (lru_list.pop()) |node| {
        const entry: *Entry = @fieldParentPtr("node", node);
        _ = lookup.remove(entry.key);
        allocator.free(entry.key);
        allocator.destroy(entry);
        break;  // evict one
    }
}
```

### Free List

```zig
var free_nodes: std.SinglyLinkedList = .{};

fn acquire() *Node {
    if (free_nodes.popFirst()) |node| return node;
    return allocator.create(Node) catch @panic("OOM");
}

fn release(node: *Node) void {
    free_nodes.prepend(node);
}
```

### Intrusive Queue

```zig
var queue: std.DoublyLinkedList = .{};

fn enqueue(node: *Node) void {
    queue.append(node);
}

fn dequeue() ?*Node {
    return queue.popFirst();
}
```

## Memory Considerations

| Aspect | ArrayList | Linked List |
|--------|-----------|-------------|
| Memory | Contiguous, cache-friendly | Scattered, cache-unfriendly |
| Insert at end | O(1) amortized | O(1) |
| Insert at front | O(n) | O(1) |
| Remove by value | O(n) | O(1) if node known |
| Index access | O(1) | O(n) |
| Memory overhead | None (just capacity) | 1-2 pointers per node |
| Allocation on insert | Yes (may grow) | No (nodes pre-allocated) |

## Gotchas

1. **`@fieldParentPtr` is required** — linked list nodes don't know their containing struct. Use `@fieldParentPtr("field_name", &node)` to get the parent.
2. **You manage node memory** — the list never allocates or frees nodes. You must allocate/deallocate nodes yourself.
3. **Node must not be in multiple lists** — a `Node` has only one `next`/`prev`. For multiple lists, use multiple node fields.
4. **`remove()` on DoublyLinkedList requires a pointer to the exact node** — not a copy, not null.
5. **`len()` is O(n)** — for frequent size queries, track the count separately.
6. **Don't use after free** — removing a node doesn't deallocate it; disposing the containing struct while still in a list causes dangling pointers.
7. **`concatByMoving` leaves source list empty** — all nodes are moved, not copied.
