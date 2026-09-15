# Example 2 — Read-only tuple consistency audit

## Prompt

> Our service claims to be on the ddd4j-quarkus 3.3.x line. Can you do a read-only check that the POM and toolchain actually match before our audit?

## What the skill should do

1. Stay read-only — this is an audit, not a migration.
2. Read the root POM: parent version, `quarkus-bom.version`, POM model, and ddd4j versions.
3. Run or request the toolchain evidence: `git branch`, `java -version`, `./mvnw -version`.
4. Compare each value against the 3.3.x contract (ddd4j 2.0.x / JDK 17 / Maven 3 / Quarkus Platform 3.37.4) and report per-row verdicts.
5. Mark anything not directly inspected as unverified instead of assuming.

## Expected output

| Check | Contract (3.3.x) | Found | Verdict |
|---|---|---|---|
| ddd4j version | 2.0.x | 2.0.7 | MATCH |
| Quarkus Platform | 3.37.4 | 3.20.3 | **MISMATCH** |
| JDK | 17 | 17 (from `java -version`) | MATCH |
| Maven | 3 | 3.9.9 (from `./mvnw -version`) | MATCH |
| POM model | Maven 3 model | 4.0 | MATCH |

Finding: `quarkus-bom.version` points at Platform 3.20.3, not the line's 3.37.4. Everything else satisfies the 3.3.x contract.
Evidence: SOURCE read (root POM) + toolchain output. Tests and CI NOT RUN for this SHA.

## Failure the skill must avoid

Reporting "consistent with 3.3.x" after reading only the branch name. The branch says 3.3.x; the BOM says 3.20.3 — only the POM is authoritative.
