# Example 1 — New auto-configuration with a real off switch

## Prompt

> Add an auto-configuration for our feature on the 3.x line. It needs a config prefix, sensible defaults, and a way for users to switch it off completely.

## What the skill should do

1. Fix the maintenance line, then register the configuration using that line's mechanism (`AutoConfiguration.imports` for Boot 3.x+).
2. Define the configuration prefix and a `@ConfigurationProperties` class bound to it.
3. Guard each default bean with `@ConditionalOnMissingBean` so user declarations win.
4. Make the off switch (`@ConditionalOnProperty` with `matchIfMissing = true`) gate the whole assembly — when disabled, no beans from the feature are created at all.
5. Give every created resource an explicit owner, a failure rollback, and an idempotent close; declare the `destroyMethod`.

## Expected output

```java
@AutoConfiguration
@ConditionalOnClass(FeatureClient.class)
@ConditionalOnProperty(prefix = "ddd4j.feature", name = "enabled",
                       havingValue = "true", matchIfMissing = true)
@EnableConfigurationProperties(FeatureProperties.class)
public class FeatureAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public FeatureClient featureClient(FeatureProperties props) { ... }
}
```

Plus: the imports-file entry, a context test matrix (default on, user bean overrides, `ddd4j.feature.enabled=false` produces zero feature beans), and the destroy path named.

## Failure the skill must avoid

Implementing the off switch as a condition on a single `@Bean` method while the configuration class still creates helper beans. The feature is then "disabled" but its collaborators still assemble — half-wired and untestable.
