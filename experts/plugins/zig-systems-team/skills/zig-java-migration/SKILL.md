---
name: zig-java-migration
license: Apache-2.0
description: Evidence-driven, lossless Java-to-Zig migration and incomplete-port audit. Use when migrating a Java repository, module, framework, API, tests, fixtures, examples, or runtime behavior to Zig; when checking whether a Java-to-Zig port is actually complete; or when planning AgentScope Java to AgentScope Zig parity. Requires complete source-object and contract inventory, idiomatic Zig implementation, exact source-test preservation, differential verification, and explicit production-readiness evidence.
---

# Java to Zig Migration

Treat migration as preservation of observable contracts, not translation of
syntax or production-file counts. Java remains the compatibility oracle until
the complete agreed denominator is proven in Zig.

## Compose with the Zig skill pack

This skill owns migration governance. Load the target-language skills needed by
the repository instead of embedding a second Zig manual here:

- use `$zig-0.16` for Zig 0.16 projects and `$zig-0.15` only when the pinned
  toolchain requires it;
- use `$zig-project-structure` and `$zig-build-system` for modules, `build.zig`,
  package paths, targets, and cross-compilation;
- use `$zig-testing` and `$zig-java-migration-testing` for test implementation
  and completion evidence;
- use `$zig-concurrency`, `$zig-json`, `$zig-http`, or `$zig-crypto` only when
  those contracts are in scope;
- finish with `$zig-code-review` and `$zig-tiger-style` where compatible with
  source parity.

The source-side migration contract is shared with `rust-java-migration` and
future `kotlin-java-migration` and `swift-java-migration` skills. Only the
target-language profile changes. Read
[Cross-language migration profile](references/cross-language-migration-profile.md)
before changing denominators, dispositions, document schemas, or completion
claims.

## Non-negotiable outcome

A completed migration has all of the following:

1. Every in-scope Java object, member, overload, parameter, exception, comment,
   test case, fixture, script, example, and externally observable behavior has a
   traceable Zig disposition.
2. Every required disposition has real Zig logic; declarations, imports,
   generated API lists, empty bodies, `unreachable`, placeholder errors, and
   compile-only facades do not count.
3. The complete Java test suite and the complete Zig lossless-port suite pass.
4. Every concrete source case has a Java/Zig golden or live differential result
   of `MATCH`; no mismatch, harness failure, skip, or not-run case remains.
5. Zig-specific allocator, ownership, error-set, `defer`/`errdefer`, target,
   ABI, concurrency, and build-graph risks have additional tests.
6. Real-host, load, security, rollout, and rollback claims remain separate from
   functional parity and require their own evidence.

Coverage is a diagnostic signal. It is never the migration denominator or proof
that Java and Zig produce the same result.

## Establish baselines and scope

Record before editing:

- immutable Java SHA/tag and Zig SHA;
- JDK/build-tool versions, Zig version, target triple, optimization mode, and
  build options;
- source and target roots;
- public API, serialization, protocol, error, lifecycle, concurrency, and side
  effect contracts;
- source test roots and every non-standard fixture/resource/script/data root;
- generated sources, platform-only behavior, approved exclusions, and blockers;
- exact commands for Java, Zig, differential, host, and non-functional gates.

If `.codegraph/` exists, use CodeGraph before text search to trace public entry
points, dynamic registries, callbacks, lifecycle edges, and test-to-production
paths. Otherwise use deterministic source inventories and compiler/build data.

## Maintain four current migration documents

Keep one current set per source module:

1. `迁移路线图.md`
2. `对象级对照表.md`
3. `语义迁移对照表.md`
4. `对象名称一致性检查.md`

All four documents must carry the same Java baseline, Zig baseline, audit date,
scope, and completion state. Historical design material belongs after an
explicit historical marker; it cannot override current generated facts.

Use these states precisely:

| State | Meaning | Completion effect |
|---|---|---|
| `MISSING` | no Zig counterpart | blocks |
| `MISPLACED` | counterpart exists at the wrong agreed path | blocks |
| `STUB` | placeholder or non-functional body | blocks |
| `PARTIAL` | some contracts are absent | blocks |
| `UNVERIFIED` | implementation exists without required evidence | blocks |
| `IMPLEMENTED` | structure, behavior, and required evidence complete | handled |
| `DEPENDENCY_REUSED` | pinned Zig dependency plus adapter and local tests | handled |
| `PLATFORM_NA` | proven JVM/platform-only contract | outside denominator |
| `ZIG_EXTENSION` | target-only additive capability | outside source denominator |

## Map Java structure to Zig

Default structural rule:

- one Java class/interface/enum/record/annotation maps to one primary `.zig`
  file;
- nested types and builders may remain with their owning type;
- package directories become `snake_case` directories using the documented
  repository path algorithm;
- `root.zig` files define module imports and public re-exports, not a warehouse
  of migrated objects;
- type names use `TitleCase`; functions and local values use Zig `camelCase`;
  preserve Java member names separately in registries, serializers, protocols,
  or compatibility metadata when observable;
- do not use one `compat.zig`, generated registry, or re-export facade to inflate
  object completion.

