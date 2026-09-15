---
name: kotlin-java-migration
license: Apache-2.0
description: Migrate Java systems to Kotlin without semantic simplification by inventorying every production object and member, preserving public behavior and compatibility, mapping Java frameworks deliberately, implementing Kotlin-native code, and maintaining a machine-checkable migration ledger. Use for Java-to-Kotlin ports, rewrites, compatibility layers, or migration-completeness work; pair with kotlin-java-migration-testing for proof.
---

# Java to Kotlin Migration

The target is equivalent capability and behavior, not similar-looking code. A compiling Kotlin project is only an intermediate state.

## Non-negotiable completion contract

- Every in-scope Java production class, interface, enum, record, annotation, nested type, constructor, method, field-backed contract, and externally visible behavior is recorded.
- Every record is `IMPLEMENTED`, `ADAPTED` with evidence, or explicitly out of scope with approved rationale. No silent omission, stub, unfinished marker, or placeholder counts.
- Java semantics for values, errors, ordering, state, concurrency, serialization, reflection metadata, resources, and side effects are preserved unless an intentional, documented change is approved.
- Kotlin-native design may replace Java mechanics, but it must not reduce capability.
- Completion is not declared until `kotlin-java-migration-testing` passes the full source-suite and differential gates.

## Required workflow

### 1. Freeze scope and baselines

Record source/target commits, Java/JDK/Gradle/Kotlin versions, modules, generated sources, supported platforms, feature flags, external services, and exclusions. Capture the Java build and test baseline before implementation.

### 2. Build the source ledger

Use package/class discovery plus parser or compiler metadata. Track at least:

```text
java_key | kind | target_path | target_symbol | status | evidence | notes
```

Method overloads require full signatures. Nested types and default/interface methods are separate rows. Reconcile the ledger in CI so new Java objects cannot appear unnoticed.

### 3. Map architecture and semantics

- Maven/Gradle modules become coherent Gradle Kotlin modules, not arbitrary file buckets.
- `CompletableFuture`/Reactor map to suspend/Flow only after cancellation, ordering, backpressure, scheduler, and error semantics are specified.
- Jackson, reflection, annotations, service loading, proxies, synchronization, thread locals, and checked exceptions need explicit target designs.
- Preserve Java-call-site ABI where compatibility is required; otherwise document the Kotlin-first API and adapter boundary.
- Keep one Kotlin source file per primary migrated Java object when traceability benefits, but allow idiomatic Kotlin organization when the ledger remains exact.

Read [Kotlin migration adapter](references/kotlin-migration-adapter.md) before choosing framework mappings.

### 4. Implement in vertical slices

For each slice: migrate contracts, production behavior, source tests, copied assets, differential cases, and Kotlin-specific tests together. Do not finish all production code before beginning parity testing.

### 5. Preserve documentation

Translate semantic Javadoc, parameter/return/error contracts, thread-safety notes, lifecycle rules, and compatibility constraints into KDoc. Avoid comments that merely restate syntax.

### 6. Run gates

```bash
./gradlew --no-daemon compileKotlin compileTestKotlin
./gradlew --no-daemon test
./gradlew --no-daemon check
```

Then run the dedicated `<project>-test` module and complete Java/Kotlin differential suite defined by `kotlin-java-migration-testing`.

## Status reporting

Report separate denominators for production objects, members, source test methods/cases, assets, differential cases, and Kotlin-only obligations. Never collapse these into one percentage, and never use coverage as the migration-completion percentage.
