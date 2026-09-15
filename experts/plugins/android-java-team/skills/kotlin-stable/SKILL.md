---
name: kotlin-stable
license: Apache-2.0
description: Implement and diagnose stable Kotlin language semantics for JVM projects, including null safety, types, generics, variance, classes, interfaces, sealed hierarchies, delegation, exceptions, and Java interoperability. Use for Kotlin source changes and compiler errors; combine with specialized build, coroutine, testing, review, or migration skills when those domains are present.
---

# Kotlin Stable

Use this skill as the language-semantic foundation. Preserve the project language level and JVM target instead of assuming the newest compiler.

## Before changing code

1. Inspect `settings.gradle.kts`, `build.gradle.kts`, version catalogs, `gradle.properties`, and Java toolchain declarations.
2. Record Kotlin plugin version, language/API version, JVM target, JDK, enabled compiler plugins, and target platforms.
3. Compile the smallest affected module before diagnosing source semantics.
4. Load `kotlin-gradle-build` for build configuration and `kotlin-coroutines` for suspend/Flow behavior.

## Language rules

- Model absence with nullable types only where absence is a real domain state. Avoid `!!` and unchecked casts.
- Prefer immutable `val`, read-only collection interfaces, data classes for value semantics, and sealed types for closed result domains.
- Distinguish read-only collections from immutable implementations; copy at trust boundaries when callers must not mutate state.
- Apply declaration-site variance deliberately. Do not hide an incorrect type model behind star projections.
- Use extension functions for behavior that is coherent with the receiver; do not use them as a global utility namespace.
- Preserve equality, hash, ordering, exception, serialization, and Java-call-site contracts when converting types.
- Treat platform types from Java as untrusted nullable boundaries. Validate once and expose explicit Kotlin types internally.
- Use `@JvmName`, `@JvmStatic`, `@JvmOverloads`, wildcards, and checked-exception annotations only when a verified Java ABI requires them.
- Avoid clever scope-function chains. Choose `let`, `run`, `apply`, `also`, or `with` only when receiver/result semantics make the code clearer.

## Workflow

1. Reproduce the compiler or behavioral failure.
2. Identify whether the defect is type modeling, nullability, variance, overload resolution, ABI, or build configuration.
3. Make the minimum semantic correction without weakening types.
4. Add a regression test that observes public behavior.
5. Run module compilation, tests, static analysis, then the affected project gate.

## Quality gate

```bash
gradle --no-daemon compileKotlin compileTestKotlin
gradle --no-daemon test
gradle --no-daemon check
```

Use the repository wrapper (`./gradlew`) when present. Never silently raise language level, JVM target, or JDK.

