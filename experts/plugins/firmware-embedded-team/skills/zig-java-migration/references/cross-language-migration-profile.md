# Cross-language Java Migration Profile

## Purpose

Every target-language skill package exposes the same two responsibilities:

| Skill | Shared responsibility | Target-specific responsibility |
|---|---|---|
| `<target>-java-migration` | source denominator, contracts, dispositions, documents, completion semantics | language mappings, layout, toolchain, ownership/lifecycle model |
| `<target>-java-migration-testing` | 100% source tests/assets, complete differential gate, whole-project acceptance | test syntax, build runner, leak/race/ABI/target obligations |

Canonical names:

| Target package | Migration skill | Testing skill |
|---|---|---|
| `rust-skills` | `rust-java-migration` | `rust-java-migration-testing` |
| `zig-skills` | `zig-java-migration` | `zig-java-migration-testing` |
| `kotlin-skills` | `kotlin-java-migration` | `kotlin-java-migration-testing` |
| `swift-skills` | `swift-java-migration` | `swift-java-migration-testing` |

Do not name these `java-to-zig`, `java2zig`, `migration-zig`, or alternate
between `-test` and `-testing`. Stable names allow prompts, CI policies, and
skill installation to remain predictable.

## Shared source contract

All adapters must preserve the same source-side facts:

- immutable Java and target baselines;
- complete source object and member inventory;
- public and protected signatures, overloads, parameters, return contracts,
  checked exceptions, annotations, generics, nullability, and comments;
- observable data, protocol, serialization, ordering, lifecycle, concurrency,
  security, and side-effect behavior;
- every source test method and every concrete parameterized/dynamic case;
- every fixture, resource, script, corpus, golden file, and test data file;
- examples, host integrations, platform constraints, and production operations.

The shared blocking states are `MISSING`, `MISPLACED`, `STUB`, `PARTIAL`, and
`UNVERIFIED`. A target adapter may add `<TARGET>_EXTENSION`, but may not remove or
weaken a blocking state.

## Shared implementation rules

Each target adapter must enforce:

1. One traceable target disposition per Java source object and member.
2. Real production logic rather than facade/re-export/registry/file-count
   placeholders.
3. No contract weakening merely because the target language lacks an identical
   runtime mechanism.
4. Explicit mapping for platform-only behavior and dependency reuse.
5. Batch implementation followed by consolidated audit and verification.
6. One current set of migration documents with matching baselines.
7. A dedicated whole-project `<project>-test` acceptance module.
8. Separate structural, behavioral, host-integration, non-functional, and
   production-readiness conclusions.

## Shared testing rules

The testing adapter must require:

- 100% source test/case mapping;
- byte-identical source asset copies with SHA-256;
- preservation of input, assertion, fixture state, side effect, and cleanup;
- complete pinned source and target suite runs;
- golden or live Java/target comparison for every concrete case;
- `MATCH` only, with zero mismatch, harness failure, skip, ignore, or not-run;
- additive target-language obligations after source parity;
- complete aggregate evidence owned by `<project>-test`.

Coverage, file counts, mirrored test names, two green suites, sampled corpora,
and pass thresholds are not substitutes for result parity.

## Target adapter interface

Every target pair documents these fields:

| Field | Required content |
|---|---|
| `target_language` | stable lowercase name such as `zig` |
| `target_toolchain` | pinned compiler/runtime and supported targets |
| `build_manifest` | target build/workspace manifest |
| `build_command` | complete production build command |
| `local_test_command` | focused module test command |
| `acceptance_command` | explicit `<project>-test` command |
| `format_lint_commands` | target formatting and static checks |
| `layout_rule` | Java object to target file/module mapping |
| `name_rule` | type/function/file/package conventions |
| `error_mapping` | checked/unchecked exceptions to target errors |
| `null_mapping` | nullable and absence semantics |
| `generic_mapping` | generic, trait/protocol/interface semantics |
| `async_mapping` | futures/streams/cancellation/backpressure mapping |
| `resource_mapping` | allocation, ownership, cleanup, and leak rules |
| `reflection_mapping` | annotation/reflection/SPI replacement |
| `serialization_mapping` | field names, defaults, unknowns, numeric behavior |
| `platform_matrix` | host/target/ABI/feature combinations |
| `target_obligations` | tests that do not exist in Java but are mandatory |

## Target profiles

| Concern | Rust | Zig | Kotlin | Swift |
|---|---|---|---|---|
| build | Cargo workspace | `build.zig` / `build.zig.zon` | Gradle Kotlin DSL | SwiftPM |
| errors | `Result` + error enum | error union + error set | exceptions / sealed result | `throws` / typed result |
| absence | `Option<T>` | `?T` | `T?` | `T?` |
| async | async/await + Stream | target/runtime-specific explicit async model | coroutines + Flow | structured concurrency + AsyncSequence |
| resources | ownership/RAII | explicit allocator + `defer`/`errdefer` | JVM lifecycle + `use` | ARC + deterministic cleanup where required |
| whole test | Cargo package `<project>-test` | build module `<project>-test` | Gradle module `<project>-test` | SwiftPM test target `<Project>MigrationTests` with `<project>-test` directory |

The target adapter must refine this table against the actual repository. It must
not invent a runtime, framework, or test library merely because the table names
a general language mechanism.

## Versioning and drift control

Treat this profile as a logical contract. Target packages may format their
documents and scripts differently, but these invariants must remain equivalent.
When changing one target pair:

1. classify the change as shared or target-specific;
2. if shared, audit the other target pairs and record follow-up work;
3. keep manifest concepts and completion vocabulary compatible;
4. add a regression test for deterministic audit behavior;
5. never silently weaken an older target's completion gate.

## Example: AgentScope

For AgentScope Java migrations:

- `agentscope-rust` uses `rust-java-migration` plus the Rust skill pack;
- `agentscope-zig` uses `zig-java-migration` plus the Zig skill pack;
- `agentscope-kotlin` will use `kotlin-java-migration` plus the Kotlin skill pack;
- `agentscope-swift` will use `swift-java-migration` plus the Swift skill pack.

All four targets share the same frozen Java denominator and source test assets.
Each target retains its own baseline, target test implementation, target-specific
obligations, and Java/target differential evidence. Passing one target never
proves another target complete.
