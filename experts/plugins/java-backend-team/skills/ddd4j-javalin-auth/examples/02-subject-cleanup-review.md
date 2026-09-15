# Example 2 — Read-only auth cleanup review

## Prompt

> Security asked us to prove subjects can't leak between requests. Do a read-only review of our auth wiring on 6.7.x and tell them something concrete.

## What the skill should do

1. Stay read-only; produce findings with file/line evidence.
2. Find every Subject bind site and check for a matching release on the three exit paths: success, exception, async completion.
3. Flag any path where an exception skips the release — that is the leak load testing usually finds, because pooled threads inherit the previous request's Subject.
4. Check that tokens and cookies cannot reach logs: inspect log statements in filters, error handlers, and exception mappers for raw header or cookie values.

## Expected output

| Bind site | Release on success | Release on exception | Release on async |
|---|---|---|---|
| `AuthFilter.java:31` | yes (`:58`) | **no** — defect | n/a |
| `OidcCallback.java:77` | yes (`:90`) | yes (`:90`, finally) | **no** — defect |

Leak scenario: request A throws at line 44 → release at line 58 skipped → thread returns to pool with Subject A bound → request B on the same thread reads A's tenant.

Plus: log hygiene check (two `log.debug` statements print the raw `Authorization` header — redact), and what was not verified (no load test executed).

## Failure the skill must avoid

Answering "add a `Subject.clear()` at the end of the filter" and calling it done. Without covering the exception and async paths — and the log statements — the leak persists and the review conclusion is false.
