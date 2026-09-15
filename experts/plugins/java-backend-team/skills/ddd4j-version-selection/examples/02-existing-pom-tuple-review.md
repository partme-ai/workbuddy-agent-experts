# Example 2 — Reviewing an existing project's version tuple (read-only)

## Prompt

> Here's our POM (Java 8 toolchain, Spring Boot 2.7, ddd4j-core 1.0.x, Spring Cloud 2021.0.x). An architect review claimed our combination is "unsupported". Check it read-only — no changes.

## What the skill should do

1. Read the actual POM fields — JDK target, Boot parent, ddd4j coordinates, Cloud train — not the review's paraphrase of them.
2. Check each pair against the compatibility matrix: Boot 2.7.x ↔ ddd4j 1.0.x; Cloud 2021.0.x ↔ Boot parent 2.7.x ↔ ddd4j 1.0.x.
3. Verify the toolchain claim: this tuple stays Maven 3 / POM 4.0.
4. Grade evidence: matrix SOURCE read; remote consumability and CI not checked in a read-only review.
5. Return the verdict in the four-category shape so the review dispute is settled by the tuple, not by opinion.

## Expected output

```
Tuple under review: JDK 8 · Boot 2.7.18 · Cloud 2021.0.9 · ddd4j 1.0.x ·
Maven 3 / POM 4.0

Matrix check (SOURCE, re-read this session):
  - Boot 2.7.x ↔ ddd4j-boot 2.7.x ↔ ddd4j 1.0.x   → supported
  - Cloud 2021.0.x primary combination: Boot parent 2.7.x, ddd4j 1.0.x → supported
  - toolchain: Maven 3 / POM 4.0                   → consistent

Verdict: RECOMMENDED-class combination per matrix. The "unsupported" claim is
not reproducible from the current matrix.

Not verified (read-only): remote artifact presence, CI history — UNVERIFIED,
not inferred either way.
```

## Failure the skill must avoid

Settling the dispute from memory of "some matrix somewhere." Stale-table recall is exactly how false "unsupported" verdicts propagate; the matrix must be re-read with a date/SHA and the unverified rows left unverified.
