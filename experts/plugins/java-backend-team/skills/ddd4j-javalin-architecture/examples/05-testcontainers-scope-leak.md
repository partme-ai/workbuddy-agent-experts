# Example 5 — Testcontainers leaked into a production artifact

## Prompt

> Our 6.7.x service jar grew by several megabytes and the deploy now needs Docker socket permissions it never needed. It started after we bumped modules. What happened?

## What the skill should do

1. Suspect a scope leak: the testcontainers module is test-scope support, and a compile-scope dependency drags Docker client machinery into production artifacts.
2. Trace the dependency graph on 6.7.x — find which module declared the testcontainers dependency and at what scope, and which production module pulled it transitively.
3. Confirm the fix: move the dependency to test scope in the offending module and re-check the produced artifact's dependency tree.
4. Add the guardrail: a contract test or enforcer rule that fails the build when test-scope machinery appears in production scope.

## Expected output

```
Root cause: module `mq` declares io.ddd4j:ddd4j-javalin-testcontainers
at compile scope (mq/pom.xml line NN) since commit abc123.
Effect: web/mq consumers inherit Docker test machinery in production jars,
which is why deployment began requesting Docker access.

Fix:
  1. Change scope to test in mq/pom.xml.
  2. Rebuild and verify with dependency:tree — testcontainers absent from
     the production module's compile classpath.
  3. Add an architecture contract test asserting test-scope modules are
     never on production compile classpaths.

Evidence: SOURCE read (POM + commit). Rebuild NOT RUN on this checkout.
```

## Failure the skill must avoid

Treating the symptom (jar size, Docker permissions) as an infrastructure request and granting the deploy more privileges. The real defect is a module-boundary scope violation that the architecture review should have caught.
