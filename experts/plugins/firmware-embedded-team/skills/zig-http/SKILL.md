---
name: zig-http
license: Apache-2.0
description: Zig HTTP 网络编程技能。涉及 std.http 的客户端请求、服务端实现、WebSocket、TLS、连接池和压缩。在需要发起 HTTP 请求或搭建 HTTP 服务端时调用。
---

# Zig HTTP 网络编程

> 基于 std.http 的客户端与服务端开发（Zig 0.16.0）。

## Capability Boundaries

### ✅ 强项
1. HTTP 客户端请求（GET/POST/PUT/DELETE）
2. 自定义请求头、请求体、查询参数
3. HTTP 服务端搭建与路由
4. WebSocket 客户端与服务端
5. TLS/HTTPS 连接
6. 连接池管理与压缩

### ⚠️ 前置要求
1. 确认 Zig 版本（`zig version`）
2. 如需 HTTPS 需系统有 CA 证书

### ❌ 不适用范围
1. 非 HTTP 网络编程 → 使用 `zig-0.16` 的 std.net
2. Zig 语言基础 → 使用 `zig-0.16` 技能

## 何时使用

- "帮我写一个 HTTP 客户端"
- "如何搭建一个 HTTP 服务器？"
- "用 Zig 调用 REST API"

## Data Privacy

本技能不收集、存储或传输任何用户数据。

## Workflow

步骤 1. **初始化 Client** — `std.http.Client{ .allocator = allocator }`
步骤 2. **配置请求** — URL、方法、头、请求体
步骤 3. **发送请求** — `client.fetch()` 或底层 API
步骤 4. **处理响应** — 状态码、响应体
步骤 5. **资源清理** — `client.deinit()`

## HTTP 客户端

### 快速 GET
```zig
var client: std.http.Client = .{ .allocator = allocator };
defer client.deinit();

const result = try client.fetch(.{
    .location = .{ .url = "https://api.example.com/data" },
});
std.debug.print("Status: {d}\n", .{@intFromEnum(result.status)});
```

### GET 并读取响应体
```zig
var body_buf: [65536]u8 = undefined;
var body_writer: std.Io.Writer = .fixed(&body_buf);

const result = try client.fetch(.{
    .location = .{ .url = "https://api.example.com/data" },
    .response_writer = &body_writer,
});
const body = body_writer.buffered();
std.debug.print("Body: {s}\n", .{body});
```

### POST JSON
```zig
const payload = "{\"key\": \"value\"}";
var buf: [4096]u8 = undefined;
var body_writer: std.Io.Writer = .fixed(&buf);

const result = try client.fetch(.{
    .location = .{ .url = "https://api.example.com/submit" },
    .method = .POST,
    .payload = payload,
    .response_writer = &body_writer,
    .headers = &.{
        .{ .name = "Content-Type", .value = "application/json" },
    },
});
```

### 带查询参数
```zig
var uri = std.Uri.parse("https://api.example.com/search")?;
uri.query = "q=zig&limit=10";

const result = try client.fetch(.{ .location = .{ .uri = uri } });
```

### 自定义请求头
```zig
const result = try client.fetch(.{
    .location = .{ .url = "https://api.example.com/protected" },
    .headers = &.{
        .{ .name = "Authorization", .value = "Bearer token123" },
        .{ .name = "Accept", .value = "application/json" },
    },
});
```

### 文件上传（multipart）
```zig
var form = std.http.Client.Fetch.Form.init(allocator);
defer form.deinit();
try form.field("name", "value");
try form.field("file", file_contents, .{ .filename = "data.txt" });

const result = try client.fetch(.{
    .location = .{ .url = "https://api.example.com/upload" },
    .method = .POST,
    .form = form,
});
```

### 底层请求（更细粒度控制）
```zig
var req = try client.request(.GET, uri, .{}, .{});
defer req.deinit();

// 发送请求头
try req.send(.{});

// 发送请求体（可选）
try req.writeAll("body data");

// 开始读取响应
try req.finish();
try req.wait();

// 读取响应体
var buf: [4096]u8 = undefined;
var reader_writer: std.Io.Writer = .fixed(&buf);
try req.reader().?.readAllWriter(&reader_writer);
```

### 连接池
```zig
try client.pool.enable();  // 启用连接池
// 多个请求复用连接
for (urls) |url| {
    const result = try client.fetch(.{ .location = .{ .url = url } });
    _ = result;
}
```

## HTTP 服务端

### 基础服务端
```zig
pub fn main() !void {
    var gpa: std.heap.DebugAllocator(.{}) = .init;
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    var server = std.http.Server.init(allocator, .{
        .reuse_port = true,
    });
    defer server.deinit();

    const addr = try std.net.Address.parseIp("127.0.0.1", 8080);
    try server.listen(addr);

    while (true) {
        var response_buf: [65536]u8 = undefined;
        var req = try server.accept(.{ .response_buffer = &response_buf });
        defer req.deinit();

        // 响应 Hello World
        try req.respond("Hello, World!\n", .{});
    }
}
```

### 路由分发
```zig
while (true) {
    var buf: [65536]u8 = undefined;
    var req = try server.accept(.{ .response_buffer = &buf });
    defer req.deinit();

    const url = req.request.target;
    if (std.mem.eql(u8, url, "/api/hello")) {
        try req.respond("{\"msg\": \"hello\"}", .{ .content_type = .json });
    } else if (std.mem.eql(u8, url, "/api/status")) {
        try req.respond("{\"status\": \"ok\"}", .{ .content_type = .json });
    } else {
        try req.respond("Not Found", .{ .status = .not_found });
    }
}
```

### JSON 响应
```zig
const body = "{\"name\": \"server\", \"version\": \"1.0\"}";
try req.respond(body, .{ .content_type = .json });
```

### 读取请求体
```zig
var req_body: [4096]u8 = undefined;
const body_len = try req.readAll(&req_body);
const body = req_body[0..body_len];
// 处理 body...
try req.respond("OK", .{});
```

## WebSocket

```zig
// 服务端升级到 WebSocket
var ws = try req.upgradeToWebSocket(.{});
defer ws.deinit();

while (true) {
    const frame = try ws.readFrame() orelse break;
    std.debug.print("Received: {s}\n", .{frame.payload});
    try ws.writeFrame("echo: " ++ frame.payload);
}
```

## Gotchas

1. **std.http 在 0.16 中是实验性的** — API 可能在未来版本变化
2. **Client 必须 deinit** — `client.deinit()` 释放连接池和资源
3. **响应体大小限制** — `fetch()` 默认不限制大小，但自行提供固定 buffer 时注意溢出
4. **HTTPS 需要系统 CA** — 在容器或无 CA 的环境中可能需要配置 `server.ca_bundle`
5. **Server.listen 的 addr** — IPv4 用 `127.0.0.1`，IPv6 用 `[::1]`

## FAQ

**Q：如何设置超时？**
A：使用底层 API（`client.request` + `req.wait()`）可以控制超时。`fetch()` 高层 API 暂不支持超时。

**Q：最大并发连接数？**
A：默认 128。启用连接池后自动管理复用，不显式限制。

**Q：支持 HTTP/2 吗？**
A：std.http 目前仅支持 HTTP/1.1。HTTP/2 支持计划中。
