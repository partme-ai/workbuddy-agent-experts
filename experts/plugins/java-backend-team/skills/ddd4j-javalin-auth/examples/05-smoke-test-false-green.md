# Example 5 — The smoke test that blessed an unprotected route

## Prompt

> Our deploy smoke test logs in and hits `/api/orders` and gets a 200, so auth works, right? The pen testers yesterday fetched the same URL with no token at all and also got a 200.

## What the skill should do

1. Diagnose immediately: a smoke test returning 200 does not prove routing or auth behavior — it only proves *a* 200 is reachable. The pen test result means route protection was never registered for that path.
2. Read the route registration and access-manager wiring on the current line: find the path pattern mismatch (`/api/*` registered, route defined as `/api/orders/:id`, or protection attached via `before` on a prefix that doesn't match).
3. Name the classic causes: protection registered after route definition, path pattern too narrow, or the auth module present but its participant never registered into the runtime.
4. Provide the failing contract first: an unauthenticated request to `/api/orders` must return 401 — then fix and re-run both the contract test and the smoke test.

## Expected output

```
Diagnosis: smoke test proves reachability, not protection.
  - Smoke test: valid login → 200 on /api/orders ........ proves routing only
  - Pen test:  no token   → 200 on /api/orders ......... protection NOT enforced

Root cause (SOURCE, 7.1.x): access manager registered via
  app.before("/api/orders", ...)          ← matches exact path only
Routes are defined as /api/orders/:id and /api/orders/list, which the
`before` handler never sees.

Fix (contract-first):
  1. RED: unauthenticated GET /api/orders/list must 401 (currently 200).
  2. Register protection on the /api/* matcher per the 7.2 pattern.
  3. Re-run: anonymous/expired/valid/insufficient-role cases.
```

## Failure the skill must avoid

Concluding "auth works, the pen test must have hit a cached response". The smoke test's 200 is exactly the false green this skill exists to unmask — protection that never runs cannot fail a test that only checks for 200.
