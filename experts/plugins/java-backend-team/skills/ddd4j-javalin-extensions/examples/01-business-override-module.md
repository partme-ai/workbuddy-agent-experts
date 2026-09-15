# Example 1 — Adding a business extension with a binding override

## Prompt

> We built a custom pricing module and want it plugged into our 7.1.x service, replacing the default pricing binding without forking the core modules. How do we compose it?

## What the skill should do

1. Confirm the line (7.1.x → Javalin 7.1/ddd4j 2/JDK 17/Maven 3) and read the extensions module's composition contract and samples.
2. Install the default modules first, then apply the business pricing module through `Modules.override` so the business binding wins.
3. Register any extension resources (scheduled jobs, clients) as lifecycle participants with explicit owners and idempotent close.
4. Provide the failing contract first: a test asserting the extension's pricing behavior is served through the public entry point — proving the override actually took, not just that the injector built.

## Expected output

```java
var injector = Guice.createInjector(
    defaultModules,                      // defaults first
    Modules.override(new PricingModule())
           .with(new BusinessPricingModule())  // business binding wins
);
runtime.register(new PricingExtensionParticipant(...)); // owned resources, idempotent close
```

Evidence: composition test showing `BusinessPricingService` (not the default) answers a real pricing call, plus the disabled-classpath case (extension jar absent → default wiring serves, service starts).

## Failure the skill must avoid

Placing the business module before the defaults "so it takes priority" — Guice has no priority concept, only install order. The override installs before its target exists and is silently ignored; the service runs with default pricing and everything still starts.
