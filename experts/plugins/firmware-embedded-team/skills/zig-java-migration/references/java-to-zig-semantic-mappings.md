# Java-to-Zig Semantic Mappings

Use this as a decision checklist, not a mechanical replacement table. Record
the exact source and target symbols plus observable contract in the semantic
ledger.

| Java mechanism | Zig direction | Required verification |
|---|---|---|
| class / record | struct with explicit methods and invariants | constructors, equality, mutation, ownership |
| interface | comptime generic, function table, or tagged union | dispatch set, object safety equivalent, errors |
| enum with fields | tagged union or enum plus payload type | names, numeric/protocol values, exhaustive handling |
| nullable `T` | `?T` | absent/default/serialized-null distinction |
| checked exception | explicit error set and error union | exact category, payload, cause/diagnostics, side effects |
| unchecked exception | explicit error, assertion, or panic only for invariant violation | public failure contract and recoverability |
| `List<T>` | owned or borrowed slice / `ArrayList` | allocator owner, mutation, order, cleanup |
| `Map<K,V>` | `AutoHashMap`, `StringHashMap`, or ordered structure | equality/hash, iteration order, duplicates, cleanup |
| generics | comptime type/function parameters | accepted type set, code size, diagnostics |
| synchronized / lock | mutex/atomic or single-owner design | ordering, races, cancellation, deadlock |
| `CompletableFuture` / Reactor | repository-selected async/runtime abstraction | laziness, cancellation, backpressure, context |
| reflection | explicit registry, generated metadata, or comptime discovery | lookup names, accessibility, missing-member errors |
| annotation processor | build-time generator or comptime metadata | generated API and diagnostics |
| `ServiceLoader` | explicit registry/build-generated provider table | provider discovery, ordering, duplicate handling |
| Jackson | `std.json` plus explicit adapters | field names, defaults, unknown fields, numbers, nulls |
| `AutoCloseable` | explicit `deinit` plus `defer`/`errdefer` | normal/error/cancellation cleanup exactly once |
| byte buffer / stream | slices, readers, writers, owned buffers | position, partial I/O, limits, allocator lifetime |

## Allocator contract

For every API allocating memory, record:

- which allocator is passed;
- whether returned memory is borrowed, caller-owned, arena-owned, or type-owned;
- matching `deinit`/free responsibility;
- behavior on partial failure and `errdefer` cleanup;
- maximum allocation and denial-of-service limits;
- whether the Java implementation previously relied on GC lifetime.

Never return a slice backed by a temporary arena or stack value. Never hide a
new caller cleanup obligation from the public contract.

## Error contract

Do not collapse all Java failures into `anyerror`. Define the smallest stable
error surface that preserves caller-observable categories. When Java carries
structured error data, use a result payload or diagnostic object rather than
assuming an error-set tag can carry fields.

Assert:

- exact error tag/category;
- structured details and public diagnostic text where contractual;
- state and side effects before failure;
- cleanup and retry safety;
- source cause preservation where the Zig API exposes it.

## Async and concurrency contract

Zig async/runtime support is repository and version dependent. Inspect the
actual target before choosing threads, event loops, callbacks, or third-party
runtimes. Preserve:

- eager versus lazy execution;
- ordering and concurrency limits;
- cancellation ownership and propagation;
- timeout start/end boundaries;
- backpressure and buffering;
- context propagation;
- shutdown and cleanup.

Do not claim parity from matching function signatures when execution semantics
differ.

## ABI and cross-target contract

For C ABI, Wasm/WASI, embedded, or mobile targets, verify layout, alignment,
calling convention, integer widths, endian behavior, exported symbol names,
allocator boundary, and error transport on every claimed target.
