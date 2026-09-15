---
name: zig-0-16
license: Apache-2.0
description: Up-to-date Zig 0.16.0 language and standard library skill. Use when writing, reviewing, debugging, or migrating Zig code, working with build.zig/build.zig.zon, std modules, comptime, C interop, and modern 0.16 APIs.
---

# Zig Language Reference (v0.16.0)

This skill covers the Zig 0.16.0 language and standard library. Use it when writing, reviewing, or migrating Zig code, working with build.zig / build.zig.zon, standard library modules, and comptime metaprogramming.

Zig evolves rapidly. Training data, blog posts, and many public examples are stale. This skill is the main Zig 0.16.0 aggregate skill for this repository: it condenses the official 0.16.0 language reference, the official std index, the Chinese Zig homepage, and the local offline reference set under `references/`.

## Capability Boundaries

### ✅ Strong Suits
1. Writing and optimizing Zig 0.16.0 code with standard library modules
2. Using the build.zig / build.zig.zon build system
3. Comptime metaprogramming, builtin functions, and type reflection
4. C interop: @cImport, linking, header management
5. Code review and migration: older versions → 0.16.0

### ⚠️ Requirements
1. Target version must be confirmed as 0.16.0 (run `zig version`)
2. Library-specific work (raylib/SDL3) should switch to the dedicated skill
3. Platform-specific APIs may require additional OS knowledge

### ❌ Out of Scope (with alternatives)
1. Game/graphics API development → use zig-raylib or zig-sdl3-bindings
2. Database/backend service development → use appropriate domain skill
3. Non-Zig language coding → use the corresponding language skill

## When to use this skill

Use this skill when the user needs to write, review, debug, or migrate Zig 0.16.0 code, or when working with build.zig / build.zig.zon, std modules, comptime, or C interop.

## Data Privacy

This skill does not collect, store, or transmit any user data. All code examples are for local development reference only.

## Official Positioning

From the Zig 0.16.0 docs and Chinese homepage, Zig is a general-purpose programming language and toolchain for building robust, optimal, and reusable software.

### Core design ideas
- No implicit control flow.
- No implicit memory allocation.
- No preprocessor and no macros.
- `comptime` makes type-driven programming and code generation first-class.
- Zig is both a language and a cross-platform toolchain for Zig, C, and C++ projects.

