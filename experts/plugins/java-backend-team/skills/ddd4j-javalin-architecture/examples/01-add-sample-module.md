# Example 1 — Adding a sample module to the 7.2.x line

## Prompt

> We want to add an `order-service` sample under the ddd4j-javalin 7.2.x repo showing web + data + cache together. Where does it go and what does it need to declare?

## What the skill should do

1. Confirm the line is 7.2.x (Javalin 7.2/ddd4j 3/JDK 21/Maven 4, POM 4.1 `<subprojects>`) before writing any POM fragment.
2. Place the sample as a leaf module under the parent/BOM layering, depending on published capability modules — not on their internals.
3. Declare only the capability artifacts it exercises (web, data, cache) plus the testcontainers module at test scope.
4. Show how the sample composes providers through the runtime so the module list and dependency direction stay consistent with the other samples.

## Expected output

```xml
<!-- 7.2.x root: <subprojects> picks the module up automatically (POM 4.1) -->
<project>
  <parent>io.ddd4j:ddd4j-javalin-parent</parent>
  <artifactId>ddd4j-javalin-samples-order-service</artifactId>
  <dependencies>
    <dependency>io.ddd4j:ddd4j-javalin-web</dependency>
    <dependency>io.ddd4j:ddd4j-javalin-data</dependency>
    <dependency>io.ddd4j:ddd4j-javalin-cache</dependency>
    <dependency>io.ddd4j:ddd4j-javalin-testcontainers</dependency> <!-- test scope -->
  </dependencies>
</project>
```

Plus a statement that the sample builds on the 7.2.x toolchain only (JDK 21/Maven 4) and must not be back-ported to 6.7.x/7.1.x without per-line re-verification.

## Failure the skill must avoid

Writing a Maven 3 `<modules>` entry for a POM 4.1 line, or adding the testcontainers module at compile scope because "the sample uses it" — both are structural defects this skill exists to catch.
