# Example 2 — Read-only context filter review

## Prompt

> Audit our context handling before we freeze for the release. Read-only — I want to know where restoration or cleanup is missing, not a refactor.

## What the skill should do

1. Stay read-only — findings table, no edits.
2. Enumerate every `ThreadContext` bind site and its matching release site in the service and the line's filters.
3. For each hop (sync, async, Reactor, Feign), check restoration on the terminal state and cleanup on success, exception, and pool-reuse paths.
4. Check filter registration and ordering — a filter that exists but is not chained is a finding, not a pass.
5. State what was not verified (no runtime test executed) and list the tests that would close the gap.

## Expected output

| Hop | Bind site | Restore on terminal | Cleanup paths | Verdict |
|---|---|---|---|---|
| HTTP entry | `WebFilter` NN | n/a | success/exception | OK |
| `@Async` | executor wrapper NN | async complete | missing exception | DEFECT |
| Feign | interceptor NN | response terminal | success only | DEFECT |

Plus: registration/order check result, explicitly untested paths, and evidence status (SOURCE only).

## Failure the skill must avoid

Reporting "context handling is fine" because each hop has *a* filter class present. The defects live in which terminal states restore and which paths clean up — presence without registration and path coverage is exactly the false pass this review prevents.
