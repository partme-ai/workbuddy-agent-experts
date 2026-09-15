# Example 4 — Boundary: Spring annotation mistaken for ddd4j

## Prompt

> Add a `@Transactional` and a `@Component` on my aggregate base class so ddd4j picks them up automatically — same thing as your DDD annotations, right?

## What the skill should do

1. Decline to conflate the two: Spring's `@Transactional` / `@Component` are framework contracts owned by the Spring adapter layer, not ddd4j metadata.
2. Explain that ddd4j annotations describe domain/CQRS/API/ORM facts and are consumed by ddd4j adapters — they do not register Beans.
3. Redirect: runtime concerns (Bean registration, transactions) belong to the adapter layer per `ddd4j-runtime` / `ddd4j-data`, not to annotations on the domain base class.
4. If the project actually needs Spring behavior, show where Spring annotations are acceptable — the adapter layer, never the domain.
5. State what was not verified rather than inventing a registration mechanism.

## Expected output

```
Refusal rationale: @Component / @Transactional are Spring contracts. ddd4j
annotations (Contract, BusinessType, CreateEvent, @TenantId, ...) are metadata
consumed by ddd4j adapters; none of them registers a Bean or opens a
transaction. Annotating the domain base class with Spring types violates the
core boundary (domain must compile without framework imports).

Correct placement: Bean registration and transaction demarcation go in the
runtime/data adapter. Ask ddd4j-runtime for wiring and ddd4j-data for
transaction boundaries.

Evidence: SOURCE read of the annotation families. No Spring wiring attempted.
```

## Failure the skill must avoid

Blending the annotation families — answering "sure, `@Component` works like `DDDAnnotation`." That erases the domain/adapter boundary the skill exists to protect.
