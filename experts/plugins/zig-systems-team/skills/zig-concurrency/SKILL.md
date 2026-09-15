---
name: zig-concurrency
license: Apache-2.0
description: Zig 并发编程技能。涉及 std.Thread 的线程创建、同步原语（Mutex、RwLock、Condition、Semaphore、WaitGroup）、线程池和原子操作。在需要多线程或并行计算时调用。
---

# Zig 并发编程

> 基于 std.Thread 和 std.atomic 的并发原语（Zig 0.16.0）。

## Capability Boundaries

### ✅ 强项
1. 线程创建与管理（spawn、join、detach）
2. 同步原语（Mutex、RwLock、Condition、Semaphore、ResetEvent、WaitGroup）
3. 线程池（Thread.Pool）用于并行任务
4. 原子操作（std.atomic.Value）
5. 常见并发模式（生产者-消费者、工作队列）

### ⚠️ 前置要求
1. 确认 Zig 版本（`zig version`）
2. 理解基本并发概念（竞态条件、死锁）

### ❌ 不适用范围
1. 异步 I/O → 使用 `zig-http` 或 `zig-0.16` 的 std.Io
2. 非并发场景 → 使用 `zig-0.16` 技能

## 何时使用

- "多线程处理数据"
- "并行执行多个任务"
- "线程安全的共享状态"

## Data Privacy

本技能不收集、存储或传输任何用户数据。

## Workflow

步骤 1. **识别并发需求** — CPU 密集 / I/O 等待 / 并行计算？
步骤 2. **选择原语** — 线程 / 线程池 / 原子操作？
步骤 3. **实现同步** — Mutex / RwLock / WaitGroup
步骤 4. **测试正确性** — 竞态条件、死锁检查

## 模块总览

```zig
std.Thread                  // 线程创建与管理
std.Thread.Mutex            // 互斥锁
std.Thread.Mutex.Recursive  // 可重入互斥锁
std.Thread.RwLock           // 读写锁
std.Thread.Condition        // 条件变量
std.Thread.Semaphore        // 计数信号量
std.Thread.ResetEvent       // 布尔事件标志（阻塞式）
std.Thread.WaitGroup        // 等待多任务完成
std.Thread.Pool             // 线程池
std.Thread.Futex            // 底层 futex（高级）
std.atomic.Value(T)         // 原子类型包装
```

## 线程创建

### 基本线程
```zig
fn worker(id: usize) void {
    std.debug.print("Worker {d}\n", .{id});
}

const thread = try std.Thread.spawn(.{}, worker, .{42});
thread.join();  // 等待完成
```

### 带分配器配置
```zig
const thread = try std.Thread.spawn(.{ .allocator = allocator }, worker, .{42});
defer thread.join();
```

### 分离线程（不 join）
```zig
const thread = try std.Thread.spawn(.{}, worker, .{1});
thread.detach();  // 线程自动清理
```

## 同步原语

### Mutex（互斥锁）
```zig
var mutex: std.Thread.Mutex = .{};
var shared: i32 = 0;

fn increment() void {
    mutex.lock();
    defer mutex.unlock();
    shared += 1;
}
```

### RwLock（读写锁）
```zig
var rwlock: std.Thread.RwLock = .{};
var data: i32 = 0;

fn reader() void {
    rwlock.lockShared();
    defer rwlock.unlockShared();
    _ = data;  // 可并发读
}

fn writer() void {
    rwlock.lock();
    defer rwlock.unlock();
    data += 1;  // 独占写
}
```

### Condition（条件变量）
```zig
var mutex: std.Thread.Mutex = .{};
var cond: std.Thread.Condition = .{};
var ready: bool = false;

fn waiter() void {
    mutex.lock();
    defer mutex.unlock();
    while (!ready) {
        cond.wait(&mutex);  // 等待通知
    }
}

fn notifier() void {
    mutex.lock();
    defer mutex.unlock();
    ready = true;
    cond.signal();  // 或 cond.broadcast() 通知所有等待者
}
```

