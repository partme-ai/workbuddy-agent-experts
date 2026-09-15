# Example 3 — Proving close is idempotent

## Prompt

> Platform team says our service "must survive repeated close calls" before they'll deploy it. What does that actually require, and how do we prove it?

## What the skill should do

1. Translate the requirement into observable contracts: calling `close()` twice (or after drain) must be safe — no exception, no double-free of resources, no second shutdown hook.
2. Locate `close()` on the target line and check for an idempotency guard (flag or state check), including whether drain calls close internally.
3. Write the failing test first: invoke start → drain → close → close and assert resource state and hook count.
4. Run the test on the real line toolchain and report evidence tiers honestly.

## Expected output

```
Contract: close() is idempotent across repeated invocation and post-drain calls.

Evidence:
  - Source: close() guards with AtomicBoolean `closed` (Ddd4jJavalinRuntime.java line NN)
  - Test: LifecycleIdempotencyTest — start/drain/close/close
    before fix: 2nd close threw IllegalStateException, hook count = 2  (RED)
    after fix:  2nd close no-op, hook count = 1                        (GREEN, executed)
  - Line/toolchain: 7.1.x, JDK 17, Maven 3

Remaining gap: embedded-test repetition (10 start/stop cycles) NOT RUN.
```

## Failure the skill must avoid

Answering "close is idempotent, we added a boolean flag" without executing the repeated-close test. The flag is the claim; the executed test on the real toolchain is the evidence — and the shutdown-hook count is where double-close usually hides.
