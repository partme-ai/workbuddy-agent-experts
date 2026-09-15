---
name: zig-java-migration-testing
license: Apache-2.0
description: Strict Java-to-Zig migration testing and completion firewall. Use when porting Java JUnit tests, parameterized cases, fixtures, resources, scripts, corpora, and golden data to Zig; building Java/Zig differential harnesses; auditing whether source tests were weakened or skipped; creating a whole-project Zig migration-test module; or adding Zig-specific allocator, error, ABI, target, concurrency, fuzz, load, and host tests after source parity.
---

# Java-to-Zig Migration Testing

Prove two separate claims in order:

1. the entire source test contract and all test assets were migrated without
   loss and Java/Zig observable results match;
2. Zig-specific risks have additional valuable tests.

Do not use coverage, target test counts, file counts, or two independently green
suites as proof of migration completion.

## Compose with the Zig skill pack

Use `$zig-testing` for Zig assertions, leak detection, and test syntax;
`$zig-build-system` for test modules, steps, options, and targets;
`$zig-concurrency` for deterministic synchronization and race/lifecycle tests;
and `$zig-java-migration` for the authoritative object and semantic scope. Load
`$zig-0.16` or `$zig-0.15` according to the pinned repository toolchain.

This skill implements the same source-test contract as
`rust-java-migration-testing` and future Kotlin/Swift variants. The invariant
portion must remain equivalent; only target syntax, build integration, and
target-specific obligations may differ. Read
[Testing adapter contract](references/testing-adapter-contract.md) before
changing dispositions, manifest fields, or completion rules.

## Required ledgers

Maintain three logically separate ledgers:

| Ledger | Denominator | Completion rule |
|---|---|---|
| `SOURCE_PARITY/TEST_CASE` | every Java test method and every concrete generated/parameterized case | lossless Zig implementation plus per-case `MATCH` |
| `SOURCE_PARITY/TEST_ASSET` | every source fixture/resource/script/corpus/golden/data file | byte-identical target copy and matching SHA-256 |
| `ZIG_OBLIGATION` | allocator, lifetime, error, target, ABI, build, concurrency and other target risks | applicable obligation passes |

`VALUE_ADD` tests may follow, but never replace a missing source row or Zig
obligation.

## Inventory the source suite

Pin the Java and Zig baselines, then inventory:

- JUnit 4/5 test methods;
- parameterized, repeated, dynamic, template, nested, inherited, and generated
  cases;
- disabled/ignored tests and their reasons;
- setup, teardown, rules, extensions, temporary directories, clocks, random
  seeds, environment, system properties, locale, and time zone;
- test-support modules and helper classes;
- every test fixture, resource, script, corpus, snapshot, and golden file;
- external services, containers, native libraries, ports, and host assumptions.

A disabled Java test remains in the denominator. It must be implemented and
enabled for migration completion, or remain an explicit blocker.

Use one row per concrete case. Never map parameterized methods only by method
name or compare aggregate test totals.

## Source test dispositions

| Disposition | Meaning | Complete only when |
|---|---|---|
| `MIRRORED` | one Java case maps to one Zig case | full contract and `MATCH` |
| `ADAPTED` | Zig-native harness represents the same contract | no weaker input/assertion/effect/cleanup and `MATCH` |
| `SPLIT` | one Java case maps to multiple Zig tests | all assertions and case identity preserved |
| `MERGED_APPROVED` | cases share a data-driven Zig runner | every case and assertion remains individually traceable |
| `NOT_APPLICABLE` | source claim considered target-inapplicable | blocks lossless completion |
| `BLOCKED` | dependency/oracle prevents execution | blocks |
| `MISSING` | no Zig test implementation | blocks |

The first four also require all preservation flags true, an existing Zig target
test, retained evidence, and Java/Zig result `MATCH`.

## Copy source assets exactly

Copy every source fixture/resource/script/corpus/golden/data file without
editing bytes. Record Java path, Zig path, mode `COPY_EXACT`, and SHA-256.
Target-normalized or generated files must be separate derivatives and must cite
the immutable source copy.

Do not silently normalize line endings, encodings, JSON/YAML formatting,
timestamps, ordering, locale data, or snapshots while copying.

## Whole-project Zig acceptance module

Every repository/product-level completion claim requires:

```text
<project>-test/
├── src/root.zig             # reusable harness only
├── tests/source_parity.zig
├── tests/cross_component.zig
└── suite/source/            # byte-identical Java test assets
```

Register it in the root `build.zig` with an explicit `migration-test` step and
run it with:

```bash
zig build migration-test
```

Keep it out of production installation and `build.zig.zon` publication paths.
It imports public production modules and owns complete source replay,
cross-module/binding workflows, differential execution, and aggregate artifacts.
Local production-module `test` blocks remain focused subsystem evidence.

