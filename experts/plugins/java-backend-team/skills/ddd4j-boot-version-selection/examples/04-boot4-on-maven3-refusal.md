# Example 4 — Boot 4 on a Maven 3 toolchain (boundary case)

## Prompt

> Leadership wants us on the newest line, 4.1.x. Our CI images still have Maven 3.9 and JDK 17. Just tell us which parent version to set.

## What the skill should do

1. Decline to name a parent version: 4.1.x pairs with ddd4j 3.0.x, JDK 21, and Maven 4 / POM 4.1 — the proposed toolchain satisfies none of the tuple.
2. State that the selection should not be made on "newest" alone; the JDK and the Maven model are hard gates, not preferences.
3. Lay out what adopting 4.1.x actually requires: JDK 21 toolchain, Maven 4, POM model 4.1, subproject layout.
4. Offer the nearest reachable alternative (highest 3.x line on JDK 17 / Maven 3) and the gap list as `missing:` items.
5. Not guess or soften the constraint to satisfy the request.

## Expected output

```
Requested: 4.1.x
Blocked:   4.1.x requires JDK 21 + Maven 4 / POM 4.1 / subprojects.
           Current toolchain: JDK 17 + Maven 3.9 — two of five tuple slots fail.

Options:
  a) Stay on 3.5.x (Boot 3.5.16 / ddd4j 2.0.x / JDK 17 / Maven 3 / POM 4.0).
  b) Provision JDK 21 + Maven 4 CI images first, then re-run selection for 4.1.x.

missing: JDK 21 and Maven 4 toolchain images; how to provide: updated CI base
image, then this skill re-selects and verifies the 4.1.x tuple.
```

## Failure the skill must avoid

Handing over a parent version string for 4.1.x because the user asked for it. That guarantees a broken build and hides that the toolchain, not the POM line, is the blocker.
