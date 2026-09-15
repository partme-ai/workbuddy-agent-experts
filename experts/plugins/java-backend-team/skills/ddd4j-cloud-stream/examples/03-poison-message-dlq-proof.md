# Example 3 — Proving nack/retry/dead-letter on RabbitMQ

## Prompt

> Compliance asks: if a malformed message hits billing, prove it doesn't get dropped or retried forever. Show me with a real broker.

## What the skill should do

1. Run the test against real RabbitMQ — embedded or mocked binders do not share ACK defaults with the real broker.
2. Inject a poison message that always fails processing and observe the full path: nack → retry attempts with backoff → dead-letter destination.
3. Assert the ACK mode actually configured matches what was assumed (Kafka and RabbitMQ defaults differ; verify, don't copy).
4. Assert a good message published after the poison one still processes — the failure must not block the channel.
5. Grade the evidence per tier and mark untested brokers (Pulsar/RocketMQ if claimed) as NOT VERIFIED.

## Expected output

```
Poison-message evidence (real RabbitMQ):
  consume → nack observed            PASS
  retries: 3 attempts, backoff seen  PASS
  dead-letter destination received   PASS (message intact)
  subsequent good message processed  PASS
  ACK mode: manual (confirmed, not assumed)

Untested: Pulsar/RocketMQ paths claimed in the feature matrix —
NOT VERIFIED in this run.
```

## Failure the skill must avoid

Proving it on an in-memory test binder and reporting the default ACK behavior as broker fact. ACK defaults differ per binder, so the evidence only counts when produced by the real broker with the configured mode confirmed.
