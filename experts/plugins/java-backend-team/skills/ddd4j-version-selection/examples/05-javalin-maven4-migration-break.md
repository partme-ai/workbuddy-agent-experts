# Example 5 — Diagnosing the Javalin upgrade that broke the build

## Prompt

> We upgraded ddd4j-javalin from 7.1.x to 7.2.x and now CI fails with a POM error about `<subproject>` before anything even compiles. Developers on Maven 3.9 can't build either. What did the upgrade actually change?

## What the skill should do

1. Diagnose from the error: `<subprojects>`/`<subproject>` syntax = POM 4.1 = Maven 4 territory — 7.2.x is the line that crossed from Maven 3 / POM 4.0 to Maven 4 / POM 4.1.
2. Confirm the tuple change: 7.1.x was Javalin 7.1.0 / ddd4j 2.0.x / JDK 17 / Maven 3; 7.2.x is Javalin 7.2.3 / ddd4j 3.0.x / JDK 21 / Maven 4 — the upgrade silently changed four fields, not one.
3. Lay out the real options: (a) adopt Maven 4 + JDK 21 deliberately, (b) stay on 7.1.x and treat 7.2.x as incompatible for now, or (c) plan a staged migration JDK first.
4. Verify remote consumability for whichever option is chosen — the clean-cache gate applies again.
5. Record the decision in the four-category output so the next team inherits the analysis, not the surprise.

## Expected output

```
Diagnosis: the 7.1.x → 7.2.x upgrade crossed the toolchain boundary.

Field diff (SOURCE, matrix re-read):
  ddd4j-javalin 7.1.x: Javalin 7.1.0 · ddd4j 2.0.x · JDK 17 · Maven 3 / POM 4.0
  ddd4j-javalin 7.2.x: Javalin 7.2.3 · ddd4j 3.0.x · JDK 21 · Maven 4 / POM 4.1
  → the `<subproject>` POM error is Maven 3 reading a POM 4.1 aggregator.

Options:
  a) adopt Maven 4 + JDK 21 (deliberate toolchain migration, all CI images
     updated first)
  b) pin 7.1.x — 7.2.x classified INCOMPATIBLE for this project today
  c) staged: JDK 21 first, then Maven 4, then 7.2.x

Not verified for (a): clean-cache CONSUMED on 7.2.x — pending.
```

## Failure the skill must avoid

Answering "install Maven 4 and move on." That skips the second half of the tuple — ddd4j 2.0.x → 3.0.x also moved JDK 17 → 21 and POM semantics — and produces a project that builds on one developer machine and fails everywhere the toolchain wasn't migrated.
