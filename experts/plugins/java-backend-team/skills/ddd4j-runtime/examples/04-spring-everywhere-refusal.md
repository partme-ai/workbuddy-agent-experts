# Example 4 — Boundary: Spring assumptions applied to every runtime

## Prompt

> We standardized on Spring internally. Just use `@Component`, `@Autowired`, and `@Profile` for the Vert.x and Helidon runtimes too — it's all JVM, and our platform team only knows Spring. Same for the Guice module: slap the annotations on it.

## What the skill should do

1. Refuse the uniform-Spring approach: ddd4j core deliberately has no DI-framework dependency, and each runtime has its own registration idiom — Guice is explicit `Module`/`Injector` assembly, Vert.x is Context/Verticle lifecycle, Helidon is service registration with its own request scope.
2. Explain the concrete failure: Spring annotations do nothing in a non-Spring container — they compile and then silently register nothing, leaving `Contexts`/`Registry` empty at first use.
3. Route it correctly: platform-team familiarity is a staffing concern; the fix is a thin adapter per runtime built on that runtime's idiom, with behavior aligned by runtime-testkit.
4. Offer the legitimate reuse: share the provider classes (the implementations of the ports) across runtimes — only the registration layer differs.

## Expected output

```
Refusal: @Component/@Autowired/@Profile register nothing outside Spring.
Guice ignores them; Vert.x/Helidon never scan them. The result is a boot
that looks green with an empty Registry — first CommandBus.execute fails.

Correct structure:
  - providers (SubjectProvider impls, repositories, executors): shared,
    framework-free
  - registration: per runtime — Spring bean lifecycle, Guice Module,
    Vert.x verticle deployment, Helidon service registration
  - alignment: runtime-testkit asserts identical registration, scope, and
    close behavior on each runtime

Evidence: SOURCE (runtime matrix read). No wiring attempted under Spring-
everywhere.
```

## Failure the skill must avoid

Producing the annotated classes "for consistency." They become landmines: everything compiles, nothing registers, and the failure appears at first request in an environment nobody associated with the annotation decision.
