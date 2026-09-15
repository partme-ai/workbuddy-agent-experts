# Build Mode

Zig provides four standard build modes, configured via `-Doptimize` or `b.standardOptimizeOption(.{})`.

## Quick Reference

| Mode | Flag | Safety Checks | Runtime Speed | Build Speed |
|------|------|---------------|---------------|-------------|
| **Debug** | (default) | ✅ All on | Slowest | Fastest |
| **ReleaseFast** | `-Doptimize=ReleaseFast` | ❌ Most off | Fastest | Slowest |
| **ReleaseSafe** | `-Doptimize=ReleaseSafe` | ✅ Safety on | Fast, less than ReleaseFast | Slower |
| **ReleaseSmall** | `-Doptimize=ReleaseSmall` | ❌ Most off | Slower | Slowest |

## Debug (default)

```bash
zig build               # Debug
zig build -Doptimize=Debug  # explicit
```

- All safety checks enabled: bounds checking, integer overflow, unwrap null, etc.
- No optimization (fastest compile, slowest runtime)
- Best for development and testing

## ReleaseFast

```bash
zig build -Doptimize=ReleaseFast
```

- Maximum optimization (`-O3` equivalent)
- Most safety checks disabled
- Assertions (`std.debug.assert`) are stripped
- Best for production deployment where safety is handled by tests

## ReleaseSafe

```bash
zig build -Doptimize=ReleaseSafe
```

- Full optimization while keeping safety checks
- Bounds checking, integer overflow detection, stack traces all remain
- Runtime performance slower than ReleaseFast but safer
- Best for production code that may encounter unexpected conditions

## ReleaseSmall

```bash
zig build -Doptimize=ReleaseSmall
```

- Optimizes for binary size (`-Oz` equivalent)
- Safety checks disabled
- Best for embedded systems, WebAssembly, or size-constrained deployments

## Build Mode Effects

### Safety Checks by Mode

| Check | Debug | ReleaseSafe | ReleaseFast | ReleaseSmall |
|-------|-------|-------------|-------------|--------------|
| Bounds checking | ✅ | ✅ | ❌ | ❌ |
| Integer overflow | ✅ | ✅ | ❌ | ❌ |
| Assertions | ✅ | ✅ | ❌ | ❌ |
| Stack traces | ✅ | ✅ | ❌ | ❌ |
| Debug allocator checks | ✅ | ✅ | ❌ | ❌ |
| `unreachable` detection | ✅ | ✅ | ❌ | ❌ |

### Runtime Behavior Differences

```zig
// This assertion is only checked in Debug and ReleaseSafe
std.debug.assert(x > 0);

// This overflow is only detected in Debug and ReleaseSafe
const sum = @addWithOverflow(u8, a, b);

// unreachable triggers a panic in Debug/ReleaseSafe
// In ReleaseFast/ReleaseSmall it becomes undefined behavior
if (condition) {
    // handle
} else {
    unreachable;
}
```

## Single Threaded Builds

```bash
zig build -Dsingle-threaded
```

- Disables thread-local storage
- Removes all thread-safety overhead from allocators
- Simplifies the runtime
- Required for WASI and some embedded targets
- Checkable at compile time:

```zig
if (@import("builtin").single_threaded) {
    // No thread safety needed
} else {
    // Thread-safe path
}
```

## Checking Build Mode at Compile Time

```zig
const builtin = @import("builtin");

switch (builtin.mode) {
    .Debug => { /* debug mode */ },
    .ReleaseFast => { /* fast mode */ },
    .ReleaseSafe => { /* safe mode */ },
    .ReleaseSmall => { /* small mode */ },
}

// In build.zig
const optimize = b.standardOptimizeOption(.{
    .preferred_optimize_mode = .ReleaseFast,
});
```

## Gotchas

1. **`std.debug.assert` vs `std.testing.expect`** — `assert` is stripped in ReleaseFast/ReleaseSmall; `expect` is always available (in tests).
2. **Unreachable behavior varies** — `unreachable` is checked in Debug/ReleaseSafe → panics on reach. In ReleaseFast/ReleaseSmall it's unchecked → undefined behavior.
3. **ReleaseSafe ≠ ReleaseFast + assertions** — ReleaseSafe keeps safety but also enables optimizations. It's not just "Debug with speed."
4. **Integer overflow is UB in ReleaseFast** — any overflow that could occur in production must be explicitly handled with `@addWithOverflow` or wrapping operators.
