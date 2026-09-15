# Example 3 — Remote consumability proof

## Prompt

> We picked the 2.0.x line and it builds fine on my laptop. Can we tell the platform team it's ready to consume?

## What the skill should do

1. Refuse to treat a green local build as proof — a warm local cache can satisfy every resolution from artifacts that were never published.
2. Require layered evidence: build, CI on the final SHA, publish, then consumption from the private repository.
3. Run the consumption check with an isolated clean cache (`-U`) so no locally installed SNAPSHOT can fake availability.
4. Report each evidence level as REACHED, NOT RUN, or BLOCKED — never silently upgrade a claim.

## Expected output

```
Line: 2.0.x (Boot 3.5.16 / ddd4j 2.0.x / JDK 17 / Maven 3 / POM 4.0)

Evidence ladder:
  BUILD     REACHED  — ./mvnw verify on the selected line
  CI        REACHED  — green run for SHA <sha>
  PUBLISHED REACHED  — artifacts visible in the private repository
  CONSUMED  NOT RUN  — clean-cache (-U) consumption pending

Verdict: NOT ready. A laptop build with a warm cache proves nothing about
remote availability. Run the -U consumption check from a clean environment.
```

## Failure the skill must avoid

Answering "yes, it builds locally, so it's consumable." The whole point of the evidence ladder is that warm-cache false greens are the standard way a "ready" line turns out to have never been published.
