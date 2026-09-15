# Example 5 — Sentinel rules never fire though they're configured

## Prompt

> We configured Sentinel flow rules for the order endpoint in our config, the app started cleanly, and yet yesterday's traffic spike blew straight through the limits. No degradation, no blocks. Why?

## What the skill should do

1. Separate the three layers where this fails: rules loaded in the app, the rule-push channel to the Sentinel dashboard/cluster, and actual rule activation on the endpoint.
2. Check the classic cause first: configuration loaded does not equal rules active — if the app never connected to the rule source, the rules exist as config text only.
3. Verify reachability: Nacos/Sentinel presence in the classpath does not mean the server is reachable; startup succeeds while the dependency is down.
4. Verify the rules target the right resource names — a rule on a resource name that the interceptor never produces is silently inert.
5. Prove the fix behaviorally: apply a tiny limit, generate load, observe the block — not just a clean log.

## Expected output

```
Diagnosis:
  - Rules present in config: YES
  - Sentinel dashboard connection: FAILED (connect timeout in logs,
    app continued startup — classpath presence ≠ reachable server)
  - Rule activation: NONE — rules never pushed to the app

Secondary check: resource names in rules vs interceptor names —
  match, so the push channel is the only break.

Fix: correct the dashboard/cluster address + auth; restart; verify by
load probe: limit=5/s → block observed at 6th request. PASS after fix.
Evidence: SOURCE + TEST (load probe post-fix). Pre-fix behavior: NOT
VERIFIED as active.
```

## Failure the skill must avoid

"Verifying" by re-reading the rule configuration and confirming it's syntactically correct. The rules were never delivered — the failure lives in the unconnected push channel that a clean startup log actively hides.
