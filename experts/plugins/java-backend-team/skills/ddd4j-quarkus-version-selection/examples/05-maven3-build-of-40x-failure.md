# Example 5 — CI cannot build the 4.0.x line with Maven 3

## Prompt

> Our CI agent runs Maven 3.9 and JDK 17. Building the ddd4j-quarkus 4.0.x branch fails immediately with POM model errors. The POM must be broken — can you fix it?

## What the skill should do

1. Diagnose the failure as a toolchain mismatch, not a POM defect: 4.0.x requires Maven 4 and JDK 21 as part of the line contract.
2. Confirm by reading the root POM model on the 4.0.x branch and the CI agent's `mvn -version` output.
3. State the fix on the environment side: provision Maven 4 + JDK 21 on the CI agent (or, if Maven 3 must stay, the 3.3.x line is the compatible target — ddd4j 2.0.x / JDK 17 / Quarkus Platform 3.37.4).
4. Warn against "fixing" the POM by downgrading its model — that would move the branch off its line contract and break the rest of the build matrix.
5. List remaining verification after the toolchain is fixed (build, tests, CI for the final SHA).

## Expected output

```
Root cause: environment, not POM.
  - 4.0.x line contract: ddd4j 3.0.x / JDK 21 / Maven 4 / Quarkus Platform 3.38.2
  - CI agent: Maven 3.9.9 / JDK 17   ← mismatch

Options:
  1. (Recommended) CI agent gets Maven 4 + JDK 21; keep the 4.0.x POM untouched.
  2. If Maven 3 is a hard constraint, target the 3.3.x line instead — this is a
     line change, not a patch.

Do NOT downgrade the 4.0.x POM model to satisfy Maven 3; that breaks the line contract.
Evidence: CI log read; POM read. Post-fix build NOT RUN.
```

## Failure the skill must avoid

Editing the POM model down to Maven 3 compatibility. The failure is the toolchain violating the line contract, and "fixing" the POM silently moves the branch out of the supported matrix.
