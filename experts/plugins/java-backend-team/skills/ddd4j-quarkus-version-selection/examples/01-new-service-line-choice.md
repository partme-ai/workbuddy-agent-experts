# Example 1 — New service, choose the line

## Prompt

> We're starting a new Quarkus service. The org standard is JDK 21 and Maven 4. Which ddd4j-quarkus line should we pick, and what exact versions go with it?

## What the skill should do

1. Fix the maintenance line first — JDK 21 + Maven 4 selects the `4.0.x` line.
2. Output the complete tuple: 4.0.x → ddd4j 3.0.x / JDK 21 / Maven 4 / Quarkus Platform 3.38.2.
3. State explicitly that 4.0.x does **not** mean Quarkus Platform 4; the platform version must be confirmed from `quarkus-bom.version` in the actual checkout.
4. List the verification commands (`git branch`, `java -version`, `./mvnw -version`) and the evidence tiers still to be proven (build, tests, CI, remote consumption).
5. Note what was not verified: no checkout was inspected, so all statuses start at SOURCE-pending.

## Expected output

```
Selected line: 4.0.x
Tuple: ddd4j-quarkus 4.0.x → ddd4j 3.0.x | JDK 21 | Maven 4 (POM model 4.x) | Quarkus Platform 3.38.2

Verification plan:
  - git branch / java -version / ./mvnw -version on the target checkout
  - quarkus-bom.version read from the root POM (authoritative, not the line name)
  - clean build + tests, CI on the final SHA, clean-cache (-U) consumption

Evidence status: NOT VERIFIED — no checkout provided.
Missing: repository path of the new service; how to provide: repo URL or workspace path.
```

## Failure the skill must avoid

Answering "4.0.x means Quarkus 4, so pin Platform 4.x." That misreads the line name — the whole reason the skill exists is that 4.0.x builds on Quarkus Platform 3.38.2.
