# Example 5 — Branch renamed but the build never followed

## Prompt

> We renamed our branch to `feature/7.2.x` last sprint during the reorg. Builds pass on my machine, but CI artifacts keep failing the consumers. Something is off — where?

## What the skill should do

1. Treat the mismatch hypothesis seriously: the branch name changed but the build contract may not have. Check every tuple dimension against the 7.2.x expectations (Javalin 7.2, ddd4j 3, JDK 21, Maven 4, POM 4.1 `<subprojects>`).
2. Read the root POM, wrapper, and compiler release settings on the current SHA — the diff between the name and the build is the defect.
3. Run `BuildLineContractTest` for the current SHA to get a per-dimension verdict.
4. Classify the CI consumer failure against the real contract, and list the fix per dimension (wrapper version, POM model, JDK release, dependency line).

## Expected output

```
Symptom: branch feature/7.2.x, local builds OK, CI/consumers fail.

Tuple audit (SOURCE, read):
  - Branch name ............. 7.2.x
  - Maven model ............. POM 4.0 <modules> + Maven 3 wrapper   ← MISMATCH
  - Compiler release ........ 17                                    ← MISMATCH
  - ddd4j dependency ........ 2.0.x                                 ← MISMATCH
  - Javalin ................. 7.1.0                                 ← MISMATCH

Diagnosis: the branch was renamed, but the build is still the 7.1.x contract.
Local builds pass because the local toolchain tolerates it; the CI/publish
gates validate the tuple and reject it.

Fix: complete the migration (wrapper → Maven 4, POM → 4.1 <subprojects>,
release → 21, deps → ddd4j 3 / Javalin 7.2) or rename the branch back to
feature/7.1.x. Re-run BuildLineContractTest and CI for the final SHA.
```

## Failure the skill must avoid

Diagnosing the CI failure as a flaky consumer or a credentials problem. The real defect is a branch name that no longer matches the build contract — the exact false identity this skill exists to catch.
