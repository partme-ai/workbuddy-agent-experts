# Example 1 — Auto-configuration test suite

## Prompt

> We just added a new starter on the 3.x line. Build the test suite that actually proves the auto-configuration works: defaults, user overrides, and the off switch.

## What the skill should do

1. Fix the maintenance line, then read the AutoConfiguration to enumerate every condition and default bean the suite must cover.
2. Build `ApplicationContextRunner` tests for the wiring matrix: default on, property off, class missing, and each `@ConditionalOnMissingBean` overridden by a user bean.
3. Assert bean presence AND absence per case — the off switch must show zero beans, not fewer beans.
4. Follow with a slice or full-context test that exercises one real behavior, since runner assertions prove wiring only.
5. Record which cases ran and which remain unrun.

## Expected output

```java
new ApplicationContextRunner()
    .withConfiguration(AutoConfigurations.of(FeatureAutoConfiguration.class))
    .run(ctx -> assertThat(ctx).hasSingleBean(FeatureClient.class));
// + .withPropertyValues("ddd4j.feature.enabled=false")
//     → assertThat(ctx).doesNotHaveBean(FeatureClient.class)
// + .withBean("userClient", FeatureClient.class)
//     → default backed off, user bean wins
```

Plus the real-behavior test (one round-trip through the assembled client) and an inventory: 4 runner cases run, 1 behavior test run, CI NOT RUN.

## Failure the skill must avoid

A suite that only asserts the happy default. Without the off-switch and override cases, the starter ships with untested promises — the exact gap `ApplicationContextRunner` suites exist to close.
