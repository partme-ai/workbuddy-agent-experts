---
name: swift-stable
license: Apache-2.0
description: Implement and diagnose stable Swift language semantics including value and reference types, optionals, generics, protocols, existentials, ownership, access control, enums, pattern matching, closures, error handling, Codable boundaries, and Objective-C interoperability. Use for Swift source changes and compiler errors; combine with package, concurrency, testing, review, or migration skills as needed.
---

# Swift Stable

Use this skill as the language-semantic foundation. Respect the project's Swift tools version, supported platforms, strict-concurrency mode, and library-evolution contract.

## Before changing code

1. Inspect `Package.swift`, Xcode project settings when present, CI, and compiler flags.
2. Record Swift tools/compiler version, platforms, target architectures, language mode, strict concurrency, and library evolution.
3. Compile the smallest affected target before diagnosing source semantics.
4. Load `swift-package-manager` for package topology and `swift-concurrency` for actor/task behavior.

## Language rules

- Choose `struct` for independent value semantics and `class` only when shared identity, inheritance, or Objective-C constraints are real requirements.
- Model absence with optionals; avoid force unwraps and forced casts outside proven invariants with explicit failure behavior.
- Prefer exhaustive enums and pattern matching for closed domains.
- Distinguish `some Protocol`, `any Protocol`, and generic constraints by ownership, performance, and API evolution needs.
- Preserve `Equatable`, `Hashable`, ordering, Codable shape, error, and collection semantics when changing representations.
- Make access control intentional. Public API includes generic constraints, associated types, actor isolation, `Sendable`, and thrown errors.
- Use copy-on-write or immutable snapshots when mutable storage crosses trust or concurrency boundaries.
- Keep Objective-C bridging at adapters; do not leak implicitly unwrapped optionals into the core model.

## Workflow

1. Reproduce compiler or behavioral failure.
2. Classify it as optionality, ownership, generic/existential modeling, overload resolution, ABI, or configuration.
3. Make the minimum type-safe semantic correction.
4. Add a regression test for observable behavior.
5. Run formatting policy, build, tests, and target-specific gates.

```bash
swift build
swift test
```

Never silently raise platform deployment targets or tools version.

