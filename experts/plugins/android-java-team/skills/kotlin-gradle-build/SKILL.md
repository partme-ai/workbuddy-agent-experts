---
name: kotlin-gradle-build
license: Apache-2.0
description: Design, repair, and validate Kotlin Gradle builds using Kotlin DSL, version catalogs, Java toolchains, multi-module boundaries, dependency scopes, compiler options, reproducible CI, publishing, and cache-safe tasks. Use for settings.gradle.kts, build.gradle.kts, gradle.properties, wrapper, module layout, dependency, toolchain, or CI problems.
---

# Kotlin Gradle Build

Own the build graph and reproducibility boundary; defer source semantics to `kotlin-stable` and behavioral test design to `kotlin-testing`.

## Inspect first

- Read wrapper properties, settings, root and module builds, version catalogs, convention plugins, and CI workflows.
- Record Kotlin Gradle plugin, Gradle, AGP if present, Java toolchain, JVM target, repositories, and dependency locking policy.
- Run `gradle projects`, `gradle tasks`, and dependency insight only for the relevant configuration.
- Verify versions against official compatibility documentation before upgrades.

## Build rules

- Prefer the checked-in Gradle wrapper for projects; keep wrapper checksum validation enabled in CI.
- Use Kotlin DSL and convention plugins for shared policy. Keep root builds declarative.
- Declare Java toolchains and Kotlin compiler options explicitly; align `jvmTarget` with the selected runtime contract.
- Centralize versions in a catalog or coherent platform, but do not obscure ownership of dependency scopes.
- Use `api` only for types exposed by the public ABI; otherwise prefer `implementation`.
- Make custom tasks lazy, cache-correct, and explicit about inputs, outputs, environment, and side effects.
- Keep credentials in Gradle providers or CI secrets. Never write tokens into source, properties committed to Git, logs, or generated metadata.
- Separate production modules from the dedicated `<project>-test` whole-project acceptance module used by migrations.

## Multi-module pattern

```text
project/
├── settings.gradle.kts
├── build-logic/
├── core/
├── adapters/
└── project-test/       # cross-module acceptance and source-parity suite
```

## Verification

```bash
./gradlew --no-daemon projects
./gradlew --no-daemon check
./gradlew --no-daemon build
```

For publishing, add artifact inspection, reproducible metadata, signing, and a clean consumer-project test. Do not accept a build that works only from an IDE.

