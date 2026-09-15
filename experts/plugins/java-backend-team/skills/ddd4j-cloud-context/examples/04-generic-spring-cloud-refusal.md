# Example 4 — Same problem, but the project has no ddd4j

## Prompt

> We have the classic problem — request context lost in `@Async` and Feign calls. We don't use ddd4j though, just Spring Cloud + Boot. Which ddd4j-cloud context filter should we copy?

## What the skill should do

1. Say plainly: do not use this skill's ddd4j-cloud filters in a non-ddd4j project — they bind against ddd4j `ThreadContext`/Subject contracts the project does not have.
2. Refuse to retro-fit ddd4j types into the codebase; adding the dependency "just for the filter" drags the whole tuple in.
3. Route to generic `spring-cloud` guidance for the standard mechanisms (thread-local propagation decorators for executors, Feign `RequestInterceptor` for headers) — no `npx skills add` command applies.
4. If the team is actually evaluating ddd4j adoption, explain that the Cloud→Boot→ddd4j tuple is chosen first and this skill applies afterwards.

## Expected output

```
Finding: project has no ddd4j dependency; ddd4j-cloud context filters
are coupled to ddd4j context contracts.

Verdict: do not copy ddd4j-cloud filters here.

Path forward (no ddd4j):
  - Executor decorators: wrap task submission to capture/restore your own
    thread-locals (generic spring-cloud guidance).
  - Feign: RequestInterceptor copying the needed headers, cleared after.

If adopting ddd4j: choose the Cloud→Boot→ddd4j tuple first, then apply
this skill's propagation map on top.
```

## Failure the skill must avoid

Handing over the ddd4j-cloud filter class "since it's just a filter". It compiles against ddd4j contracts, and installing the dependency for one class silently re-pins the project's Boot/Cloud versions — the exact tuple mixing this package exists to prevent.
