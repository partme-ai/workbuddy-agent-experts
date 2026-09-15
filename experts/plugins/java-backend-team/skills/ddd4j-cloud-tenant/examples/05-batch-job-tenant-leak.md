# Example 5 — Batch job leaks one tenant's data to another

## Prompt

> We added a nightly batch job last week. This morning tenant 42's dashboard showed tenant 7's invoices. The batch job runs fine. What did we do?

## What the skill should do

1. Connect the timeline: the defect appeared with the batch job, so inspect its tenant handling first.
2. Look for the two classic shapes: an ignore rule written so the batch job can run that also matches ordinary requests, and system context set by the job that is never cleared when the thread returns to the pool.
3. Read the exact ignore conditions and the job's context setup/teardown — not the comments, the conditions.
4. Explain the leak path: a pooled worker thread still carrying system context (or a broad ignore) serves a normal request with filtering disabled.
5. Fix by scoping: ignore/system context only inside the job's explicit scope, cleared on all exit paths, and add a regression test that runs a normal request after a simulated job on the same thread.

## Expected output

```
Findings:
  - Ignore rule "tenant is empty OR user is system" → matches the job AND
    any request that loses its tenant header downstream. TOO BROAD.
  - Batch worker sets system context, clears only on success — a failed
    item leaves system context set on the pooled thread.

Leak path: poisoned thread serves tenant 42's request with filtering
disabled → tenant 7's invoices visible.

Fix: narrow the rule to the job's explicit scope; clear system context in
a finally on every exit path.
Evidence: SOURCE read. Thread-reuse reproduction test NOT RUN — flagged.
```

## Failure the skill must avoid

Blaming the dashboard query or adding tenant 7 to an allowlist. The root cause is the batch job's tenant ignore rule and uncleared system context — exactly the "ignore condition too broad" leak this skill exists to catch.
