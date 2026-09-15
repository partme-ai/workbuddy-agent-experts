# Example 2 — Auditing which line a checkout really is

## Prompt

> We inherited a checkout on branch `feature/7.1.x`. Before we touch it, can you verify it actually is the 7.1 line? Read-only please.

## What the skill should do

1. Stay read-only — this is an audit, not a migration.
2. Check each tuple dimension independently: Javalin version from the POM, ddd4j dependency line, JDK required by the compiler config, Maven model (3 `<modules>` versus 4 `<subprojects>`), and Maven Wrapper version.
3. Run or locate `BuildLineContractTest` results for the current SHA; if it cannot run, mark it `NOT RUN`.
4. Compare every finding against the 7.1.x tuple: Javalin 7.1/ddd4j 2/JDK 17/Maven 3.

## Expected output

```
Branch: feature/7.1.x (SHA abc1234)

| Dimension    | Expected (7.1.x) | Found                  | Verdict |
|--------------|------------------|------------------------|---------|
| Javalin      | 7.1              | 7.1.0                  | MATCH   |
| ddd4j line   | 2.0.x            | 2.0.x                  | MATCH   |
| JDK          | 17               | 17 (release flag)      | MATCH   |
| Maven/POM    | Maven 3, POM 4.0 | Maven 3, `<modules>`   | MATCH   |

BuildLineContractTest: NOT RUN (no recent CI run for this SHA).
Verdict: consistent with 7.1.x on source evidence; behavior evidence pending.
```

## Failure the skill must avoid

Answering "the branch is named `feature/7.1.x`, so it's 7.1" without reading the POM, wrapper, and JDK config. The branch name is the one input this skill exists to distrust.
