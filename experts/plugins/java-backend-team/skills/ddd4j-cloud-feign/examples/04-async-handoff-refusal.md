# Example 4 — Feign is the wrong tool for event delivery

## Prompt

> Our order service finishes and needs to tell five downstream services. Someone suggested five Feign calls from a loop with retries. That's fine, right?

## What the skill should do

1. Say when this near-miss is wrong: fan-out notification to five consumers is messaging, not synchronous RPC — do not use this skill's retry/cleanup machinery to fake delivery guarantees.
2. Name the concrete failure mode: five sequential calls with per-call retries means one slow consumer delays the request thread, and partial failure leaves unclearable half-delivered state.
3. Route to `ddd4j-cloud-stream`: publish one event with binding/destination naming and let each consumer own its ACK and retry.
4. Keep the boundary honest: Feign remains right for true request/response needs (e.g. a synchronous price lookup), where this skill applies.
5. If latency-coupled fan-out is genuinely required, say so explicitly and design for partial failure rather than pretending Feign gives delivery semantics.

## Expected output

```
Verdict: do not implement consumer notification as five Feign calls.

Why: per-call retries give no delivery guarantee across five consumers,
tie the request thread to the slowest consumer, and leave partial-failure
state that no cleanup path can repair.

Handoff: publish one change event via ddd4j-cloud-stream — consumers
own ACK/retry. Install: `npx skills add full-stack-skills/ddd4j-skills
--skill ddd4j-cloud-stream`.

Keep Feign for: synchronous request/response (price lookup, reservation
check) — that is this skill's contract.
```

## Failure the skill must avoid

Configuring more aggressive retries to make the loop "reliable". Retries strengthen exactly the wrong half: they help one call while the design still has no delivery semantics for the other four consumers.
