# Example 5 — Diagnosing missing read-model rows

## Prompt

> Our read model is missing some orders — not randomly, but there are gaps, and the projection's checkpoint says everything is processed. Replaying by hand "fixes" it until the next incident. What's the actual bug?

## What the skill should do

1. Read the symptom: checkpoint ahead + missing rows = the cursor advanced before (or instead of) the read-model write committing.
2. Locate the order of operations in `ProjectionService`: position update and read-model write must share one explicit transaction, read-model write first.
3. Explain the failure sequence: crash (or exception) after `ProjectionPositionRepository` advances but before the view insert commits — the event is now behind the cursor forever.
4. Check the second-order issues while there: is position allocation atomic (not `MAX(position)+1`), and is the read-model write idempotent by event id for safe replays?
5. Prescribe the fix and the regression test: kill the process between the two writes and assert the event is reprocessed.

## Expected output

```
Defect: cursor-before-view commit ordering.

Sequence that dropped events:
  t1: ProjectionPositionRepository.advance(pos)  ← committed
  t2: crash / exception before view insert commits
  → event is below the checkpoint; never reprocessed. Gaps match restarts.

Fix:
  1. one transaction: read-model write + position advance, view first
  2. idempotent view writes keyed by event id (safe reprocessing)
  3. atomic position allocation (unique constraint + retry), not
     MAX(position)+1

Regression test: kill the projection after advance, before view commit;
assert the event is reprocessed on restart. Status: NOT RUN.
```

## Failure the skill must avoid

Recommending "replay nightly to patch gaps." The scheduled replay is a band-aid over a commit-ordering bug — the fix is the transaction boundary, and the kill-test proves it.
