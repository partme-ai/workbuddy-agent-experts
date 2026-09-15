# Example 1 — New project line selection

## Prompt

> We're starting a greenfield service. The org standardizes on JDK 17 and we build with Maven 3.9. Which ddd4j-boot line should we adopt, and what parent/BOM should we pin?

## What the skill should do

1. Treat Spring Boot version and JDK as the entry constraints and match them against the 13-line matrix (`config/consistency/ddd4j-boot-build-matrix.tsv`).
2. Read the matrix rather than guessing from branch names; JDK 17 + Maven 3 excludes every 4.x line.
3. Output the complete Boot→ddd4j→JDK→Maven/POM tuple, not just the Boot version.
4. Prefer the highest primary combination the organization supports and that is remotely consumable.
5. State the evidence status and what remains unverified (no build or consumption has happened yet).

## Expected output

| Line | Spring Boot | ddd4j | JDK | Maven/POM |
|---|---|---|---:|---|
| 3.5.x | 3.5.16 | 2.0.x | 17 | 3/4.0 |

Rationale: JDK 17 admits every 3.x line; Maven 3 / POM 4.0 excludes the 4.x lines, which require Maven 4 / POM 4.1. The 3.5.x line is the highest Boot line that fits.

Evidence status: SOURCE (matrix read). TEST/CI/PUBLISHED/CONSUMED — NOT RUN until a build and a clean-cache consumption are performed on the chosen line.

## Failure the skill must avoid

Recommending the 4.1.x line because it is newest, then discovering at build time that Maven 4 / POM 4.1 is required. The tuple must be checked as a whole — Boot, ddd4j, JDK, Maven, and POM model together.
