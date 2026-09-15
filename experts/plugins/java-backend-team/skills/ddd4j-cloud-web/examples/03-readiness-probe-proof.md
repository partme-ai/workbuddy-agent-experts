# Example 3 — Proving readiness reflects real dependency state

## Prompt

> Our service must not receive traffic when Nacos or the database is unreachable. Prove the readiness probe behaves for each dependency state — we don't trust the config alone.

## What the skill should do

1. Enumerate what readiness aggregates: database, Nacos, Sentinel as applicable to this service, per the web extension's readiness wiring.
2. Test each dependency state independently: up, down, and recovering — asserting the probe flips and recovers.
3. Confirm liveness stays independent of external dependencies so a Nacos blip does not restart pods.
4. Confirm traffic actually stops (platform behavior) when readiness goes false, not just that the endpoint responds 503.
5. Grade evidence per state and mark untested states explicitly.

## Expected output

```
Readiness evidence (probe matrix):
  DB down        → /ready 503, traffic drained   PASS
  Nacos down     → /ready 503, traffic drained   PASS
  Sentinel down  → /ready <result>               NOT RUN
  all recovered  → /ready 200, traffic restored  PASS
Liveness: independent of externals — PASS (no restarts during the drill)

Evidence: TEST (live drill, 3 of 4 states). Remaining: Sentinel state —
schedule or mark NOT VERIFIED in the report.
```

## Failure the skill must avoid

Proving readiness by starting everything healthy and showing a 200. The property being purchased is behavior under failure — a probe only proven in the all-up state is indistinguishable from a hardcoded READY.
