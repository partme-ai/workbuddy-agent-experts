# Example 3 — User override path verification

## Prompt

> We tell our users "just declare your own bean and it takes precedence." Prove that's actually true for the cache client on the line we ship, before we document it.

## What the skill should do

1. Read the AutoConfiguration on the shipping line and locate the client bean's `@ConditionalOnMissingBean` condition.
2. Run the module's context test twice: once with only the default, once with a user-declared bean.
3. Assert the direction: with a user bean, the default must not be created (no duplicate, no "user bean loses" outcome).
4. Also exercise the property-override path if the configuration exposes one.
5. Report configuration presence, bean creation, and behavior as separate evidence layers; grade CI as needed.

## Expected output

```
Override verification (line 3.x, CacheClientAutoConfiguration):
  context test A — no user bean:
    CacheClient = default impl            PASS
  context test B — user CacheClient bean:
    CacheClient = user impl               PASS
    default bean method never invoked     PASS (backed off via
    @ConditionalOnMissingBean)
  property path — ddd4j.cache.mode=near:
    CacheClient = near variant            PASS

Conclusion: the documented claim holds on this line.
Evidence: TEST RUN (context). CI: NOT RUN. Publish: n/a.
```

## Failure the skill must avoid

Blessing the override claim from reading the annotation alone. If the guard is missing or on the wrong bean, users' "overriding" bean either loses or coexists with the default — only a context test with both beans proves which happens.
