# Example 5 — Context and Subject leak

## Prompt

> We bind the tenant and Subject into `ThreadContext` at the start of each request. Under load testing we sometimes see one user's data in another user's response. Where should we look?

## What the skill should do

1. Trace every `ThreadContext` bind site and find the matching release.
2. Check the three exit paths independently: success, exception, async completion.
3. Flag the classic failure: release only on the success path, so a thrown exception leaves the previous request's Subject bound on a pooled thread.
4. Check async handoffs — a `ThreadLocal`-backed context does not follow an async boundary automatically.
5. Recommend a scope or `try / finally` that covers all three exit paths.

## Expected output

```
Bind sites found:
  - RequestFilter.java line NN — binds Subject + Tenant
Release sites found:
  - RequestFilter.java line NN — releases on success only  ← defect

Leak scenario: request A throws → release skipped → thread returns to pool with
Subject A bound → request B served by the same thread inherits Subject A.

Fix: wrap the bind in a scope that releases in a finally block, and add an
async-completion release for any handoff to another thread.

Evidence: SOURCE read. Reproduce under load NOT RUN — flagged as remaining gap.
```

## Failure the skill must avoid

Answering "add `ThreadContext.clear()` at the end of the request" while ignoring the exception path and the async path. Both leak; the exception path is the one load testing typically surfaces.