Preserve Java method parameters in order and meaning. Zig API naming may be
idiomatic, but the object and semantic ledgers must record the exact Java symbol
to Zig symbol mapping. Read
[Java-to-Zig semantic mappings](references/java-to-zig-semantic-mappings.md)
before implementing ownership, exceptions, async behavior, generics, reflection,
annotations, serialization, or service discovery.

## Implement in dependency batches

1. Freeze the complete object, method, test, and asset denominator.
2. Resolve architecture-wide decisions: allocator ownership, error model,
   cancellation, serialization, registry/SPI, synchronization, and ABI.
3. Implement the full dependency-ordered batch without alternating migration and
   final acceptance object by object.
4. Recompute the full inventory from current Java and Zig sources.
5. Reconcile all four documents in one pass.
6. Run the unified engineering and semantic verification pipeline.

Avoid permanent compatibility layers that merely preserve Java class shapes.
Use Zig-native structs, tagged unions, error unions, comptime, explicit
allocators, and modules where they preserve the same contract. Keep adapters at
real Java compatibility boundaries such as serialized names, plugin IDs,
protocol fields, or host APIs.

## Dependency replacement

Do not select a Zig package because its name resembles a Java library. Record:

- exact Java responsibility and observable contract;
- candidate package URL, version/commit, license, Zig compatibility, target
  support, maintenance and security evidence;
- exact upstream symbol and local call point;
- adapter behavior for errors, lifecycle, cancellation, threading, ordering,
  allocation, and serialization;
- focused spike, shared conformance test, and real-host result;
- rollback or replacement strategy.

`DEPENDENCY_REUSED` is valid only after the exact declared dependency path is
executed through local integration tests.

## Whole-project acceptance module

Every repository/product-level completion claim requires a dedicated,
non-production `<project>-test/` module. Register an explicit
`zig build migration-test` step in `build.zig`; keep the module out of published
package paths and production artifacts. It owns:

- complete source-suite and immutable source-asset replay;
- public cross-module and binding/adapter workflows;
- Java/Zig golden or live differential execution;
- aggregate machine-readable evidence.

Local `test` blocks inside production modules prove focused implementation
behavior only. They do not replace `<project>-test`. The whole-project gate is
all source cases `MATCH` with zero failed, skipped, ignored, or not-run cases.

## Unified verification

Run after the batch is frozen:

1. formatting and repository-specific lint/style checks;
2. `zig build`, `zig build test`, explicit target/optimization matrices, and
   cross-compilation checks;
3. complete mirrored source tests in `<project>-test`;
4. complete pinned Java and Zig suites plus every-case differential comparison;
5. real script/example replay;
6. allocator/leak, lifecycle, concurrency, cancellation, and deterministic
   scheduling tests;
7. malformed input, fuzz/property, load/soak, and security tests;
8. real host/binding/ABI integration;
9. gray rollout and rollback rehearsal when production replacement is claimed.

Read [Verification and acceptance](references/verification-and-acceptance.md) for
evidence levels and completion reporting.

## Red lines

- Do not simplify Java semantics to make Zig implementation easier.
- Do not omit overloads, parameter variants, exception behavior, side effects,
  lifecycle rules, tests, resources, or comments from the denominator.
- Do not count file existence, imports, exports, build success, or API manifests
  as implementation.
- Do not use `unreachable`, placeholder errors, empty tests, or ignored errors as
  migrated logic.
- Do not treat allocator leaks, borrowed-slice lifetime changes, error-set
  collapse, target omissions, or ABI changes as internal details.
- Do not modify copied source fixtures in place; preserve byte-identical copies
  and generate target-specific derivatives separately.
- Do not accept two independently green suites as parity.
- Do not use sampled differential cases, pass thresholds, coverage percentages,
  or “representative” scripts for a completion claim.
- Do not hide `MISSING`, `PARTIAL`, `STUB`, `MISPLACED`, or `UNVERIFIED` rows in
  historical appendices or alternate documents.

## Completion criteria

- The current object denominator contains no incomplete state.
- Every Java object/member/test/case/asset is traceable and losslessly handled.
- Every copied source asset has matching SHA-256.
- Java and Zig complete suites pass from pinned baselines.
- Full per-case differential output is 100% `MATCH` with zero harness failure or
  not-run case.
- `<project>-test` owns the complete command and aggregate artifact.
- Zig-specific allocator, error, target, ABI, concurrency, and build obligations
  pass.
- Real-host and production-readiness claims have separate evidence.
- Final reporting distinguishes structural, implementation, behavioral,
  integration, and production-readiness completion.

## Resources

- [Cross-language migration profile](references/cross-language-migration-profile.md)
- [Java-to-Zig semantic mappings](references/java-to-zig-semantic-mappings.md)
- [Verification and acceptance](references/verification-and-acceptance.md)
- [Migration roadmap template](assets/迁移路线图.md)
- [Object mapping template](assets/对象级对照表.md)
- [Semantic mapping template](assets/语义迁移对照表.md)
- [Name consistency template](assets/对象名称一致性检查.md)
