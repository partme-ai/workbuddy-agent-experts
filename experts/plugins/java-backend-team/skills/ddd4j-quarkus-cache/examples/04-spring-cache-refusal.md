# Example 4 — Spring Cache annotations in Quarkus

## Prompt

> We're most productive with Spring's `@Cacheable`/`@CacheEvict`. Can we add spring-cache to our ddd4j-quarkus service and configure Redis as the backing store?

## What the skill should do

1. Draw the stack boundary: `@Cacheable` is Spring's runtime AOP caching abstraction; the ddd4j-quarkus line integrates caches through the `Cache` SPI with build-time CDI wiring.
2. Refuse to blend the stacks — Spring Cache interceptors and the ddd4j Cache SPI would be two caching layers over one Redis, with uncoordinated TTL and eviction.
3. Route Spring Boot projects to `ddd4j-boot-cache` where the Spring abstraction is the correct model.
4. Offer the ddd4j path: express the caching intent (what to cache, TTL, invalidation) through the `Cache` SPI, which is portable across the Boot/Quarkus/Javalin lines.
5. Keep it constructive: the team's `@Cacheable` habits translate to SPI cache names plus explicit invalidate calls — do not use this skill to wire Spring annotations.

## Expected output

```
Boundary: spring-cache annotations are Spring AOP machinery (ddd4j-boot-cache territory).
The ddd4j-quarkus line caches through the Cache SPI + CDI; mixing both means two
caching layers over one Redis with uncoordinated TTL/eviction.

Translation path: @Cacheable("prices", key=sku) → Cache SPI cache "prices" with
get-or-load on sku; @CacheEvict → explicit invalidate on the same cache name.

If this were a Spring Boot service: use ddd4j-boot-cache instead.
Install: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-cache
```

## Failure the skill must avoid

Adding spring-cache alongside the Cache SPI "temporarily". Both layers write the same Redis keys with different TTLs, and eviction from one layer leaves the other serving stale values.