The whole-project gate cannot use “at least N passes”, representative cases,
filters, skipped capabilities, or ignored tests. Require every source case
`MATCH` and failed/skipped/not-run counts of zero.

## Implement Zig test contracts

For each Java case preserve:

- exact inputs and boundary values;
- assertion specificity, including exact error category and structured data;
- fixture setup and state;
- observable output, ordering, state transitions, side effects, and calls;
- cleanup on success, error, cancellation, and partial initialization;
- deterministic clock/random/scheduling behavior;
- environment and host assumptions.

Use `std.testing.expectEqual`, `expectEqualStrings`, `expectError`, or more
specific assertions rather than generic success/failure checks. A compile-only
import or `try` with no observable assertion does not preserve a source test.

## Differential verification

Run the complete pinned Java suite and complete Zig suite, then compare every
source case using either:

- pinned Java golden artifacts consumed by Zig; or
- a live harness that invokes both implementations.

Retain raw Java output, raw Zig output, normalized output, and the comparison
report separately. Normalize only documented nondeterminism. Never normalize
error categories, missing/extra fields, numeric precision, contractual order,
side-effect counts, lifecycle transitions, or security-relevant data.

Required outcome:

```text
matched == source_cases
mismatched == 0
harness_failures == 0
skipped == 0
not_run == 0
```

Use the [source parity manifest](assets/source-test-parity.json) and run the
audit script described below.

## Zig-specific obligations

After source parity, add tests where applicable for:

- allocator ownership and matching free/deinit;
- `defer` and `errdefer` behavior under every partial failure point;
- borrowed slice/pointer lifetime and aliasing;
- exact error-set and diagnostic behavior;
- integer width, overflow, alignment, endian, and ABI layout;
- comptime branches and generated declarations;
- Debug, ReleaseSafe, ReleaseFast, and ReleaseSmall differences;
- native, cross-compiled, Wasm/WASI, embedded, or mobile targets claimed;
- thread safety, atomics, cancellation, bounded queues, and shutdown;
- JSON unknown/default/null/numeric behavior;
- malformed input, allocation limits, fuzz/property invariants;
- real C library, service, filesystem, network, or host integration.

These are additive. They do not increase the source parity numerator.

## Audit workflow

Resolve `SKILL_DIR` to this skill directory and run:

```bash
python3 "$SKILL_DIR/scripts/audit_java_zig_tests.py" \
  --java-root ../agentscope-java \
  --zig-root ../agentscope-zig \
  --parity-manifest docs/source-test-parity.json \
  --fail-on-incomplete
```

The script verifies baselines, every recorded source case, preservation flags,
existing Zig target files, exact source assets, complete run records,
`migration-test` module registration, and the full differential counts. Static
extraction is conservative and cannot infer semantic mappings; the manifest and
retained artifacts remain required evidence.

Read [Verification SOP](references/migration-verification-sop.md) for schema,
module layout, evidence, and normalizer rules.

## Red lines

- Do not exclude, disable, weaken, or merge away source tests to manufacture
  parity.
- Do not accept generic “no error” assertions when Java checks exact values,
  state, side effects, or error categories.
- Do not edit source assets in place.
- Do not call mirrored tests differential unless Java output participates.
- Do not use test totals, coverage, sampled cases, or two green suites as parity.
- Do not accept leaks, hidden allocator ownership, skipped targets, broad
  `anyerror`, ignored cleanup, or ABI gaps as language-internal details.
- Do not put missing production logic in `<project>-test`.
- Do not let local module tests replace whole-project acceptance.
- Do not claim completion with any failed, skipped, ignored, blocked, missing,
  mismatched, harness-failed, or not-run case.

## Completion criteria

- Every Java test and concrete generated case has a lossless Zig implementation.
- Every source test asset has a byte-identical Zig repository copy and matching
  SHA-256.
- Every mapped case preserves inputs, assertions, fixture state, effects, and
  cleanup.
- Complete Java and Zig suites pass from pinned baselines.
- Full Java/Zig differential results are 100% `MATCH`.
- `<project>-test` is registered under `zig build migration-test`, excluded from
  production publication, and owns aggregate evidence.
- All applicable Zig obligations pass across claimed targets and modes.
- Object-ledger blockers, host gaps, flakes, warnings, and production-readiness
  gaps remain visible.

## Resources

- [Testing adapter contract](references/testing-adapter-contract.md)
- [Verification SOP](references/migration-verification-sop.md)
- [Test categories](references/test-categories.md)
- [Migration test ledger template](assets/迁移测试对照表.md)
- [Source parity manifest template](assets/source-test-parity.json)
- `scripts/audit_java_zig_tests.py`
