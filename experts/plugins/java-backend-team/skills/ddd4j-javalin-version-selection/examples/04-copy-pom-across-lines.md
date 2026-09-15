# Example 4 — Copying a root POM across lines

## Prompt

> Our 6.7.x branch is behind. Just copy the 7.2.x root POM over it so we get the newer plugin versions — it's only build files, right?

## What the skill should do

1. Refuse the copy: the root POM encodes the line's contract (JDK release, Maven model, module layout, ddd4j dependency line), and 6.7.x's tuple is Javalin 6.7/ddd4j 1/JDK 17/Maven 3.
2. Explain that POM 4.1 `<subprojects>` from 7.2.x is not valid on a Maven 3/POM 4.0 line, and that raising the JDK or ddd4j line there is a compatibility break.
3. Offer the correct paths: stay on the 6.7.x contract and cherry-pick plugin updates verified against it, or plan a real line migration with `BuildLineContractTest` evidence.
4. Hand implementation of whichever capability comes next to the matching capability skill.

## Expected output

```
Refused: copying the 7.2.x root POM onto 6.7.x mixes line contracts.

Why it breaks:
  - POM 4.1 <subprojects> requires Maven 4; 6.7.x contract is Maven 3 / POM 4.0 <modules>.
  - The 7.2.x POM pins the ddd4j 3 dependency line; 6.7.x binds ddd4j 1.
  - Compiler release settings target JDK 21 there; 6.7.x is a JDK 17 line.

Evidence status: contract tuples from the version-selection matrix (SOURCE);
per-plugin compatibility on 6.7.x NOT RUN.

Correct paths: (a) verify plugin updates individually against the 6.7.x contract,
or (b) plan an explicit 6.7.x → 7.2.x migration with per-line evidence.
```

## Failure the skill must avoid

Treating "it's only build files" as safe. The root POM is the machine-readable form of the maintenance-line contract, and copying it is the exact mechanical cross-line transfer this skill must prevent.
