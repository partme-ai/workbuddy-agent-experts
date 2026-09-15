# Example 1 — Designing the suite for a line upgrade

## Prompt

> We're moving our service from 2021.0.x to 2023.0.x. What's the test plan to be allowed into the release window?

## What the skill should do

1. Fix both combinations with `ddd4j-cloud-version-selection` and record the exact toolchains (Maven/JDK per line).
2. Plan the compatibility suite for the target line — the WebMVC/MySQL pairing first.
3. Plan behavior suites per capability the service uses: context propagation, Feign round-trips, binder tests against the real broker, database round-trips.
4. State which suites need Docker/container infrastructure and what happens to them if it is absent.
5. Define the evidence gate: pass/fail plus the BLOCKED/SKIPPED/NOT VERIFIED inventory, with skips never translating into success.

## Expected output

```
Test plan (2021.0.x → 2023.0.x):
  1. Compatibility: WebMVC/MySQL pairing on target line — required
  2. Context: propagation across sync/async/Reactor/Feign incl.
     exception + pool-reuse paths
  3. Feign: real round-trip (success/error/timeout/retry)
  4. Binder: Kafka publish/consume + ack/retry (real broker)
  5. DB: MySQL round-trip + migration up/down
Container suites: need Docker; if absent → recorded SKIPPED(reason),
NOT silently dropped.
Gate: green report = all executed PASS + honest inventory of the rest.
```

## Failure the skill must avoid

Equating "unit tests pass" with an upgrade-ready suite. Without the WebMVC/MySQL compatibility run and the real-broker/real-DB behavior suites, the plan certifies nothing about the new line.
