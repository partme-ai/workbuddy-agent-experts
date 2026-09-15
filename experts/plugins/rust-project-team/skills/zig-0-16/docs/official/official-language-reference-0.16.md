# Zig 0.16 Language Reference (Official Distillation)

Source: https://ziglang.org/documentation/0.16.0/

This file distills the official language reference into an offline "coverage map + navigation guide", and points to the matching offline reference files in this repository.

## What the official language reference contains

The official Zig language reference is organized as:

- A table of contents covering the full language surface
- Core language concepts: values, types, control flow, functions, errors, optionals, casting
- Metaprogramming: `comptime`, reflection, builtin functions
- Low-level features: assembly and atomics
- Safety model: build modes and illegal behavior checks
- Memory model and allocator guidance
- Compilation model and how Zig sources are discovered/linked
- C interoperability, translation, and linking
- Targets, WebAssembly/WASI notes, and style guidance
- Appendix: keyword reference, grammar, "Zen"

## Official coverage map (high level)

The following groups correspond to the official TOC sections.

### Getting started and docs conventions

- Introduction
- Hello World
- Comments / doc comments / top-level doc comments
- Identifiers (including string identifier syntax)

### Values and basic types

- Values
  - Primitive types, primitive values
  - String literals, escape sequences, multiline literals
- Assignment
  - `undefined`
  - Destructuring
- Variables (container-level, static local, thread local, local variables)
- Integers (literals, runtime values)
- Floats (literals, floating point ops)
- Operators (operator table, precedence)

Offline mapping:

- `../../references/language.md` for core syntax and semantics
- `../../references/std-fmt.md` and `../../references/std-ascii.md` for parsing/formatting related parts

### Collections and memory views

- Arrays (multidimensional, sentinel-terminated, destructuring)
- Vectors (relationship with arrays, destructuring)
- Pointers (volatile, alignment, allowzero, sentinel-terminated pointers)
- Slices (sentinel-terminated slices)

Offline mapping:

- `../../references/std-mem.md` for slice and memory utilities
- `../../references/std-allocators.md` for allocator choices and patterns

### User-defined types

- `struct` (default fields, extern/packed, naming, anonymous literals, tuples)
- `enum` (extern enum, enum literals, non-exhaustive enums)
- `union` (tagged unions, extern/packed unions, anonymous union literals)
- `opaque`

Offline mapping:

- `../../references/language.md` for type semantics
- `../../references/patterns.md` for idiomatic usage and API shaping

### Control flow

- Blocks (shadowing, empty blocks)
- `switch` (exhaustive switching, enum literals, switching on errors, labeled switch, inline switch prongs)
- `while` (labeled, with optionals, with error unions, inline while)
- `for` (labeled for, inline for)
- `if` (including optionals)
- `defer`
- `unreachable` (basics, at compile-time)
- `noreturn`

Offline mapping:

- `../../references/language.md` for control flow rules
- `../../references/code-review.md` for stale-pattern detection and foot-guns

### Functions, errors, optionals, casting

- Functions (pass-by-value params, parameter type inference, inline fn, function reflection)
- Errors
  - Error set type (including the global error set)
  - Error union type (`catch`, `try`, `errdefer`, merging/inferred error sets)
  - Error return traces
- Optionals (optional type, null, optional pointers)
- Casting
  - Type coercion variants
  - Explicit casts
  - Peer type resolution
- Zero-bit types (`void`)
- Result location semantics

Offline mapping:

- `../../references/language.md` for the language rules
- `../../references/patterns.md` for idiomatic error/optional patterns

### Comptime and builtins

- `comptime` (compile-time parameters/variables/expressions, generic data structures, case study)
- Builtin functions (`@...`)

Offline mapping:

- `../../references/comptime.md` and `../../references/std-meta.md` for metaprogramming patterns
- `../../references/builtins.md` for the offline builtin function reference

### Low-level features and runtime safety

- Assembly (constraints, clobbers, global assembly)
- Atomics
- Async Functions (covered by the official docs, but do not assume old `async`/`await` syntax works in modern Zig)
- Build Mode (Debug/ReleaseFast/ReleaseSafe/ReleaseSmall, single-threaded builds)
- Illegal Behavior (unreachable, OOB, casts, overflow, division-by-zero, unwrap null/error, alignment, union access, etc.)

Offline mapping:

- `../../references/std-atomic.md` and `../../references/std-thread.md`
- `../../references/code-review.md` for migration traps

### Memory model and allocators

- Memory
  - Choosing an allocator
  - Where are the bytes?
  - Heap allocation failure
  - Recursion
  - Lifetime and ownership

Offline mapping:

- `../../references/std-allocators.md`
- `../../references/patterns.md`

### Compilation model and build system

- Compile variables
- Compilation model
- Source file structs
- File and declaration discovery
- Special root declarations
- Entry point
- Standard library options
- Panic handler
- Zig build system

Offline mapping:

- `../../references/std-build.md`
- `../../references/std-debug.md` and `../../references/std-log.md` for diagnostics

### C, targets, and style guide

- C and C translation (CLI flags, `-target` and `-cflags`, `@cImport` vs translate-c, caching, macros, pointers, variadics)
- Exporting a C library, mixing object files
- WebAssembly, freestanding, WASI, targets
- Style guide (naming, whitespace, doc comment guidance, source encoding)
- Keyword reference, appendix, containers, grammar, zen

Offline mapping:

- `../../references/c-interop.md` and `../../references/std-c.md`
- `../../references/style-guide.md`

## Practical note

The official language reference is the authority for section names and definitions. This repository's `references/` set is optimized for offline use and "copy/paste + compile" examples.
