# Example 4 — Request/response smuggled through a queue

## Prompt

> Our checkout needs the current fraud score before it can proceed. A teammate proposed publishing a "score request" message and waiting for the reply on another queue. Set that up with StreamBridge?

## What the skill should do

1. Identify the near-miss: a blocking request/response need is being forced through async messaging — do not build this on the stream skill's bindings.
2. Name what breaks: the checkout thread blocks on a correlation reply with no timeout semantics, no error contract, and retry behavior that can duplicate the fraud check or orphan replies.
3. Route to `ddd4j-cloud-feign`: a synchronous scored call with the error decoder factory, timeout, and (only if idempotent) retry is exactly the contract this need has.
4. Keep messaging for what it is good at: fire-and-forget or event fan-out where the consumer's ACK/retry owns delivery.
5. If the team insists on async for resilience, redesign explicitly (callback or saga) rather than simulating RPC over two bindings.

## Expected output

```
Verdict: do not simulate request/response over StreamBridge bindings.

Why: blocking on a reply queue has no timeout/error contract here, and
retries can duplicate the fraud check or strand replies without a
consumer.

Handoff: synchronous scored call via ddd4j-cloud-feign (error decoder +
timeout; retry only if the endpoint is idempotent).
Install: `npx skills add full-stack-skills/ddd4j-skills --skill
ddd4j-cloud-feign`.

Keep stream for: order events, audit fan-out — one-way flows where
consumer ACK owns delivery.
```

## Failure the skill must avoid

Wiring the request/reply binding pair with a "temporary" thread sleep for the reply. The checkout then couples its latency to consumer health, and the failure path — reply never arrives — has no defined behavior at all.
