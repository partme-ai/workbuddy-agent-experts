# Example 2 — Domain layer purity review

## Prompt

> Review my domain module. I think it's clean but I want a read-only check before we ship.

## What the skill should do

1. Stay read-only — this is a review request, not an implementation request.
2. Enumerate the framework imports in the domain layer and flag any of:
   - `org.springframework.*`
   - `com.baomidou.mybatisplus.*` / `org.apache.ibatis.*`
   - `io.javalin.*`
   - `io.quarkus.*`
   - `javax.servlet.*` / `jakarta.servlet.*`
3. Check that aggregates extend `AggregateRoot<ID>` and identifiers implement `Serializable`.
4. Check that repositories depend on the `Repository` SPI, not on a concrete mapper.
5. Check `ThreadContext` binding sites for a matching cleanup on success, exception, and async paths.

## Expected output

A findings table with one row per violation:

| File | Line | Violation | Why it breaks the contract |
|---|---|---|---|
| `OrderService.java` | 42 | imports `com.baomidou.mybatisplus.core.conditions.query.QueryWrapper` | Domain must not depend on the ORM; move the query into the data adapter |

Plus a list of what was checked and found clean, and an explicit statement of what was **not** verified (for example: no runtime test executed).

## Failure the skill must avoid

Reporting "domain layer is clean" after only reading file names. Purity claims require reading imports and confirming `CoreIndependenceTest` exists and passes for that line.
