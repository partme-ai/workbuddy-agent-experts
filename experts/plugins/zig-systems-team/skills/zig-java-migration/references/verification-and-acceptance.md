# Verification and Acceptance

## Evidence levels

| Level | Evidence | Claim allowed |
|---|---|---|
| `V0_STATIC` | inventory and source trace | planned/mapped only |
| `V1_ZIG_LOCAL` | focused Zig test | local target behavior |
| `V2_MIRRORED` | lossless Java test implemented in Zig | source contract represented |
| `V3_GOLDEN_DIFF` | pinned Java golden compared with Zig | compared cases only |
| `V4_LIVE_DIFF` | both implementations executed | compared cases only |
| `V5_HOST` | real host/dependency/ABI target | integration claim |
| `V6_NONFUNCTIONAL` | concurrency/load/fuzz/security/soak | measured property only |
| `V7_ROLLBACK` | gray and rollback rehearsal | production recovery claim |

Evidence levels do not automatically promote one another. A full migration
requires the applicable combination, not merely the highest number reached by
one test.

## Whole-project test layout

```text
<project>/
├── build.zig
├── build.zig.zon
├── <production modules>/
└── <project>-test/
    ├── src/root.zig
    ├── tests/source_parity.zig
    ├── tests/cross_component.zig
    └── suite/source/     # immutable Java test assets
```

`build.zig` must expose an explicit `migration-test` step which imports public
production modules and runs the whole-project suite. Keep `<project>-test` out
of installed production artifacts and package publication paths.

## Required result artifact

Record at minimum:

```json
{
  "target_language": "zig",
  "java_baseline": "<sha>",
  "target_baseline": "<sha>",
  "source_cases": 0,
  "matched": 0,
  "mismatched": 0,
  "harness_failures": 0,
  "skipped": 0,
  "not_run": 0
}
```

Completion requires `matched == source_cases` and every other count zero.

## Zig engineering matrix

Run the repository's pinned equivalent of:

```bash
zig fmt --check .
zig build
zig build test
zig build migration-test
zig build -Doptimize=ReleaseSafe
```

Add all claimed targets and options. A native debug run does not prove release,
Wasm/WASI, embedded, mobile, or foreign ABI behavior.

## Production-readiness separation

Report independently:

- structural mapping completion;
- implementation completion;
- full behavioral parity;
- real-host/ABI integration;
- concurrency and resource safety;
- performance/stability;
- security;
- rollout and rollback readiness.

Never compress these into one percentage or one green CI badge.
