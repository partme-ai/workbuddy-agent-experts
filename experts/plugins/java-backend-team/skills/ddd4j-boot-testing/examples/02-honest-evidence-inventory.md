# Example 2 — Honest evidence inventory

## Prompt

> Management wants a "testing status" slide for the 3.x integration. Half our container tests couldn't run in the office because Docker Desktop wasn't running. How do we report this?

## What the skill should do

1. Refuse to fold skips into passes: Docker-unavailable suites are BLOCKED, and a blocked suite proves nothing either way.
2. Fix the line, then inventory every suite in the module's `src/test`: context, slice, contract, and container-based.
3. Classify each as PASS, FAIL, BLOCKED (Docker/environment), or SKIPPED (deliberately not run), with the line/JDK/Maven used.
4. Map the inventory against the feature matrix so coverage gaps are visible, not averaged away.
5. State exactly what re-run is needed to clear the blocked items.

## Expected output

```
Testing inventory (line 3.x, JDK 17, Maven 3):
  context/slice suites      42/42 PASS
  HTTP contract suite       18/18 PASS
  DB round-trip (container) 12/12 PASS
  Redis round-trip          BLOCKED — Docker unavailable (0 run)
  Broker round-trip         BLOCKED — Docker unavailable (0 run)

Coverage vs feature matrix: wiring + HTTP covered; Redis and broker
behavior UNVERIFIED on this line.

To clear: run the two container suites on a Docker-enabled runner; until
then "integration verified" is NOT a supported claim.
```

## Failure the skill must avoid

Reporting "96% green" by counting blocked suites as skipped-and-fine. The two blocked suites are precisely the ones that cover the outage-prone integrations — hiding them turns the slide into a liability.
