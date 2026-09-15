---
name: swift-package-manager
license: Apache-2.0
description: Design, repair, and validate Swift Package Manager manifests, products, targets, dependencies, resources, plugins, platform constraints, binary targets, build settings, test topology, CI, and publishing. Use for Package.swift, Package.resolved, Sources, Tests, Plugins, target layout, dependency resolution, or SwiftPM build failures.
---

# Swift Package Manager

Own package topology and reproducibility. Defer source semantics to `swift-stable` and behavioral test design to `swift-testing`.

## Inspect first

- Read `Package.swift`, resolved dependencies, source/test/resource layout, plugins, generated code, and CI.
- Record tools version, compiler, platforms, products, targets, conditions, unsafe flags, and dependency pinning policy.
- Run `swift package describe` and inspect the affected target graph.
- Verify manifest APIs and platform/compiler requirements against official Swift documentation before upgrading.

## Design rules

- Give each target one coherent responsibility and explicit dependencies.
- Expose libraries/executables through products only when consumers need them.
- Declare resources explicitly and test lookup through `Bundle.module`.
- Avoid unsafe flags in reusable products; document unavoidable C/C++ linker and header boundaries.
- Keep generated sources deterministic and plugins explicit about inputs, outputs, permissions, and tools.
- Do not commit credentials. Use CI secret stores and environment/provider boundaries.
- Separate production targets from a dedicated `<project>-test` acceptance package or clearly isolated integration test target for large migrations.
- Validate macOS/Linux behavior when the package claims both; Apple-framework imports require conditional boundaries.

## Verification

```bash
swift package describe
swift package resolve
swift build
swift test
```

For a published library, add clean consumer-package compilation, API compatibility review, symbol/ABI checks where promised, and artifact inspection.

