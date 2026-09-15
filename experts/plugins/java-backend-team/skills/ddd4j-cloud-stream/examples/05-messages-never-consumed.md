# Example 5 — App healthy, consumer never receives messages

## Prompt

> Our producer says events are published successfully and the app logs look clean, but billing never receives anything. Both services are up. Where do we look?

## What the skill should do

1. Separate the three name layers first: verify the function name, the binding name, and the physical destination actually configured on both producer and consumer sides.
2. Check for the classic causes in order: destination mismatch (producer publishes to topic X, consumer listens on Y), binder on the classpath while the broker is unreachable, and consumer binding disabled or mis-indexed.
3. Inspect the broker itself — list what destinations exist and where the produced messages actually landed.
4. Check tenant/context header handling once connectivity is restored, so the fix doesn't stop at "messages flow".
5. Verify the fix with a real round-trip and mark evidence honestly.

## Expected output

```
Producer config: orderPublisher-out-0 → destination orders.events (kafka)
Consumer config: orderEvents-in-0    → destination <unset>
  → destination defaults to the binding name "orderEvents-in-0",
    which is NOT a real topic. No consumer group on orders.events
    from billing.

Broker check: orders.events has messages; no topic named orderEvents-in-0.

Root cause: function/binding/destination confusion — consumer destination
never configured, silently defaulting to the binding name.

Fix: set the consumer destination explicitly; restart; round-trip test
PASS pending run (broker + tenant header assertions).
```

## Failure the skill must avoid

Restarting both services and calling it fixed when messages "eventually show up", or adding a second producer "just in case". The defect is the unset destination silently aliasing to the binding name — a configuration fact, not a runtime flake.
