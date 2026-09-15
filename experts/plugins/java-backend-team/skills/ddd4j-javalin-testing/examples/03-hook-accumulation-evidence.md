# Example 3 — Proving repeated starts don't accumulate hooks

## Prompt

> Our test suite starts and stops the app dozens of times, and CI containers eventually die with "too many open files" or shutdown hangs. Prove to me whether hook accumulation is real here.

## What the skill should do

1. Fix the line and locate the shutdown-hook registration site in the runtime start path — the suspect is one `Runtime.getRuntime().addShutdownHook(...)` per `start()`.
2. Design the accumulating-evidence test: run N start/stop cycles (embedded, in one JVM), capture the JVM's live shutdown-hook count after each cycle, and assert it does not grow.
3. Confirm the failure mode first: run the cycle test against current code and show the count growing — that is the RED that proves the diagnosis.
4. Fix (register once, or remove on stop), re-run the cycle test, and report evidence with the actual counts.

## Expected output

```
Contract: repeated start/stop must not accumulate shutdown hooks.

RED (current 7.1.x code, executed):
  cycles: 1  live hooks: 2
  cycles: 5  live hooks: 10
  cycles: 20 live hooks: 40   ← leak confirmed; matches CI fd-exhaustion

Fix: hook registered once per process, removed on close
(Ddd4jJavalinRuntime start/close).

GREEN (executed):
  cycles: 1/5/20/50 → live hooks: 2/2/2/2, all cycles drain+close clean.

Evidence tiers: behavior (executed, this SHA); container tier NOT RUN.
```

## Failure the skill must avoid

Answering "shutdown hooks are fine, the JVM cleans them up". Hooks are process-global and never cleaned until JVM exit — only the cycle-count evidence makes the accumulation visible, and only the removal fix stops the CI container deaths.