### Primary official sources
- [Language reference](https://ziglang.org/documentation/0.16.0/)
- [Introduction](https://ziglang.org/documentation/0.16.0/#Introduction)
- [Standard library index](https://ziglang.org/documentation/0.16.0/std/)
- [Chinese homepage](https://ziglang.org/zh-CN/)
- [Build system documentation](https://ziglang.org/learn/build-system/)
- [0.16.0 release notes](https://ziglang.org/download/0.16.0/release-notes.html)

## Quick Start

**Example invocations:**
```
Write an HTTP server in Zig 0.16 using std.http
Create a build.zig that depends on a third-party library
Review this Zig code for 0.16 compatibility issues
Migrate this Zig 0.14 project to 0.16
```

## Workflow

Step 1. **Confirm version** — Run `zig version` to verify the user is on 0.16.0

Step 2. **Review official reference** — Read the main skill body for the overall framework

Step 3. **Look up std modules** — Find the relevant module from the std index, then load the matching `references/` file

Step 4. **Use examples** — Load copyable code snippets from `examples/`

Step 5. **Handle migrations** — For legacy code, check the Removed Features and Breaking Changes sections

## Critical: How to use this skill

1. Confirm the user is targeting Zig 0.16.0 or wants modern Zig patterns.
2. Start here for language, build system, std modules, code review, or migration work.
3. Prefer local `references/*.md` when you need concrete examples or offline guidance.
4. Use the official links above for authority, API confirmation, and section names.
5. Switch to `zig-raylib` or `zig-sdl3-bindings` only for those library-specific workflows.

## Critical: Official 0.16.0 coverage map

The official Zig 0.16.0 language reference covers these major areas:

- Introduction and Zig Standard Library entry.
- Hello World, comments, doc comments, top-level docs, identifiers, values, literals, assignment, and destructuring.
- `test` declarations, doctests, leak reporting, test output, and `std.testing`.
- Integers, floats, operators, arrays, vectors, pointers, many-item pointers, slices, sentinel-terminated types, and optional pointers.
- `struct`, `enum`, `union`, `opaque`, tuples, anonymous literals, non-exhaustive enums, tagged unions, and result location semantics.
- Blocks, labels, `switch`, `while`, `for`, `if`, `defer`, `errdefer`, `unreachable`, and `noreturn`.
- Functions, methods, errors, optionals, casts, coercions, peer type resolution, and zero-bit types.
- `comptime`, generic data structures, builtin functions, atomics, async-related syntax history, and assembly.
- C interop related builtins such as `@cImport`, `@cInclude`, `@extern`, and `@export`.
- The Zig Build System, which points to the dedicated build-system docs.

## Critical: Standard library 0.16.0 coverage map

The official 0.16.0 std index exposes the modules most often needed for application work:

- Build and tooling: `std.Build`, `std.zig`, `std.zon`
- I/O and OS: `std.Io`, `std.fs`, `std.process`, `std.os`, `std.c`
- Memory and text: `std.heap`, `std.mem`, `std.fmt`, `std.ascii`, `std.unicode`, `std.base64`
- Data and networking: `std.http`, `std.json`, `std.Uri`, `std.net`
- Runtime services: `std.log`, `std.debug`, `std.testing`, `std.time`, `std.Tz`
- Algorithms and utilities: `std.math`, `std.hash`, `std.crypto`, `std.Random`, `std.sort`, `std.simd`
- Concurrency and reflection: `std.Thread`, `std.atomic`, `std.meta`
- Containers: `std.ArrayList`, `std.HashMap`, `std.ArrayHashMap`, `std.MultiArrayList`, `std.StaticStringMap`, `std.bit_set`, `std.PriorityQueue`

Use the official std index to confirm module names and the local `references/` folder for curated examples and practical notes.

## Critical: Removed Features Still Missing in 0.16

### `usingnamespace` - removed
```zig
// WRONG
pub usingnamespace @import("other.zig");

// CORRECT
const other = @import("other.zig");
pub const foo = other.foo;
```

### `async`/`await` - removed
These keywords are still not part of normal Zig 0.16 source code patterns. Do not suggest legacy async examples from old posts.

### `@fence` - removed
Use stronger atomic orderings or RMW operations instead.

## Critical: I/O API Rewrite

The `std.io` era patterns remain stale. Modern Zig uses `std.Io.Writer` and `std.Io.Reader` with explicit buffers and interface access.

### Writing
```zig
// WRONG - old API
const stdout = std.io.getStdOut().writer();
try stdout.print("Hello\n", .{});

// CORRECT - modern API
var buf: [4096]u8 = undefined;
var stdout_writer = std.fs.File.stdout().writer(&buf);
const stdout = &stdout_writer.interface;
try stdout.print("Hello\n", .{});
try stdout.flush();
```

### Reading
```zig
var buf: [4096]u8 = undefined;
var file_reader = file.reader(&buf);
const r = &file_reader.interface;

while (try r.takeDelimiter('\n')) |line| {
    // line does not include '\n'
}
```

### Fixed writer and reader
```zig
var out_buf: [256]u8 = undefined;
var w: std.Io.Writer = .fixed(&out_buf);
try w.print("Hello {s}", .{"world"});
const result = w.buffered();

var r: std.Io.Reader = .fixed("hello\nworld");
const first = (try r.takeDelimiter('\n')).?;
_ = first;
```

Deprecated names such as `BufferedWriter`, `GenericWriter`, `AnyWriter`, and `FixedBufferStream` should not be suggested for Zig 0.16 code.

## Critical: Build System

The official 0.16.0 docs describe the Zig Build System as a cross-platform, dependency-free way to declare project build logic in `build.zig`.

### Core workflow
- Run `zig init` or scaffold the project manually.
- Inspect available options with `zig build --help`.
- Put package metadata and dependencies in `build.zig.zon`.
- Use `std.Build` and module-based APIs in `build.zig`.

### Modern build pattern
```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const exe = b.addExecutable(.{
        .name = "app",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/main.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });

    b.installArtifact(exe);
}
```

### `root_module` is mandatory
```zig
// WRONG - removed field on addExecutable/addLibrary/addTest
b.addExecutable(.{
    .name = "app",
    .root_source_file = b.path("src/main.zig"),
});

// CORRECT
b.addExecutable(.{
    .name = "app",
    .root_module = b.createModule(.{
        .root_source_file = b.path("src/main.zig"),
    }),
});
```

### Module imports changed
```zig
// WRONG
exe.addModule("helper", helper_mod);

// CORRECT
exe.root_module.addImport("helper", helper_mod);
```

### Dependency modules
```zig
const dep = b.dependency("lib", .{
    .target = target,
    .optimize = optimize,
});
exe.root_module.addImport("lib", dep.module("lib"));
```

Compile-level methods like `exe.linkSystemLibrary()` and `exe.addCSourceFiles()` should generally move to `exe.root_module.*` based APIs in modern code.

## Critical: Container Initialization

Never suggest `.{}` for container initialization unless the type is documented to support it. For the common std containers and allocators, Zig 0.16 still expects `.empty` or `.init`.

```zig
// WRONG
var list: std.ArrayList(u32) = .{};
var gpa: std.heap.DebugAllocator(.{}) = .{};

// CORRECT
var list: std.ArrayList(u32) = .empty;
var map: std.AutoHashMapUnmanaged(u32, u32) = .empty;
var gpa: std.heap.DebugAllocator(.{}) = .init;
var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
```

### Naming changes that remain relevant
- `std.ArrayListUnmanaged` -> `std.ArrayList`
- `std.heap.GeneralPurposeAllocator` -> `std.heap.DebugAllocator`

### `std.BoundedArray` replacement
```zig
var buffer: [8]i32 = undefined;
var stack = std.ArrayList(i32).initBuffer(&buffer);
```

## Critical: Format Strings

Some custom formatters now require `{f}`:

```zig
// WRONG
std.debug.print("{}", .{std.zig.fmtId("x")});

// CORRECT
std.debug.print("{f}", .{std.zig.fmtId("x")});
```

Modern format methods also use writer-based signatures:

```zig
pub fn format(self: @This(), writer: *std.Io.Writer) std.Io.Writer.Error!void {
    _ = self;
    _ = writer;
}
```

## Official Zig 0.16 workflow

### Learn and bootstrap
- Read the Introduction section first.
- Use `zig version` to confirm the compiler is `0.16.0`.
- Use the Chinese homepage positioning when explaining Zig to users: robust, optimal, reusable.

### Build, run, test
```bash
zig build
zig build run
zig test src/main.zig
zig build test
```

### Chinese homepage sample pattern
```zig
const std = @import("std");
const parseInt = std.fmt.parseInt;

test "parse integers" {
    const input = "123 67 89,99";
    const gpa = std.testing.allocator;

    var list: std.ArrayList(u32) = .empty;
    defer list.deinit(gpa);

    var it = std.mem.tokenizeAny(u8, input, " ,");
    while (it.next()) |num| {
        const n = try parseInt(u32, num, 10);
        try list.append(gpa, n);
    }

    const expected = [_]u32{ 123, 67, 89, 99 };
    for (expected, list.items) |exp, actual| {
        try std.testing.expectEqual(exp, actual);
    }
}
```

## Breaking Changes Carried Forward from Recent Releases

These patterns are still useful for 0.16 review and migration work:

### `@branchHint` replaces `@setCold`
```zig
// WRONG
@setCold(true);

// CORRECT
@branchHint(.cold);
```

### `@export` takes a pointer
```zig
// WRONG
@export(foo, .{ .name = "bar" });

// CORRECT
@export(&foo, .{ .name = "bar" });
```

### Typed inline asm clobbers
```zig
// WRONG
: "rcx", "r11"

// CORRECT
: .{ .rcx = true, .r11 = true }
```

### Decl literals
```zig
const S = struct {
    x: u32,
    const default: S = .{ .x = 0 };
    fn init(v: u32) S { return .{ .x = v }; }
};

const a: S = .default;
const b: S = .init(42);
```

### Labeled switch
```zig
state: switch (initial) {
    .idle => continue :state .running,
    .running => if (done) break :state result else continue :state .running,
    .error => return error.Failed,
}
```

### Non-exhaustive enum switch
```zig
switch (value) {
    .a, .b => {},
    else => {},  // other named tags
    _ => {},     // unnamed integer values
}
```

## Quick Fixes

| Error | Fix |
|-------|-----|
| `no field 'root_source_file'` | Use `root_module = b.createModule(.{...})` in `addExecutable`/`addLibrary`/`addTest` |
| `use of undefined value` | Arithmetic on `undefined` is illegal; initialize data before use |
| `type 'f32' cannot represent integer` | Use a float literal such as `123_456_789.0` |
| `std.io` examples don't compile | Use `std.Io` writer/reader patterns with explicit buffers |
| Old container init example uses `.{}` | Prefer `.empty` or `.init` depending on the type |
| `ambiguous format string` | Use `{f}` for custom formatter output |
| `sanitize_c = true` no longer works | Use the modern enum-style sanitize configuration from recent Zig releases |
| `std.fifo.LinearFifo` examples fail | Prefer `std.Io.Reader` or `std.Io.Writer` based streaming patterns |
| `posix.sendfile` examples fail | Use file writer APIs such as `.sendFileAll()` |
| `std.fmt.Formatter` examples fail | Use `std.fmt.Alt` in modern code |
| `fmtSliceEscapeLower`/`fmtSliceEscapeUpper` missing | Use `std.ascii.hexEscape(bytes, .lower/.upper)` |
| User's zig version is not 0.16.0 | Confirm version, then guide to upgrade or switch skills |
| User asks about raylib/SDL3 API | Guide to use zig-raylib / zig-sdl3-bindings |
| Code from old blog/tutorial with unknown version | Use Quick Fixes table to check each compilation error pattern |
| Need module-specific details | Load the matching local `references/*.md` file |
| Build-system API uncertainty | Check both local `std-build.md` and the official build-system docs |

## Offline Examples

Use the local `examples/` directory when you need copyable snippets quickly or cannot rely on live web access:

- `examples/quickstart-workflows.md` - starter project, tests, JSON, process, HTTP, review checklist
- `examples/build-zig-zon-workflows.md` - package metadata, dependencies, executable and library layouts
- `examples/comptime-patterns.md` - reflection, generic helpers, generated types, inline loops
- `examples/c-interop-workflows.md` - `@cImport`, exported APIs, static libraries, headers
- `examples/std-thread-patterns.md` - spawn and join, mutex, wait group, atomic counter patterns

## Official Distillations

Use `docs/official/` when you need offline distilled versions of the official Zig 0.16 pages themselves rather than topic cards:

- `docs/official/official-sources.md` - source index and navigation
- `docs/official/official-language-reference-0.16.md` - language reference coverage map
- `docs/official/official-introduction-0.16.md` - introduction distillation
- `docs/official/official-std-index-0.16.md` - standard library index distillation
- `docs/official/official-zh-cn-home-0.16.md` - Chinese homepage distillation

## Language References

Load these references when working with core language features:

### Code Style
- **[Style Guide](references/style-guide.md)** - Official Zig naming conventions, whitespace rules, doc comment guidance, redundancy avoidance, `zig fmt`

### Language Basics & Built-ins
- **[Language Basics](references/language.md)** - Core language: types, control flow, error handling, optionals, structs, enums, unions, pointers, slices, comptime, functions
- **[Built-in Functions](references/builtins.md)** - All `@` built-ins: casts, arithmetic, bit ops, memory, atomics, introspection, SIMD, C interop

## Standard Library References

Load these references when working with specific modules:

### Memory & Slices
- **[std.mem](references/std-mem.md)** - Slice search or compare, split or tokenize, alignment, endianness, byte conversion

### Text & Encoding
- **[std.fmt](references/std-fmt.md)** - Format strings, integer or float parsing, custom formatters, `{f}` notes
- **[std.ascii](references/std-ascii.md)** - ASCII classification, case conversion, case-insensitive comparison
- **[std.unicode](references/std-unicode.md)** - UTF-8 and UTF-16 handling, codepoint iteration, validation
- **[std.base64](references/std-base64.md)** - Base64 encoding and decoding

### Math & Random
- **[std.math](references/std-math.md)** - Floating-point ops, trig, checked arithmetic, constants
- **[std.Random](references/std-random.md)** - PRNGs, random integers or floats, shuffle, distributions
- **[std.hash](references/std-hash.md)** - Hash functions, checksums, auto-hashing

### SIMD & Vectorization
- **[std.simd](references/std-simd.md)** - SIMD vector utilities and patterns

### Time & Timing
- **[std.time](references/std-time.md)** - Timestamps, timers, epoch conversions, calendar helpers
- **[std.Tz](references/std-tz.md)** - Timezone database parsing and timezone handling

### Sorting & Searching
- **[std.sort](references/std-sort.md)** - Sorting algorithms, binary search, min and max helpers

### Core Data Structures
- **[std.ArrayList](references/std-arraylist.md)** - Dynamic arrays and buffer-backed patterns
- **[std.HashMap / AutoHashMap](references/std-hashmap.md)** - Hash maps, string maps, ordered maps
- **[std.ArrayHashMap](references/std-array-hash-map.md)** - Insertion-order preserving maps
- **[std.MultiArrayList](references/std-multi-array-list.md)** - Struct-of-arrays storage
- **[std.SegmentedList](references/std-segmented-list.md)** - Stable pointers and arena-friendly storage
- **[std.DoublyLinkedList / SinglyLinkedList](references/std-linked-list.md)** - Intrusive linked lists
- **[std.PriorityQueue](references/std-priority-queue.md)** - Binary heap based queues
- **[std.PriorityDequeue](references/std-priority-dequeue.md)** - Double-ended priority extraction
- **[std.Treap](references/std-treap.md)** - Balanced tree with ordered keys
- **[std.bit_set](references/std-bit-set.md)** - Static and dynamic bit sets
- **[std.BufMap / BufSet](references/std-buf-map.md)** - String-owning maps and sets
- **[std.StaticStringMap](references/std-static-string-map.md)** - Compile-time string lookup
- **[std.enums](references/std-enums.md)** - EnumSet, EnumMap, EnumArray

### Allocators
- **[std.heap](references/std-allocators.md)** - Allocator selection guide and custom allocator patterns

### I/O & Files
- **[std.Io](references/std-io.md)** - Reader and Writer API patterns, buffered I/O, streaming, binary data
- **[std.fs](references/std-fs.md)** - Files, directories, iteration, atomic writes, paths
- **[std.tar](references/std-tar.md)** - Tar archive handling
- **[std.zip](references/std-zip.md)** - ZIP archive handling
- **[std.compress](references/std-compress.md)** - Compression and decompression modules

### Networking
- **[std.http](references/std-http.md)** - HTTP client or server patterns, TLS, compression
- **[std.net](references/std-net.md)** - Socket basics, address parsing, DNS
- **[std.Uri](references/std-uri.md)** - URI parsing, percent-encoding, relative resolution

### Process Management
- **[std.process](references/std-process.md)** - Child process spawning, environment, arguments, exec

### OS-Specific APIs
- **[std.os](references/std-os.md)** - Platform-specific APIs, syscalls, Windows or WASI access
- **[std.c](references/std-c.md)** - C ABI types and libc bindings

### Concurrency
- **[std.Thread](references/std-thread.md)** - Thread spawning, mutexes, rw locks, conditions, semaphores
- **[std.atomic](references/std-atomic.md)** - Atomic operations, orderings, compare-and-swap

### Patterns & Best Practices
- **[Zig Patterns](references/patterns.md)** - Practical patterns for writing and reviewing Zig code
- **[Code Review](references/code-review.md)** - Review checklist and stale-pattern detection

## Audience

| User Type | Usage |
|-----------|-------|
| **Zig beginners** | Write basic code and learn 0.16 API patterns |
| **Migration users** | Migrate from older versions by following the Critical sections |
| **Experienced developers** | Deep-dive into std modules via references/ and copy patterns from examples/ |

Customization options:
- Specify output format (full code / snippet / diff)
- Request a specific module focus (e.g., build.zig only or I/O only)

## Gotchas

1. **Always confirm the version first** — Verify `zig version` is 0.16.0 before giving advice; API differences cause compilation errors
2. **build.zig requires root_module** — `addExecutable`/`addLibrary` no longer accept `root_source_file`; use `root_module = b.createModule(...)`
3. **std.Io pattern is mandatory** — Old `std.io` patterns (e.g. `std.io.getStdOut().writer()`) do not compile under 0.16.0
4. **Container init does not use `.{ }`** — ArrayList/HashMap must use `.empty` or `.init`
5. **Format strings need `{f}`** — Custom formatter output requires `{f}` instead of `{}`
6. **Prefer offline references** — Use `references/` local files over web search to ensure 0.16.0 consistency
7. **Do not assume the latest compiler** — If the user's version is not 0.16.0, guide them to upgrade or switch skills

## FAQ

**Q: How does this skill differ from `zig-0.15`?**
A: `zig-0-16` is the primary skill covering the latest stable 0.16.0 release. `zig-0.15` is retained as a legacy compatibility reference.

**Q: What if example code fails to compile?**
A: Verify `zig version` outputs 0.16.0. If the version differs, some APIs may have changed. Use the Quick Fixes table to diagnose.

**Q: How do I find a specific std module?**
A: Look up the module name in the Standard Library References section, then load the matching `references/*.md` file.

**Q: Can I use this offline?**
A: Yes. All references/ and examples/ files are local copies and work without internet access.

**Q: Does this skill collect my code?**
A: No. This skill is a pure documentation reference and does not collect any user data.

### Serialization
- **[std.json](references/std-json.md)** - JSON parsing, serialization, dynamic values, streaming
- **[std.zon](references/std-zon.md)** - ZON parsing and serialization for `build.zig.zon` and configs

### Testing & Debug
- **[std.testing](references/std-testing.md)** - Unit test assertions and utilities
- **[std.debug](references/std-debug.md)** - Panic, assert, stack traces, hex dump
- **[std.log](references/std-log.md)** - Scoped logging and configurable levels

### Metaprogramming
- **[Comptime Reference](references/comptime.md)** - Comptime fundamentals, reflection, generic patterns
- **[std.meta](references/std-meta.md)** - Type introspection, field iteration, stringToEnum, generic programming

### Compiler Utilities
- **[std.zig](references/std-zig.md)** - AST parsing, tokenization, source analysis, linters, formatters, ZON parsing

### Security & Cryptography
- **[std.crypto](references/std-crypto.md)** - Hashing, AEAD, signatures, key exchange, password hashing, secure random

### Build System
- **[std.Build](references/std-build.md)** - Build system, modules, dependencies, steps, options, testing, C or C++ integration

### Interoperability
- **[C Interop](references/c-interop.md)** - Exporting C-compatible APIs, calling conventions, libraries, headers, module maps
