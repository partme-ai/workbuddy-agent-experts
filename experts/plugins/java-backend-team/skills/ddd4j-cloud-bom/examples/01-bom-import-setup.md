# Example 1 — Setting up BOM imports for a new service

## Prompt

> We're wiring a new service on the 2023.0.x line with Alibaba Nacos. What should our BOM imports look like, and in what order?

## What the skill should do

1. Fix the combination with `ddd4j-cloud-version-selection` first — BOM contents follow the pairing, not the other way round.
2. Read the line's `cloud-parent` / `cloud-dependencies` / `cloud-bom` POMs and derive the consumer coordinates.
3. Write the import order explicitly: `spring-cloud-dependencies`, then the Spring Cloud Alibaba BOM, then the ddd4j BOM — and state why the order matters.
4. Confirm the Boot parent alignment against the combination matrix.
5. Give the verification step: build the effective POM and consume from the private repository with a clean cache.

## Expected output

```xml
<dependencyManagement>
  <dependencies>
    <!-- 1. Spring Cloud first -->
    <dependency> <!-- spring-cloud-dependencies <v> --> </dependency>
    <!-- 2. Spring Cloud Alibaba second -->
    <dependency> <!-- alibaba BOM <v> --> </dependency>
    <!-- 3. ddd4j BOM last -->
    <dependency> <!-- ddd4j-cloud BOM <v> --> </dependency>
  </dependencies>
</dependencyManagement>
```

Plus: Boot parent `<v>` per the matrix, consumer coordinates, and the note that reversing imports 1–3 can silently change effective versions.

## Failure the skill must avoid

Handing over a BOM snippet without an order rationale. Reversed import order resolves different effective versions and the misconfiguration only surfaces later as "two services on the same line behave differently".
