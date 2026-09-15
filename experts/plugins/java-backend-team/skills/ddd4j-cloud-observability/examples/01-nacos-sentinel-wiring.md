# Example 1 — Wiring Nacos registration and Sentinel rules

## Prompt

> Put our new ddd4j-cloud service on Nacos for discovery/config and add Sentinel rate limiting on the order endpoints. We need it to actually work, not just boot.

## What the skill should do

1. Fix the combination with `ddd4j-cloud-version-selection`, then use the line's nacos/sentinel extensions and their configuration keys.
2. Configure Nacos registration and configuration with the real server address; verify registration actually appears in the registry.
3. Configure Sentinel rules on the order endpoints and verify the rule-push channel is connected — rules on the classpath alone never activate.
4. Keep liveness independent of Nacos/Sentinel; aggregate them into readiness instead.
5. Specify the verification: registry entry visible, a rule provably triggering under load, and probe behavior when each dependency is down.

## Expected output

```
Nacos: registration verified — service visible in registry (<server>)
Sentinel: flow rules on GET/POST /orders; rule trigger verified by
  load probe (429/degrade observed) — channel connected
Probes: liveness = process only; readiness aggregates Nacos + Sentinel
  (+ DB)

Pending: dependency-down drill (Nacos down, Sentinel down) to prove
readiness flips.
```

## Failure the skill must avoid

Declaring success at clean startup with the dependencies in the POM. Classpath presence does not prove reachability — the service boots green with Nacos down and registers nothing, which is exactly what the registry check catches.
