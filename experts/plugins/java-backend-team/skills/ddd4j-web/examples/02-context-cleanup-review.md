# Example 2 — Context cleanup review across three exit paths (read-only)

## Prompt

> Before the pen test, review our WebFlux service for context handling. The pen testers always find the request-context stuff, so let's find it first.

## What the skill should do

1. Stay read-only — audit, don't patch.
2. Enumerate context bind sites (Request/Trace/Tenant/Subject) and their matching release sites.
3. Verify the three exit paths independently: normal completion, exception, async completion (subscription termination on a different thread).
4. Check the error contract while there: statuses stable, cause preserved internally, no stack trace or internal detail in payloads.
5. Check headers/logs for `Authorization`, `Cookie`, and full request bodies.

## Expected output

| Exit path | Bind | Restore | Verdict |
|---|---|---|---|
| Normal completion | filter entry | `doOnComplete` handler | OK |
| Exception | filter entry | missing on `doOnError` ← | violation |
| Async completion | filter entry | missing on cancel/timeout path ← | violation |

Error contract: payload shape stable, but 500 responses embed `exception.getMessage()` from a driver class — internal detail exposed. No `Authorization` logging found.

Verdict: two leak paths plus one error-contract defect — exactly the pen-test surface. Evidence: SOURCE only.

## Failure the skill must avoid

Passing the review because the happy path cleans up. Reactive streams terminate three different ways; pen testers and load tests find the two the review exists to check.
