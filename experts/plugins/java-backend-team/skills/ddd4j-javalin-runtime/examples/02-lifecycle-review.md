# Example 2 — Read-only lifecycle review

## Prompt

> Audit our runtime lifecycle before we on-call this service. Read-only. I care about start, drain, and close.

## What the skill should do

1. Stay read-only — no edits, findings only.
2. Trace the full `start → validate → initialize → ready → drain → close` path in `Ddd4jJavalinRuntime`, recording file paths and line numbers.
3. Check three specific failure modes: rollback on partial init (reverse order, initialized only), idempotent `close()` (repeated calls safe), and shutdown hooks accumulating across starts.
4. Verify Context/Subject cleanup is wired to terminal states, and check configuration validation rejects invalid production config.

## Expected output

| Concern | Finding | Evidence |
|---|---|---|
| Lifecycle path | coherent start→drain→close | `Ddd4jJavalinRuntime.java` lines NN–NN |
| Partial-init rollback | closes ALL participants, even uninitialized ones | `start()` catch block, line NN — defect |
| Idempotent close | guarded by `closed` flag | `close()` line NN — OK |
| Shutdown hooks | one hook per start, never removed | `start()` line NN — accumulates in embedded tests |

Plus: what was checked and found clean, and the explicit statement that no test was executed during this review.

## Failure the skill must avoid

Reporting "lifecycle looks fine" after reading only the `start()` method. The defects here live in the catch path and the shutdown-hook registration — the paths nobody reads.
