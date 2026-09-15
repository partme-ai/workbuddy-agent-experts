# Example 2 — Auth wiring review (read-only)

## Prompt

> Security review tomorrow. Read-only check please: is our boot auth wiring sane? One framework, clean overrides, exceptions mapped, nothing leaking between requests.

## What the skill should do

1. Stay read-only; findings with severity, not patches.
2. Fix the line, then read the auth AutoConfiguration, Properties, and every auth-related bean the application declares.
3. Verify exactly one primary `SubjectProvider` is assembled — flag two active providers or an accidental override.
4. Check each default bean's `@ConditionalOnMissingBean` guard and the off switch's scope (skips assembly, not one bean).
5. Check exception mapping onto the web error contract and the per-request Subject/token cleanup paths.

## Expected output

| Check | Finding | Severity |
|---|---|---|
| Primary provider | Spring Security assembled; Sa-Token starter also on classpath but its provider not registered | Info — remove unused starter |
| Override guard | user `SubjectProvider` bean replaces default (guard verified) | OK |
| Off switch | `auth.enabled=false` leaves the exception mapper bean alive | High |
| Exception mapping | expired token returns 500 instead of 401 | High |
| Request cleanup | cleanup registered on success path only | Critical |

Evidence: SOURCE read on line <L>. Behavior tests NOT RUN — read-only review.

## Failure the skill must avoid

Reporting "auth is fine, Spring Security is configured" without checking for a second framework on the classpath or the cleanup paths. The critical finding here — cleanup only on success — never shows up in a passing smoke test.
