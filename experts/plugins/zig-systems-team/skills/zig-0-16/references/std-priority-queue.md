# std.PriorityQueue

Binary heap-based priority queue. Efficiently retrieves elements by priority order. Backed by `std.ArrayList`.

## When to Use

- Task scheduling by priority
- Dijkstra's algorithm, A* pathfinding
- Event-driven simulation (process soonest event first)
- Merging sorted streams
- Top-K selection problems

## Initialization

### Min-Heap (Smallest First)

```zig
const std = @import("std");

fn lessThan(context: void, a: u32, b: u32) std.math.Order {
    _ = context;
    return std.math.order(a, b);
}

const PQ = std.PriorityQueue(u32, void, lessThan);
var queue = PQ.init(allocator, {});
defer queue.deinit();
```

### Max-Heap (Largest First)

```zig
fn greaterThan(_: void, a: u32, b: u32) std.math.Order {
    return std.math.order(a, b).invert();
}

const MaxPQ = std.PriorityQueue(u32, void, greaterThan);
```

### Inline Comparator

```zig
var queue = std.PriorityQueue(u32, void, struct {
    fn order(_: void, a: u32, b: u32) std.math.Order {
        return std.math.order(a, b);
    }
}.order).init(allocator, {});
```

## Basic Operations

```zig
// Add elements
try queue.add(54);
try queue.add(12);
try queue.add(7);
try queue.addSlice(&[_]u32{ 1, 2, 3 });

// Peek at highest priority (doesn't remove)
if (queue.peek()) |top| {
    std.debug.print("top: {d}\n", .{top});  // 7 for min-heap
}

// Remove highest priority
const top = queue.remove();           // asserts non-empty → T
const maybe = queue.removeOrNull();   // returns ?T

// Size
const n = queue.count();
const cap = queue.capacity();
const empty = queue.len() == 0;
```

## From Existing Slice

```zig
// Take ownership, heapify in place (O(n))
var items = try allocator.dupe(u32, &[_]u32{ 5, 3, 8, 1, 2 });
var queue = PQ.fromOwnedSlice(allocator, items, {});
// Now a valid heap — no additional allocation
```

## Context-Based Comparator

Use context for comparing by external data (e.g., Dijkstra distances):

```zig
fn compareByScore(scores: []const u32, a: usize, b: usize) std.math.Order {
    return std.math.order(scores[a], scores[b]);
}

const IndexPQ = std.PriorityQueue(usize, []const u32, compareByScore);

const scores = [_]u32{ 50, 30, 80, 20 };
var queue = IndexPQ.init(allocator, &scores);

try queue.add(0);  // score 50
try queue.add(1);  // score 30
try queue.add(2);  // score 80
try queue.add(3);  // score 20

const best = queue.remove();  // 3 (score 20 is smallest)
```

## Update Priority

```zig
// Remove old value, add new value (O(n) for find + O(log n) for heapify)
try queue.update(old_value, new_value);
// Error if old_value not found in queue
```

## Remove by Index

```zig
const removed = queue.removeIndex(0);  // remove at heap position, O(log n)
```

## Iteration

```zig
// Iterate WITHOUT removing (order IS NOT priority order — it's heap array order)
var it = queue.iterator();
while (it.next()) |elem| { _ = elem; }
it.reset();  // restart from beginning
```

## Capacity Management

```zig
try queue.ensureTotalCapacity(100);
try queue.ensureUnusedCapacity(10);
queue.shrinkAndFree(new_capacity);
queue.clearRetainingCapacity();
queue.clearAndFree();
```

## Complete Example: Task Scheduler

```zig
const std = @import("std");

const Task = struct {
    name: []const u8,
    priority: u32,
};

fn taskCompare(_: void, a: Task, b: Task) std.math.Order {
    return std.math.order(a.priority, b.priority);
}

const TaskQueue = std.PriorityQueue(Task, void, taskCompare);

pub fn main() !void {
    var gpa: std.heap.DebugAllocator(.{}) = .init;
    defer _ = gpa.deinit();

    var tasks = TaskQueue.init(gpa.allocator(), {});
    defer tasks.deinit();

    try tasks.add(.{ .name = "low", .priority = 100 });
    try tasks.add(.{ .name = "urgent", .priority = 1 });
    try tasks.add(.{ .name = "medium", .priority = 50 });

    while (tasks.removeOrNull()) |task| {
        std.debug.print("Processing: {s}\n", .{task.name});
    }
    // Output: urgent → medium → low
}
```

## Complete Example: Dijkstra's Algorithm

```zig
const NodeIndex = usize;
const Distances = []const u32;

fn dijkstraCmp(dist: Distances, a: NodeIndex, b: NodeIndex) std.math.Order {
    return std.math.order(dist[a], dist[b]);
}

const DijkstraPQ = std.PriorityQueue(NodeIndex, Distances, dijkstraCmp);

fn dijkstra(graph: anytype, start: NodeIndex, allocator: Allocator) ![]u32 {
    const n = graph.len();
    var dist = try allocator.alloc(u32, n);
    @memset(dist, std.math.maxInt(u32));
    dist[start] = 0;

    var pq = DijkstraPQ.init(allocator, dist);
    defer pq.deinit();
    try pq.add(start);

    while (pq.removeOrNull()) |u| {
        for (graph.neighbors(u)) |v| {
            const alt = dist[u] + graph.weight(u, v);
            if (alt < dist[v]) {
                dist[v] = alt;
                try pq.add(v);
            }
        }
    }
    return dist;
}
```

## How It Works

```
Binary Heap:
          1
       /     \
      3       2
     / \     / \
    7   8   5   4
   /
  9

Array representation: [1, 3, 2, 7, 8, 5, 4, 9]
Parent of i: (i-1)/2
Children of i: 2i+1, 2i+2
```

- `add()` — append to end, sift up: O(log n)
- `remove()` — swap root with last, sift down: O(log n)
- `peek()` — return root: O(1)
- `fromOwnedSlice()` — Floyd's algorithm: O(n)

## Gotchas

1. **`remove()` panics on empty queue** — use `removeOrNull()` if the queue might be empty.
2. **Iterator order is NOT priority order** — the iterator walks the heap array, which is not sorted. Use repeated `removeOrNull()` for priority order.
3. **`update()` is O(n)** — it must find the old value first. For frequently changing priorities, consider marking stale entries and pushing new ones.
4. **Comparator must be deterministic** — inconsistent ordering (e.g., based on pointer comparison) will break the heap invariant.
5. **`order` returns `std.math.Order`** — `.lt`, `.eq`, `.gt`. Not a bool comparison.
