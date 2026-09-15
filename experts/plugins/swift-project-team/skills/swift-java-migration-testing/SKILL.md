---
name: swift-java-migration-testing
license: Apache-2.0
description: Prove Java-to-Swift migration completeness through 100 percent lossless source-test implementation, byte-identical source assets, dedicated whole-project acceptance packages, full Java/Swift differential execution, Swift-specific risk tests, and auditable evidence. Use during or after swift-java-migration; coverage alone never satisfies this skill.
---

# Java to Swift Migration Testing

The acceptance objective is identical observable behavior for identical inputs under equivalent environments.

## Mandatory evidence dimensions

Maintain independent denominators for:

1. Java production objects and members.
2. Java test files, methods, parameterized/dynamic concrete cases, suites, and disabled tests.
3. Test resources, golden files, schemas, certificates, archives, scripts, and datasets.
4. Full Java/Swift differential cases.
5. Swift-only obligations: optional/bridge boundaries, Codable shape, ownership, actor isolation, Sendable, cancellation, platform conditions, and SwiftPM behavior.
6. Coverage, mutation, fuzz/property, sanitizer, performance/load, security, and platform evidence.

Dimensions 1–4 require exact completeness; dimensions 5–6 add target-language risk proof.

## Source-test parity

- Inventory every Java test source and concrete case, including parameter sources, nested/dynamic tests, inherited contract suites, tags, assumptions, disabled cases, fixtures, and external prerequisites.
- Implement each case losslessly in Swift, preserving input, setup, operation, assertion strength, expected error, side effects, order, cleanup, and identity.
- Grouping cases is allowed only when the ledger maps and reports each original case independently.
- No skipped, disabled, quarantined, compile-only, unsupported, or not-run Swift case counts as complete.
- Keep the complete Java suite executable.

## Asset parity

Copy source assets directly when policy permits. Preserve bytes, relative paths, encoding, line endings, permissions where relevant, and archive structure. Generate a SHA-256 manifest and fail for missing, extra, or changed required assets. Generated equivalents require explicit approval and reproducibility proof.

```bash
python3 scripts/audit_migration_tests.py \
  --java-root /path/to/java-project \
  --target-root /path/to/swift-project \
  --target-extension .swift
```

## Dedicated whole-project acceptance

For large migrations, create a sibling package named `<project>-test`, or a clearly separated integration target with the same ownership:

```text
project-test/
├── Package.swift
├── Sources/ParityHarness/
└── Tests/ProjectAcceptanceTests/
    └── Resources/       # byte-identical Java fixtures
```

It depends on production products through public composition, runs real cross-target/host scenarios, invokes Java and Swift runners, normalizes only proven nondeterminism, and publishes parity reports. Production-target tests remain local unit/component evidence.

## Differential gate

Run every source case through Java and Swift with the same versioned input. Compare:

- value and type/category;
- structured error, causal semantics, and contractual message;
- ordering, state transitions, side effects, emitted events, and call counts;
- serialized bytes, protocol output, filesystem/database effects, and resource lifecycle where applicable.

Retain raw outputs separately. Pin commits, runner and normalizer versions, locale, timezone, encoding, dependency versions, seed, platform, and architecture. Never normalize unexpected fields away.

Final acceptance requires:

```text
java_suite=PASS
swift_suite=PASS
differential_cases=100% MATCH
mismatch=0 harness_error=0 skipped=0 disabled=0 not_run=0
```

## Swift-specific additions

Add tests for nil and Objective-C bridges, struct/class identity, copy-on-write behavior, Codable exact shape, generic/existential use, actor isolation, Sendable crossings, cancellation, continuation single-resume, AsyncSequence lifecycle, ARC cleanup, platform conditionals, and Swift tools compatibility. They supplement source parity.

## Coverage position

Measure comparable production scopes after parity. Coverage locates unexercised paths but cannot prove equal behavior. Do not weaken assertions or add trivial tests to satisfy a percentage.

## Completion report

Publish commands, environments, artifact links, the per-case ledger, asset hashes, mismatch report, known limitations, sanitizer/platform results, and rollback/compatibility evidence. Say “complete” only when every mandatory gate passes with zero unexplained exceptions.