### Semaphore（信号量）
```zig
var sem = std.Thread.Semaphore{ .permits = 3 }; // 最多 3 个并发

fn worker() void {
    sem.wait();   // 获取许可
    defer sem.post();  // 释放许可
    // 执行工作...
}
```

### WaitGroup
```zig
var wg: std.Thread.WaitGroup = .{};
wg.reset();  // 初始化计数器为 0

fn worker(wg: *std.Thread.WaitGroup) void {
    defer wg.finish();
    // 执行工作
}

// 启动 5 个任务
wg.start();  // +1
const t1 = try std.Thread.spawn(.{}, worker, .{&wg});
wg.start();  // +1
const t2 = try std.Thread.spawn(.{}, worker, .{&wg});
wg.wait();   // 等待所有 finish()
```

### ResetEvent
```zig
var event: std.Thread.ResetEvent = .{};

fn waiter() void {
    event.wait();  // 阻塞直到被设置
}

fn setter() void {
    // ... 准备工作
    event.set();  // 通知等待者
}
```

## 线程池

```zig
var pool: std.Thread.Pool = .{};
try pool.init(.{ .max_threads = 4 });
defer pool.deinit();

// 提交任务
for (0..100) |i| {
    try pool.spawn(worker, .{i});
}
// pool.deinit() 等待所有任务完成
```

## 原子操作

```zig
var counter: std.atomic.Value(u64) = .{ .raw = 0 };

// 原子递增
_ = counter.fetchAdd(1, .acq_rel);

// 原子加载/存储
const val = counter.load(.acquire);
counter.store(42, .release);

// CAS（比较并交换）
const prev = counter.cmpxchgWeak(42, 100, .acq_rel, .acquire);
```

### 原子顺序
```zig
// 从弱到强
.monotonic    // 仅保证原子性，无同步语义
.acquire      // 读取后所有后续操作可见
.release      // 写入前所有操作已完成
.acq_rel      // acquire + release
.seq_cst      // 全局顺序一致（默认）
```

## 常见模式

### 生产者-消费者
```zig
const Queue = struct {
    items: std.ArrayList(i32),
    mutex: std.Thread.Mutex = .{},
    cond: std.Thread.Condition = .{},
    done: bool = false,
};

fn producer(q: *Queue) void {
    for (0..10) |i| {
        q.mutex.lock();
        q.items.append(@intCast(i));
        q.cond.signal();
        q.mutex.unlock();
    }
    q.mutex.lock();
    q.done = true;
    q.cond.broadcast();
    q.mutex.unlock();
}

fn consumer(q: *Queue) void {
    q.mutex.lock();
    while (!q.done or q.items.items.len > 0) {
        while (q.items.items.len == 0 and !q.done)
            q.cond.wait(&q.mutex);
        if (q.items.popOrNull()) |item| { /* 处理 */ }
    }
    q.mutex.unlock();
}
```

## Gotchas

1. **Zig 线程不返回值** — 线程函数是 `fn(Args) void`，结果通过共享内存传递
2. **Mutex 不可复制** — 使用指针传递 `*std.Thread.Mutex`
3. **条件变量的虚假唤醒** — `cond.wait()` 返回后必须重新检查条件（用 `while` 而非 `if`）
4. **`pool.spawn` 可能阻塞** — 线程池满时 `spawn` 会等待空闲线程
5. **`std.Thread.spawn` 的配置参数** — 第一个参数是 `.{}`（默认配置），可设置 `stack_size` 等
6. **`defer` 是解锁的最佳实践** — `mutex.lock()` 后立即 `defer mutex.unlock()` 防止遗漏

## FAQ

**Q：什么时候用 Mutex vs RwLock？**
A：读多写少用 RwLock（读者可并发），读写比例接近或用 Mutex（实现简单，无锁竞争开销）。

**Q：线程池大小怎么设置？**
A：CPU 密集型用 `std.Thread.getCpuCount()` 或手动设为核数；I/O 密集型可以设更大（如 4×核数）。

**Q：`std.Thread.spawn` 和 `pool.spawn` 区别？**
A：前者创建独立线程，适合少量长期任务；后者交给线程池复用线程，适合大量短任务。
