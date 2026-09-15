# Example 4 — Asked to bend core contracts for the Cloud layer

## Prompt

> Our Cloud extension needs aggregate internals that ddd4j-core doesn't expose. Change the core aggregate contracts so the extension can reach them.

## What the skill should do

1. Refuse the reframing: core domain and SPI contracts are owned by `ddd4j-core`, not by the Cloud architecture — do not redesign them here.
2. Restate the boundary: Spring/Cloud modules assemble in the adapter layer; they consume core contracts, never redefine them.
3. Offer the legitimate paths: expose what is needed through the extension's own SPI against the published core contracts, or propose the core change through `ddd4j-core` where it is evaluated for all runtimes (Boot, Javalin, Quarkus too).
4. Classify the current need precisely; if the gap is a missing core capability, record it as such instead of hacking around it in the Cloud layer.

## Expected output

```
Verdict: do not change core aggregate contracts from the Cloud architecture.

Boundary: ddd4j-core owns domain/SPI contracts; ddd4j-cloud only assembles
adapters on top of them.

Options:
  1. Define the extension's own SPI in the Cloud layer, implemented against
     the published core contracts (preferred).
  2. Request the core capability via ddd4j-core so all runtimes get it
     consistently.

Missing: which aggregate internals the extension needs;
how to provide: the extension source and the failing access point.
```

## Failure the skill must avoid

Punching a hole through the aggregate for one Cloud extension. That leaks framework concerns into the domain layer and forks the core semantics for every other runtime that shares the contracts.
