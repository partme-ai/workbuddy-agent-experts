# Example 4 — Domain modeling request, not a boundary question

## Prompt

> Design the aggregate structure for our order domain — Order, OrderItem, Payment. We're on Quarkus. I assume this module-layout skill is the right one?

## What the skill should do

1. Recognize that aggregate modeling is a `ddd4j-core` concern, not a ddd4j-quarkus module-boundary concern — and should not be improvised here.
2. Hand off to `ddd4j-core` for `AggregateRoot`, `Command`, `Query`, and `Repository` contract design.
3. Clarify what this skill will do once the domain is designed: place the Quarkus adapter artifacts (which runtime/deployment modules host the repository and bus adapters).
4. If Quarkus is not actually the runtime or the project is plain Quarkus without ddd4j, route to the matching skill or generic guidance instead of forcing ddd4j modules onto the stack.
5. Keep the refusal scoped: no fabricated aggregate code, no invented module.

## Expected output

```
Boundary: aggregate modeling belongs to the ddd4j-core skill.
  Install: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core

This skill engages after the domain contracts exist, to answer:
  - which ddd4j-quarkus modules host the repository/bus adapters,
  - the runtime/deployment split for those adapters,
  - dependency direction and bom/dependencies registration.

Do not use this skill to author AggregateRoot hierarchies.
```

## Failure the skill must avoid

Inventing an `Order extends AggregateRoot<OrderId>` sketch with a made-up module placement. Wrong-layer design churns both the domain and the adapter; the handoff keeps each concern in its skill.
