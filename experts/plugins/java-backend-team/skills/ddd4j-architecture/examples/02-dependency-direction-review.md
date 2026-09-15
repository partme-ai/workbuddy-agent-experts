# Example 2 — Domain dependency-direction review (read-only)

## Prompt

> Before we tag a release, do a read-only architecture check on our domain module. Is it still clean?

## What the skill should do

1. Stay read-only — review, no edits.
2. Enumerate imports in the domain layer and flag `org.springframework.*`, `com.baomidou.mybatisplus.*` / `org.apache.ibatis.*`, `io.javalin.*`, `io.quarkus.*`, and servlet packages.
3. Confirm arrows still point adapter→core: no capability module compiled against a concrete runtime class.
4. Trace one port end to end (e.g. `Repository`) to its registered adapter to confirm registration actually happens.
5. Separate findings into facts, inferences, and unverified areas.

## Expected output

| File | Line | Violation | Rule broken |
|---|---|---|---|
| `OrderService.java` | 42 | `import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper` | domain must not depend on the ORM |
| `InventoryDomain.java` | 17 | `import io.quarkus.arc.InstanceHandle` | domain must not depend on a DI container |

Clean: no servlet imports; `Repository` port resolves to a registered data adapter; no core module imports a broker client.
Not verified: `ddd-rules` architecture tests not executed in this review — marked `NOT RUN`.

## Failure the skill must avoid

Reporting "architecture is clean" from module names or a green build. Compile success hides dependency-direction violations; only the import audit and architecture tests expose them.
