# Example 5 — TestResource state leaks between test classes

## Prompt

> Our integration suite behaves bizarrely: Kafka assertions pass when a class runs alone but fail in the full run. Order matters somehow. What's wrong with our test setup?

## What the skill should do

1. Explain the lifecycle mismatch: `@QuarkusTestResource` resources start per test class by default — a resource written assuming one-time startup (like Spring's context) is restarted per class while external state persists.
2. Inspect the shared Kafka resource: topics, consumer groups, or offsets from an earlier class leaking into later classes' assertions.
3. Check cleanup: injected/started resources must reset or isolate state per lifecycle, or declare `Lifecycle.SHARED` deliberately with proper start/stop symmetry.
4. Explain the ordering sensitivity: alone-runs hide the leak because there is no earlier class to leave state behind.
5. Prescribe the fix and its regression test: per-class isolation or explicit shared lifecycle with cleanup, then run the full suite twice in different orders.

## Expected output

```
Finding: KafkaTestResource assumes single startup.
  - Default @QuarkusTestResource lifecycle = PER_CLASS → broker resource restarted
    per class, but topics/consumer groups from class N remain for class N+1.
  - OrderConsumerTest leaves a consumer group mid-offset → OrderReplayTest asserts
    "from beginning" → fails only in the full run.

Why single-class runs pass: no predecessor to leak state.

Fix options:
  1. Lifecycle.SHARED with explicit per-class topic isolation (per-class topic names),
  2. or per-class reset of topics/groups in the resource's start/stop symmetry.

Verify: run the full suite in two orders; both must be green.
```

## Failure the skill must avoid

Adding `@TestInstance`-style workarounds or reordering classes until the run is green. The defect is the lifecycle assumption — only explicit resource isolation or SHARED-with-cleanup fixes it for every order.
