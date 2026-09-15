# Example 2 — Existing project tuple audit (read-only)

## Prompt

> Before our quarterly audit, can you check whether our service's ddd4j-boot usage is on a consistent version combination? Don't change anything, just report.

## What the skill should do

1. Stay read-only — no edits, no upgrades, just the consistency verdict.
2. Read the project's parent/BOM declarations, the effective JDK (`java -version`), and the Maven/POM model version (`./mvnw -version`, POM `modelVersion`).
3. Compare the observed tuple against the 13-line matrix row by row.
4. Flag any mixing of parent/BOM across ddd4j main lines as a defect, even if the build currently passes.
5. Report missing evidence explicitly instead of assuming it.

## Expected output

```
Observed:   Boot 2.7.18 parent, ddd4j 1.0.x BOM, JDK 8, Maven 3 / POM 4.0
Matrix row: 2.7.x → Boot 2.7.18, ddd4j 1.0.x, JDK 8, Maven 3 / 4.0
Verdict:    CONSISTENT

Warnings:
  - module `legacy-tools` declares a 3.0.x ddd4j import alongside the 1.0.x BOM
    → mixed BOM across main lines; keep the complete tuple.

Evidence: SOURCE (POM + matrix read). Build/CI not re-run — read-only audit.
```

## Failure the skill must avoid

Declaring the project consistent because the top-level POM looks right. A single submodule importing a BOM from another main line is exactly the defect this audit exists to catch.
