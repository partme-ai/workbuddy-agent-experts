# Example 5 — Diagnosing a rule-engine hang

## Prompt

> Since we let users write their own QLExpress discount rules, the service occasionally pins a CPU at 100% and stops responding. Last time we had to restart the pod. The rules work fine when I test them. What's wrong?

## What the skill should do

1. Match the symptom to the anti-pattern: user-supplied expressions executing without sandbox limits — a rule with an unbounded loop or deep recursion pins the thread.
2. Inspect the integration: is the executor built with function restrictions, accessed-type allowlists, and a timeout — or with the default builder?
3. Explain why hand-testing misses it: the authors' test rules terminate; the hang needs a specific adversarial rule (while(true), huge loops, reflection access).
4. Prescribe the fix: builder-level function/access restrictions, execution timeout, and a rules allowlist for production.
5. Add the regression test: an explicitly adversarial rule (infinite loop) must fail fast with a timeout error, not hang the worker.

## Expected output

```
Diagnosis: QLExpress running without execution limits.

Evidence:
  - Executor built with default builder — no timeout, no type allowlist (SOURCE)
  - User rules submitted via admin API, stored and executed verbatim (SOURCE)
  - Thread dump from incident: parked in rule evaluation loop (ops artifact)

Fix:
  1. restrict callable functions and accessible types via builder permissions
  2. enforce a per-evaluation timeout (rule fails, worker survives)
  3. production rules require review/allowlist

Regression test: while(true){} rule → timeout exception within N ms, service
serves other requests. Status: NOT RUN.
```

## Failure the skill must avoid

Blaming "a bad rule someone wrote" and adding input validation on the rule text. Text filtering cannot enumerate every adversarial expression — the enforcement point is the executor's sandbox limits, not the string.
