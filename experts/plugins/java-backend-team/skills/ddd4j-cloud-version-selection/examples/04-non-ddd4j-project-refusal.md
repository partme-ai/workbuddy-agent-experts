# Example 4 — Plain Spring Cloud project, no ddd4j

## Prompt

> Our platform team runs plain Spring Cloud with Spring Boot, no ddd4j. Which ddd4j-cloud maintenance line should we pick for the next upgrade?

## What the skill should do

1. Detect that the project has no ddd4j dependency and say plainly: no ddd4j-cloud line applies.
2. Do not retrofit ddd4j version constraints onto a non-ddd4j codebase.
3. Point the requester to generic Java / Spring Cloud version-selection guidance instead — no `npx skills add` command applies here.
4. If the team genuinely wants to adopt ddd4j, explain that the Cloud→Boot→ddd4j tuple must then be chosen together, and route to this skill's matrix at that point.

## Expected output

```
Finding: the POM declares Spring Cloud + Spring Boot only; no ddd4j coordinates.

Verdict: do not use a ddd4j-cloud line for this upgrade — the ddd4j-cloud
matrix constrains Cloud→Boot→ddd4j together and does not govern a
non-ddd4j project.

Path forward:
  - Without ddd4j: follow upstream Spring Cloud / Spring Boot compatibility
    guidance (generic spring-cloud skills; no ddd4j install).
  - If adopting ddd4j: choose the full Cloud→Boot→ddd4j tuple from the
    eight-line matrix first, then read the matching branch.
```

## Failure the skill must avoid

Recommending a ddd4j-cloud maintenance line "for the Spring Cloud part" of a non-ddd4j project. The ddd4j line is only half of a tuple that also pins Boot and ddd4j; applying it piecemeal invents constraints the project does not have.
