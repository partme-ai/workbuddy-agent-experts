# Example 2 — Auth integration review (read-only)

## Prompt

> Review how auth is wired in our service. We use Sa-Token, and I want to know if anything in the domain touches it directly.

## What the skill should do

1. Stay read-only — findings only.
2. Search the domain and application layers for direct framework access: `StpUtil`, `StpKit`, `SecurityContextHolder`, Shiro `SecurityUtils`.
3. Verify exactly one primary `SubjectProvider` is registered and that it maps into `AuthPrincipal`.
4. Check request-end cleanup: bind site has a matching restore on success, exception, and async paths.
5. Check that extended fields go through `AuthConstants` / type-safe getters, not raw string keys.

## Expected output

| Finding | Location | Severity |
|---|---|---|
| `StpUtil.getLoginId()` called in `OrderDomainService` | `OrderDomainService.java:88` | violation — read `Subject` instead |
| Two `SubjectProvider` beans registered (Sa-Token + custom JWT) | runtime config | violation — exactly one primary |
| Sa-Token extra key read via literal `"acctType"` | `AuthMapper.java:23` | violation — use `AuthConstants` |
| Bind/restore pair present, covers exception path | request filter | OK |

Summary states what was not verified: no live request was replayed, so cleanup under async completion is `NOT RUN`.

## Failure the skill must avoid

Reporting the integration "healthy" because login works. The review exists to surface the domain-layer framework reads and provider contention that a login smoke test never exercises.
