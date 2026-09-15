# Example 3 — Prove the SubjectProvider is request-scoped under load

## Prompt

> Someone changed our SubjectProvider from request-scoped to singleton "as an optimization". Give me the evidence that this is or isn't safe before I approve it.

## What the skill should do

1. Treat it as an evidence request: compare the two wirings against the ddd4j Subject contract rather than giving an opinion.
2. Show what `@Singleton` does to `SubjectProvider`: one instance serves all worker threads, so per-request subject state either disappears or must be re-derived per call.
3. Check the current line's Arc tests for request-context behavior on the SHA in question.
4. Name the test that would prove safety: a QuarkusTest with two concurrent requests carrying different subjects asserting isolation.
5. Report evidence status honestly — if the concurrent test has not run, say so.

## Expected output

```
Question: is SubjectProvider as @Singleton safe?

Contract: SubjectProvider resolves the current request's subject; ddd4j context is
request-scoped by design.

Evidence:
  - Wiring diff: @RequestScoped → @Singleton (PR #NN).
  - Arc test for request-context isolation: exists in runtime-quarkus, NOT RUN on PR SHA.
  - Concurrent isolation test (two subjects, two threads): ABSENT.

Verdict: UNPROVEN — singleton collapses per-request subject state unless every call
re-derives it from the request context; no test proves that.
Required: add the concurrent isolation test and run the Arc suite before approval.
```

## Failure the skill must avoid

Answering "singleton is faster, sure" without evidence. Under two concurrent requests a singleton provider that caches per-request state returns user A's subject to user B — the exact leak the contract forbids.
