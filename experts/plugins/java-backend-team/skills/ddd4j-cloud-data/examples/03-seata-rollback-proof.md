# Example 3 — Proving Seata rollback with a real database

## Prompt

> We need evidence for the go-live checklist: prove that if the second service fails mid-flow, the first service's writes roll back.

## What the skill should do

1. Run the flow against real MySQL and two real services — mocked repositories cannot produce rollback evidence.
2. Force the failure deliberately: make the second service throw mid-transaction and observe the global rollback.
3. Verify the Seata transaction coordinator is actually reachable during the test — a down coordinator can make the flow "pass" while silently running without global transaction control.
4. Test the commit path too, plus idempotent retry of the failed item after rollback.
5. Grade evidence per tier and mark what did not run (e.g. network-partition behavior) as NOT VERIFIED.

## Expected output

```
Seata evidence (real MySQL, two services):
  TC reachable during test        → CONFIRMED
  second service fails mid-flow   → global rollback: PASS (both sides clean)
  happy path commit               → PASS
  retry after rollback            → PASS (idempotent)
  TC unreachable scenario         → NOT VERIFIED (not exercised)

Evidence: TEST (real round-trip). Remaining gap: coordinator-failure
behavior — schedule a chaos run or accept the risk explicitly.
```

## Failure the skill must avoid

Reporting rollback "works" from a test where the coordinator was never reachable and each service simply committed independently. Without confirming TC connectivity, a green test may prove nothing about global transactions at all.
