---
name: kotlin-java-migration-testing
license: Apache-2.0
description: Prove Java-to-Kotlin migration completeness through 100 percent lossless source-test implementation, byte-identical source assets, dedicated whole-project test modules, full Java/Kotlin differential execution, Kotlin-specific risk tests, and auditable evidence. Use after or during kotlin-java-migration; coverage alone never satisfies this skill.
---

# Java to Kotlin Migration Testing

This skill defines the acceptance proof. The final objective is identical observable behavior for the same inputs under equivalent environments.

## Mandatory evidence dimensions

Keep independent denominators and statuses for:

1. Java production objects and members.
2. Java test files, test methods, parameterized/dynamic concrete cases, suites, and disabled tests.
3. Test resources, golden files, schemas, certificates, archives, scripts, and datasets.
4. Full Java/Kotlin differential cases.
5. Kotlin-only obligations such as null/platform-type boundaries, coroutine cancellation, Flow lifecycle, Java ABI, and Gradle/toolchain compatibility.
6. Coverage, mutation, fuzz/property, load/soak, security, and platform evidence.

Dimensions 1–4 must reach exact completeness; dimensions 5–6 are additive risk evidence.

## Source-test parity

- Inventory every Java test source and every concrete case, including parameter sources, nested/dynamic tests, inherited contract suites, tags, assumptions, disabled cases, fixtures, and external prerequisites.
- Implement each case losslessly in Kotlin. Preserve input, setup, operation, assertion strength, expected failure category/message when contractual, side effects, order, cleanup, and case identity.
- A grouped Kotlin parameterized test is acceptable only if the ledger maps every Java case and reports every result separately.
- No skipped, ignored, disabled, quarantined, compile-only, or not-run target case may count as complete.
- Keep the Java suite executable; do not replace it with translated tests alone.

## Asset parity

Copy source test assets directly whenever licensing and repository policy permit. Preserve bytes, relative paths, encoding, line endings, permissions when relevant, and archive structure. Produce a SHA-256 manifest and fail on missing, extra, or changed required assets. Generated equivalents require explicit approval and reproducibility evidence.

Use the bundled audit helper as an inventory starting point:

```bash
python3 scripts/audit_migration_tests.py \
  --java-root /path/to/java-project \
  --target-root /path/to/kotlin-project \
  --target-extension .kt
```

## Dedicated whole-project module

Create a Gradle module named `<project>-test` for migration acceptance:

```text
project-test/
├── build.gradle.kts
└── src/test/
    ├── kotlin/          # whole-project scenarios and differential harness
    └── resources/       # byte-identical copied source fixtures
```

This module depends on production modules through their public composition boundary and owns end-to-end scenarios, real adapter/host integration, Java/Kotlin runners, output normalization, and parity reports. Local tests inside production modules continue to test local behavior.

## Differential gate

For every source case, execute Java and Kotlin against the same versioned input and compare the complete observable contract:

- return value and type/category;
- structured error, causal chain, and contractual message;
- ordering, state transitions, side effects, call counts, and emitted events;
- serialized bytes, protocol output, filesystem/database effects, and resource lifecycle where applicable.

Store raw outputs separately. Pin source/target commits, runners, normalizer version, locale, timezone, encoding, dependencies, seed, and platform. Normalization may remove only proven nondeterminism and must never hide unexpected fields.

Final acceptance requires:

```text
java_suite=PASS
kotlin_suite=PASS
differential_cases=100% MATCH
mismatch=0 harness_error=0 skipped=0 ignored=0 not_run=0
```

## Kotlin-specific additions

Add tests for platform-type nulls, Java/Kotlin ABI calls, default arguments and overload bridges, generic variance, data-class equality/copy, coroutine cancellation, Flow backpressure/lifecycle, dispatcher blocking, and Gradle/JDK compatibility. These supplement source parity and cannot replace it.

## Coverage position

Measure comparable production scopes after parity. Coverage helps find unexercised Kotlin paths, but equal or high coverage does not prove equal behavior. Never weaken assertions, duplicate trivial tests, or exclude difficult code to satisfy a number.

## Completion report

Publish commands, environment, artifact links, per-case ledger, asset hashes, mismatch report, known limitations, and rollback/compatibility results. Say “complete” only when all mandatory gates pass with zero unexplained exceptions.

