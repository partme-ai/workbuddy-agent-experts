# Zig Migration Test Categories

## Source parity

Losslessly represent a Java test and compare its result with Java. Preserve
case identity, input, exact assertion, state, side effect, and cleanup.

## Allocator and lifetime

Test allocation ownership, deinit responsibility, partial initialization,
`errdefer`, arena lifetime, borrowed slices, aliases, and leak detection with
`std.testing.allocator` or the repository's deterministic allocator probe.

## Error contracts

Use `expectError` plus assertions over structured diagnostics and state. Generic
“returned an error” checks are insufficient when Java distinguishes categories
or exposes details.

## Build, comptime, ABI, and targets

Test public imports, generated declarations, compile failures where contractual,
optimization modes, target-specific branches, layout/alignment, exported names,
integer widths, endian behavior, and foreign allocator boundaries.

## Lifecycle and concurrency

Use deterministic barriers, channels, injected clocks, and controlled schedulers
instead of fixed sleeps. Test ordering, cancellation, shutdown, exactly-once
cleanup, bounded queues, atomics, and races.

## Non-functional and host

Use fuzz/property tests for untrusted parsers, load/soak for resource growth,
benchmarks for performance claims, and real services/libraries/targets for host
claims. None substitutes for functional parity.
