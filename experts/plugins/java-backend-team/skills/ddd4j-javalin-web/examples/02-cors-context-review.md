# Example 2 — Read-only CORS and context review

## Prompt

> We're about to go to production. Read-only check, please: is our CORS sane, and is the tenant context cleaned up properly on the 6.7.x branch?

## What the skill should do

1. Stay read-only; produce findings with file/line evidence.
2. Read the CORS plugin config: flag `anyHost()` or default wildcard origins, and check credentials/headers/methods are enumerated explicitly.
3. Trace Request/Trace/Tenant Context bind and release sites; verify release on success, exception, and async completion paths.
4. Check the async handlers specifically — context restored on async completion is the path most often missed.

## Expected output

| Check | Finding | Evidence |
|---|---|---|
| CORS origins | `anyHost()` in `WebConfig.java:44` | VIOLATION — production must enumerate origins |
| CORS credentials | `credentials(true)` combined with anyHost | VIOLATION — credentialed wildcard is unusable and unsafe |
| Context bind | Trace+Tenant bound at `ContextFilter.java:28` | OK |
| Context release (success) | `ContextFilter.java:55` | OK |
| Context release (exception) | finally clause covers it | OK |
| Context release (async) | missing in `ReportHandler.java:71` | VIOLATION — tenant leaks to pooled threads |

Plus: what was not verified (no load test executed in this review).

## Failure the skill must avoid

Reporting "CORS is configured and context is handled" because a CORS plugin exists and a filter class is present. The two real violations — `anyHost()` and the missing async release — are visible only by reading the actual configuration and both exit paths.
