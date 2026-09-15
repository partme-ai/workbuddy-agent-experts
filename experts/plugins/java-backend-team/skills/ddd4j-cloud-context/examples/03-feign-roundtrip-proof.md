# Example 3 — Proving headers survive a real Feign round-trip

## Prompt

> Our context tests are all green with mocks, but QA says the downstream service sometimes sees no tenant header. Prove the propagation works with a real call.

## What the skill should do

1. Set up a real Feign round-trip between two services on the confirmed line — mocks and stubs don't count as evidence here.
2. Assert on the receiving side that context and tenant headers arrive on every terminal state: success, error response, timeout, and retry.
3. Check the capturing side: headers must be read before the call switches threads and cleared after, per attempt.
4. Run the exception path deliberately — kill the downstream mid-call and confirm the caller's thread is cleaned up for reuse.
5. Grade the evidence and mark what remains NOT VERIFIED (for example other brokers of context such as Reactor paths not exercised).

## Expected output

```
Round-trip matrix (real services, no mocks):
  success        → headers received: PASS
  error response → headers received: PASS, caller cleanup: PASS
  timeout        → headers received: n/a, caller cleanup: DEFECT (residue)
  retry attempt2 → headers received: PASS

Verdict: propagation works on the happy path; cleanup after timeout leaks
state to the next request on the pooled thread.
Evidence: TEST (real round-trip). Reactor path NOT RUN.
```

## Failure the skill must avoid

Accepting the green mock-based suite as proof. Mocked Feign never switches threads and never exercises timeout/retry terminal states — exactly the paths where capture/clear breaks.
