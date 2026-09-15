---
name: swift-java-migration
license: Apache-2.0
description: Migrate Java systems to Swift without semantic simplification by inventorying every production object and member, preserving public behavior, mapping Java runtime and frameworks deliberately, implementing Swift-native code, and maintaining an auditable migration ledger. Use for Java-to-Swift ports, rewrites, compatibility layers, and migration-completeness work; pair with swift-java-migration-testing for proof.
---

# Java to Swift Migration

The target is equivalent capability and behavior, not line-by-line resemblance. Compiling Swift is an intermediate checkpoint only.

## Non-negotiable completion contract

- Record every in-scope Java class, interface, enum, record, annotation, nested type, constructor, method, and externally visible contract.
- Every record is `IMPLEMENTED`, `ADAPTED` with evidence, or explicitly excluded with approved rationale. Stubs, `fatalError`, empty bodies, placeholders, and silent omissions do not count.
- Preserve values, errors, ordering, state, concurrency, serialization, resources, and side effects unless an intentional change is approved.
- Swift-native architecture may replace Java mechanics but cannot reduce capability.
- Do not declare completion before `swift-java-migration-testing` passes full source-test and differential gates.

## Workflow

### 1. Freeze scope and baselines

Record source/target commits, Java and Swift tools, modules/targets, generated sources, platforms, feature flags, external dependencies, and exclusions. Capture the Java build/test baseline first.

### 2. Build the source ledger

Track at least:

```text
java_key | kind | target_path | target_symbol | status | evidence | notes
```

Use full method signatures for overloads. Track nested types, annotations with runtime meaning, and interface defaults independently. Reconcile the ledger in CI.

### 3. Design semantic adapters

- Map Java modules/packages to coherent SwiftPM targets and modules.
- Map interfaces to protocols only when associated types, existential use, identity, and default implementations remain valid.
- Map `CompletableFuture`/Reactor to async/await or AsyncSequence only after cancellation, ordering, backpressure, scheduling, and error semantics are specified.
- Replace reflection, annotations, service loading, proxies, synchronization, thread locals, and checked exceptions with explicit registries, generated metadata, actors/locks, task context, and typed errors.
- Preserve wire/storage schemas independent of the in-memory Swift representation.

Read [Swift migration adapter](references/swift-migration-adapter.md) before selecting mappings.

### 4. Implement vertical slices

Migrate contract, production behavior, Java tests, copied assets, differential cases, and Swift-specific tests together. Do not postpone parity testing until all source files are translated.

### 5. Preserve documentation

Translate semantic Javadoc, parameter/return/error contracts, thread-safety notes, lifecycle rules, and compatibility constraints into Swift documentation comments.

### 6. Run gates

```bash
swift build
swift test
```

Then run the dedicated `<project>-test` acceptance package/target and complete Java/Swift differential suite.

## Status reporting

Report separate denominators for production objects, members, source test cases, assets, differential cases, and Swift-only obligations. Never collapse them into one percentage or substitute coverage for migration completeness.

