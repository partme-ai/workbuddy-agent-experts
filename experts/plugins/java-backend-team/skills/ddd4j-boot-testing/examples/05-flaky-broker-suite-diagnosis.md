# Example 5 — Flaky broker suite diagnosis

## Prompt

> Our Testcontainers Kafka suite fails maybe one run in five, always on "await message consumed". Locally it's green every time. CI is red, then green on retry. What's actually wrong?

## What the skill should do

1. Recognize the signature: intermittent await-timeout on consumption is a synchronization defect in the test, not a product bug — the retry hides it, so it never gets fixed.
2. Read the fixture for the classic causes: no awaitility/polling on async consumption (fixed `Thread.sleep` instead), container startup racing the first publish, and assert-after-send without a consumer-group offset check.
3. Check the CI environment specifically: shared runners have slower container startup and port reuse — timing assumptions that hold locally break there.
4. Fix at the fixture level: poll with a deadline, wait for the container to be ready before publishing, and assert on consumer records rather than sleep-then-assert.
5. Re-run the suite repeatedly in CI to confirm stability, and only then re-enter the results in the evidence inventory.

## Expected output

```
Symptom: ~20% CI failure, always "await message consumed"; locally green.

Fixture read:
  - assert path: send → Thread.sleep(2000) → assert   ← fixed sleep
  - no wait-for-container-ready before first publish
  - CI runners: slower disk I/O, occasional port collision

Fix:
  1. container wait strategy / readiness check before publishing
  2. awaitility polling with explicit deadline on consumed records
  3. assert on consumer-group records, not on sleep elapsed

Result: 20 consecutive CI runs green (was ~20% failure).

Evidence: TEST RUN (fixture diff + stability runs). Product code: no
change needed — the flake was a test synchronization defect.
```

## Failure the skill must avoid

Adding retries around the test and moving on. The retry masks a fixture that asserts after an arbitrary sleep — it will flake again on the slowest CI day, during exactly the release run everyone is watching.
