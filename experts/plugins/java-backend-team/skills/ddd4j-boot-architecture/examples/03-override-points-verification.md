# Example 3 — Override points verification

## Prompt

> Our team wants to swap the default cache implementation that ddd4j-boot-cache assembles with our own bean. Before we rely on that, prove where the override point is and that it actually takes effect.

## What the skill should do

1. Read the target module's AutoConfiguration on the current line and locate every default bean and its `@ConditionalOnMissingBean` guard.
2. Name the exact configuration class, bean method, and condition so the override point is verifiable rather than folklore.
3. Explain the override direction: a user-declared bean satisfies the condition and silently replaces the default.
4. Run the module's context test with and without a user bean to produce behavior evidence, not just source evidence.
5. Report source/test/CI evidence separately.

## Expected output

```
Override point:
  CacheAutoConfiguration.cacheManager(...) — guarded by
  @ConditionalOnMissingBean(CacheManager.class)

Behavior evidence:
  - context test, no user bean     → default CacheManager created
  - context test, user bean        → user bean wins, default skipped
  CI for the module: <status or NOT RUN>

Conclusion: declare your CacheManager bean in the application context;
the default backs off automatically. No properties change needed.
```

## Failure the skill must avoid

Answering "just define your own bean, Spring handles it" without reading the AutoConfiguration. If the default bean lacks the `MissingBean` condition, the user bean loses or duplicates — the override direction must be verified per line.
