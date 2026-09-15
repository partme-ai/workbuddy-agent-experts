---
name: kotlin-code-review
license: Apache-2.0
description: Review Kotlin changes for correctness, compatibility, concurrency, nullability, API, security, performance, test quality, and Gradle integration. Use when asked to review, audit, assess risk, or explain defects in Kotlin code; produce evidence-backed findings without modifying code unless a fix is explicitly requested.
---

# Kotlin Code Review

Lead with findings ordered by severity. A review is not a style summary.

## Evidence workflow

1. Read the change, surrounding contracts, call sites, build configuration, and relevant tests.
2. Reproduce or statically trace each suspected defect.
3. Check nullability and platform types, equality/hash behavior, exceptions, ABI, serialization, coroutine cancellation, resource ownership, and dependency scopes.
4. Verify tests would fail for plausible defects and exercise production paths.
5. Report each finding with location, trigger, impact, and smallest credible remedy.

## Severity

- Critical: data loss, exploitable security defect, broad outage, or irreversible incompatibility.
- High: common-path wrong result, deadlock/leak, broken public contract, or migration parity failure.
- Medium: bounded correctness, resilience, performance, or maintainability risk.
- Low: concrete improvement with limited operational impact.

## Kotlin-specific checks

- Unsafe `!!`, unchecked casts, platform-type leakage, mutable collection exposure.
- Data-class equality or copy semantics that differ from the domain contract.
- Java ABI changes caused by defaults, overloads, wildcards, companions, or exception annotations.
- Coroutine scope leaks, swallowed cancellation, blocking on limited dispatchers, unbounded Flow buffers.
- Gradle dependency leakage, mismatched JVM targets, eager tasks, secret exposure, and non-reproducible generation.

If no actionable defect is found, say so and list remaining validation gaps. Do not invent findings to fill a template.

