# Example 4 — Plain Quarkus project, no ddd4j

## Prompt

> Our backend is plain Quarkus — we never adopted ddd4j. Which Quarkus Platform and JDK should we standardize on? I was told there's a version matrix I can use.

## What the skill should do

1. Recognize the boundary: the ddd4j-quarkus matrix only governs projects that consume ddd4j-quarkus adapters.
2. Decline to map a non-ddd4j project onto the 3.3.x/4.0.x tuples — do not use this matrix to pick Quarkus Platform versions for a stack that has no ddd4j dependency.
3. Hand off to generic Java/Quarkus skills and Quarkus Platform documentation for the platform/JDK choice.
4. Offer the correct conditional: if the team later adopts ddd4j-quarkus, this skill selects the line, and at that point JDK 17 + Maven 3 means 3.3.x while JDK 21 + Maven 4 means 4.0.x.
5. Keep the refusal constructive — state what the skill would need to engage (a ddd4j-quarkus dependency in the POM).

## Expected output

```
Boundary: this skill selects ddd4j-quarkus maintenance lines only.
Your POM imports no ddd4j-quarkus artifacts, so the 3.3.x / 4.0.x matrix does not apply.

Handoff: choose the Quarkus Platform and JDK with generic Quarkus/Java guidance.
Re-engage condition: once `io.ddd4j:ddd4j-quarkus-*` appears in your POM, run this
skill with the checkout path; line selection must come first for any ddd4j work.
```

## Failure the skill must avoid

Recommending "4.0.x because it's newest" for a project with no ddd4j dependency — that drags JDK 21/Maven 4/ddd4j 3.0.x constraints onto a stack that never asked for them.
