# Example 2 — Runtime registration and lifecycle review (read-only)

## Prompt

> We run the same ddd4j core on Spring (monolith) and Vert.x (edge service). Review whether both runtimes actually register and clean up everything — I don't trust the edge one.

## What the skill should do

1. Stay read-only — review both runtimes against the same contract.
2. For each runtime, enumerate registered ports and verify one-registration-per-port with duplicate detection.
3. Verify request-context bind/restore on all terminal states in both stacks — including Vert.x context handoffs between verticles/event loop threads.
4. Verify readiness aggregation and reverse-order rollback on partial startup for each.
5. Check shutdown: drain, idempotent close, and no duplicate shutdown hooks in the Spring hot-reload path.

## Expected output

| Contract | Spring monolith | Vert.x edge |
|---|---|---|
| Port registration unique + duplicate-detect | OK | duplicate `SubjectProvider` binding found |
| Context restore on exception | OK | restore missing on async completion ← |
| Readiness aggregates participants | OK | hardcoded true |
| Partial-startup reverse rollback | OK | untested |
| Idempotent close, no hook leak | hook registered twice on reload | OK |

Verdict: the edge runtime fails three contracts; the suspicion is confirmed. Evidence: SOURCE on both stacks; no restart drills executed (`NOT RUN`).

## Failure the skill must avoid

Reviewing only the Spring monolith and generalizing "runtime is fine." Cross-runtime alignment is the contract — the Vert.x edge diverges exactly where Spring idioms (bean lifecycle) don't translate.
