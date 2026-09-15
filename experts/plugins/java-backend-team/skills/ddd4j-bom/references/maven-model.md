# Maven Model

> Collection date: 2026-09-11.

| ddd4j line | JDK | Maven | model | Aggregator |
|---|---:|---|---|---|
| 1.0.x | 8  | 3 | 4.0.0 | `<modules>`     |
| 2.0.x | 17 | 3 | 4.0.0 | `<modules>`     |
| 3.0.x | 21 | 4 | 4.1.0 | `<subprojects>` |

Run `scripts/test_maven4_model_contract.py` to validate the model rules. Do not break older toolchains to unify the format.

## Current Validation Notes

When `verify_owned_source` was run in the current 3.0.x checkout on 2026-09-11, the scan
also reached `.superpowers/sdd/.../task-4-baseline-2` and reported a relocated Quarkus
test artifact under `test_repository_has_no_owned_warning_sources`. This is validation
scope pollution: until the script's exclude rules are fixed or a clean checkout is used,
the Maven 4 owned-source gate must be marked `BLOCKED`, not `PASS`.
