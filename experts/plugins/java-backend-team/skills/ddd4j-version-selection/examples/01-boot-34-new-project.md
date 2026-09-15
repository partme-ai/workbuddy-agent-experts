# Example 1 — New project on JDK 17 and Spring Boot 3.4

## Prompt

> Greenfield service: JDK 17, Spring Boot 3.4, Maven. Which ddd4j line and Boot adapter do we take, and does the build tool need anything special?

## What the skill should do

1. Lock the ddd4j line by JDK: Java 17 → 2.0.x.
2. Lock the adapter line by Boot: Boot 3.4.x → ddd4j-boot 3.4.x (which itself sits on 2.0.x).
3. Verify the toolchain: 2.0.x / Boot 3.4.x is Maven 3 / POM 4.0 — no Maven 4 needed.
4. Check remote metadata for the concrete `2.0.x` revision and mark verification state honestly.
5. Output the four categories with rationale, not just the recommendation.

## Expected output

| Field | Content |
|---|---|
| Recommended | JDK 17 · Maven 3 / POM 4.0 · ddd4j 2.0.x · ddd4j-boot 3.4.x · Boot 3.4.13 |
| Alternative | Boot 3.5.x line (ddd4j-boot 3.5.x) if 3.4 patch availability is a concern |
| Incompatible | ddd4j 3.0.x (requires Java 21 + Maven 4 / POM 4.1) |
| Unverified | remote SNAPSHOT freshness — metadata query pending |
| Evidence | SOURCE (matrix + POM read); CONSUMED pending clean-cache resolve |

Follow-up: `mvn -U -Dmaven.repo.local=<clean> dependency:go-offline` to upgrade the SNAPSHOT row from UNVERIFIED to CONSUMED.

## Failure the skill must avoid

Recommending ddd4j 3.0.x "because it's newest" — on JDK 17 with Maven 3 that combination cannot build, and the failure surfaces as a POM 4.1 parse error nobody connects to the version choice.
