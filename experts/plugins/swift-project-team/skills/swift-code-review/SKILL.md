---
name: swift-code-review
license: Apache-2.0
description: Review Swift changes for correctness, API compatibility, ownership, concurrency, memory safety, Codable and Objective-C bridges, security, performance, test quality, and SwiftPM integration. Use when asked to review, audit, assess risk, or explain defects; report evidence-backed findings without changing code unless a fix is explicitly requested.
---

# Swift Code Review

Lead with actionable findings ordered by severity. A review is not a narration of the diff.

## Evidence workflow

1. Read the change, surrounding contracts, callers, manifest, platform conditions, and relevant tests.
2. Reproduce or statically trace each suspected defect.
3. Check optionals, value/reference semantics, ARC cycles, errors, Codable shape, public ABI/API, actor isolation, Sendable crossings, cancellation, resources, and C/Objective-C boundaries.
4. Confirm tests would fail for plausible defects and use production paths.
5. Report location, trigger, impact, and the smallest credible remedy.

## Severity

- Critical: data loss, exploitable security defect, broad outage, or irreversible compatibility break.
- High: common wrong result, race/leak, broken public contract, or migration parity failure.
- Medium: bounded correctness, resilience, performance, or maintainability risk.
- Low: concrete improvement with limited operational impact.

## Swift-specific checks

- Force unwrap/cast, implicitly unwrapped Objective-C values, lifetime and retain-cycle errors.
- Incorrect struct/class choice, Hashable/Equatable drift, mutation through shared storage.
- Codable key/default/null shape changes and error erasure.
- Unstructured/detached task leaks, actor reentrancy assumptions, unchecked Sendable, swallowed cancellation.
- SwiftPM target/resource errors, unsafe flags, unsupported platform imports, and secret exposure.

If no actionable defect is found, say so and state remaining verification gaps.

