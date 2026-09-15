# Example 2 — Read-only auth wiring review

## Prompt

> Security asked for a review of our auth setup before go-live. Read-only. We're on ddd4j-quarkus 3.3.x with Sa-Token.

## What the skill should do

1. Stay read-only and fix the line/SHA (3.3.x → Quarkus Platform 3.37.4 / ddd4j 2.0.x / JDK 17 / Maven 3).
2. Count `SubjectProvider` producers — exactly one primary must exist; flag duplicates.
3. Trace the Subject bind/release pairs and check the exception and async-completion paths, not just the success path.
4. Check `AuthPrincipal` role/permission mapping is explicit and `RolesAllowed` covers the endpoints the security team listed.
5. Scan logs and config dumps for leaked tokens or secrets that must be redacted.

## Expected output

| Check | Finding | Verdict |
|---|---|---|
| SubjectProvider count | one producer | OK |
| Role mapping | roles read from token claim with explicit rules | OK |
| Context release | success path only; exception path leaks Subject | **GAP** |
| RolesAllowed coverage | `/internal/*` endpoints unprotected | **GAP** |
| Secret hygiene | dev profile prints the resolved token secret | **RISK** |

Evidence: SOURCE read of auth wiring and logs. QuarkusTest suites NOT RUN on this SHA.

## Failure the skill must avoid

Green-lighting because "login works". The three gaps above (exception-path leak, unprotected internal endpoints, printed secret) are invisible in a happy-path smoke test and are precisely what the review exists to catch.
