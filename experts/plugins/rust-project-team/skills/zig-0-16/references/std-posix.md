# std.posix

POSIX system call API — low-level OS interface for file I/O, processes, signals, sockets, and terminal control. Used by `std.fs` and `std.process` internally.

## Quick Reference

```zig
const std = @import("std");
const posix = std.posix;
```

## File I/O

### Open and Close

```zig
const fd = try posix.open("file.txt", .{ .RDONLY = true }, 0);
defer posix.close(fd);

// With flags
const fd = try posix.openZ("/path/file\0", .{
    .WRONLY = true,
    .CREAT = true,
    .TRUNC = true,
}, 0o644);
defer posix.close(fd);
```

### Read and Write

```zig
var buf: [4096]u8 = undefined;
const n = try posix.read(fd, &buf);
const written = try posix.write(fd, "hello");

// Scatter/gather I/O
const iov = [posix.iovec]{ .{ .iov_base = &buf, .iov_len = buf.len } };
const nread = try posix.readv(fd, &iov);

// Positioned I/O (no lseek needed)
const n = try posix.pread(fd, &buf, offset);
const n = try posix.pwrite(fd, "data", offset);
```

### Directory Operations

```zig
posix.chdir("/path");
posix.symlink("/src", "/dst") catch {};
posix.link("/src", "/dst") catch {};
posix.unlink("/tmp/file") catch {};
posix.rename("/old", "/new") catch {};
```

## Process Management

```zig
posix.exit(0);
const pid = posix.getpid();
const ppid = posix.getppid();

// Execute a program
try posix.execveZ("/usr/bin/ls\0", &[_?[*:0]const u8]{ null }, &[_?[*:0]const u8]{ null });

// Kill a process
posix.kill(pid, posix.SIG.TERM) catch {};
```

## File Operations

```zig
// Duplicate file descriptor
const new_fd = try posix.dup(fd);
const exact_fd = try posix.dup2(fd, 5);

// Truncate
try posix.ftruncate(fd, 1024);

// Change permissions
try posix.fchmod(fd, 0o644);

// Change ownership
try posix.fchown(fd, uid, gid) catch {};
```

## Sockets and Networking

```zig
const sock = try posix.socket(posix.AF.INET, posix.SOCK.STREAM, 0);
defer posix.close(sock);

try posix.connect(sock, &address, address.getOsSockLen());
try posix.bind(sock, &address, address.getOsSockLen());
try posix.listen(sock, 128);

var client_addr: posix.sockaddr = undefined;
var addr_len: posix.socklen_t = @sizeOf(posix.sockaddr);
const client = try posix.accept(sock, &client_addr, &addr_len);

// Send/recv
const sent = try posix.send(client, "data", 0);
var buf: [1024]u8 = undefined;
const n = try posix.recv(client, &buf, 0);
```

## Signal Handling

```zig
const sig_action = posix.Sigaction{
    .handler = .{ .handler = handleSignal },
    .mask = posix.empty_sigset,
    .flags = 0,
};
try posix.sigaction(posix.SIG.INT, &sig_action, null);

// Block signals
var mask = posix.empty_sigset;
posix.sigaddset(&mask, posix.SIG.TERM);
try posix.sigprocmask(posix.SIG_BLOCK, &mask, null);

// Raise signal
posix.raise(posix.SIG.USR1) catch {};
```

## System Information

```zig
// Working directory
var cwd_buf: [posix.PATH_MAX]u8 = undefined;
const cwd = try posix.getcwd(&cwd_buf);

// Random bytes
var rand: [32]u8 = undefined;
try posix.getrandom(&rand, 0);

// Resource limits
var rl: posix.rlimit = undefined;
try posix.getrlimit(posix.RLIMIT.NOFILE, &rl);
```

## Terminal I/O

```zig
var term: posix.termios = undefined;
try posix.tcgetattr(fd, &term);
// Modify terminal settings...
try posix.tcsetattr(fd, .SANOW, &term);
```

## Error Handling

```zig
// Errno constants
posix.E.ACCES     // Permission denied
posix.E.AGAIN     // Resource temporarily unavailable
posix.E.NOENT     // No such file or directory
posix.E.INTR      // Interrupted system call
posix.E.PIPE      // Broken pipe
posix.E.NOMEM     // Cannot allocate memory
// ... 100+ errno values

// Most functions return standard error sets
// .{} for ReadError, OpenError, WriteError, etc.
```

## Key Types

```zig
posix.fd_t         // file descriptor (i32 or similar)
posix.pid_t        // process ID
posix.uid_t        // user ID
posix.gid_t        // group ID
posix.mode_t       // file permissions
posix.off_t        // file offset
posix.iovec        // scatter/gather I/O buffer
posix.Stat         // file metadata (stat)
posix.sockaddr     // socket address
posix.timespec     // nanosecond time
posix.timeval      // microsecond time
```

## Gotchas

1. **Not portable** — POSIX APIs are platform-dependent. Use `std.fs` and `std.process` for portable code.
2. **`open` vs `openZ`** — `open` takes `[]const u8`; `openZ` takes `[:0]const u8` (C string). Use `openZ` for paths from C interop.
3. **Errno is wrapped** — `posix.E.*` constants are Zig enums, not raw errno values.
4. **Signal safety** — only async-signal-safe functions can be called from signal handlers. Most `posix.*` functions are NOT safe to call from handlers.
5. **File descriptors are managed** — use `defer posix.close(fd)` immediately after open to prevent leaks.
