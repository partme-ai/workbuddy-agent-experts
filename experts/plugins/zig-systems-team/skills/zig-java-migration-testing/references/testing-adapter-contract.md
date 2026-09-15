# Java Migration Testing Adapter Contract

## Invariants shared by every target language

Every `<target>-java-migration-testing` skill must enforce:

1. one mapping for every Java test method and every concrete generated case;
2. immutable source test assets copied byte-for-byte with SHA-256 evidence;
3. preservation of contract, inputs, assertions, fixture state, side effects,
   and cleanup;
4. complete source and target suite execution from pinned baselines;
5. complete golden or live Java/target differential comparison;
6. `MATCH` for every case and zero mismatch, harness failure, skip, ignore, or
   not-run;
7. one non-production whole-project `<project>-test` acceptance module;
8. additive target-language tests after source parity;
9. separate functional, host, non-functional, and production-readiness claims.

Allowed complete dispositions are `MIRRORED`, `ADAPTED`, `SPLIT`, and
`MERGED_APPROVED`, only with full preservation and matching results.
`NOT_APPLICABLE`, `BLOCKED`, and `MISSING` always block a 100% lossless
completion claim.

## Common manifest concepts

All target adapters use these logical fields even if an older adapter accepts a
backward-compatible alias:

```json
{
  "schema": 2,
  "target_language": "<target>",
  "java_baseline": "<sha>",
  "target_baseline": "<sha>",
  "acceptance_module": {},
  "source_tests": [],
  "assets": [],
  "runs": {
    "java": {},
    "target": {},
    "differential": {}
  }
}
```

Run records contain exact command, `PASS` status, zero failure/skip/not-run
counts, and a retained artifact. Differential records additionally contain
matched, mismatched, and harness-failure counts.

## Target adapter fields

The Zig adapter defines:

- test declaration extraction for `test "name" { ... }`;
- target files ending in `.zig`;
- build manifest `build.zig` and optional package manifest `build.zig.zon`;
- whole-project directory `<project>-test`;
- build step and command `migration-test` / `zig build migration-test`;
- package exclusion attestation `published: false`;
- Zig-specific obligations for allocators, lifetimes, error sets, modes,
  targets, ABI, comptime, and concurrency.

Future Kotlin and Swift adapters keep the common fields and replace only this
target profile. They must not weaken the invariant outcome.

## Drift review

When changing a shared disposition, manifest concept, or completion rule, audit
the Rust, Zig, Kotlin, and Swift adapters. When changing only target syntax or a
toolchain gate, keep the change inside that target package.
