# Example 5 — Bean missing in prod tests, works in dev

## Prompt

> Our custom ddd4j extension's bean is injected fine in dev mode, but the packaged test run fails with an unsatisfied dependency. Where do we even look?

## What the skill should do

1. Read the failure as a build-time discovery problem, not a runtime lookup miss: Arc validates injection points when the application is built for the packaged run.
2. Map the extension's module split — check whether the bean registration (BuildItem/Recorder or bean-defining annotation) lives in the deployment module and whether the deployment artifact is on the build classpath of the failing run.
3. Check whether dev mode reached the bean through a path the packaged build does not (e.g., an `@ApplicationScoped` annotation missing on the class, so no bean was ever discovered).
4. Recommend the structural fix: register via the deployment module's build steps, or annotate the class so Arc discovers it at build time.
5. Name the verification: rerun the packaged QuarkusTest and confirm the Arc validation passes.

## Expected output

```
Diagnosis: the class exists in the runtime module but is never discovered as a bean.
  - Class found in source: YES (SubjectStore, runtime module)
  - Bean-defining annotation: ABSENT
  - Deployment module BuildItem registration: ABSENT

Why dev mode "worked": dev-mode hot path resolved the instance through the direct
@Inject in the test fixture, not through Arc discovery; the packaged build runs
Arc validation and fails the missing producer.

Fix: either annotate SubjectStore as a bean-defining class (e.g., @ApplicationScoped)
or register it from the deployment module's build steps. Rerun the packaged QuarkusTest.
```

## Failure the skill must avoid

Answering "add a lookup at runtime" or "make the injector optional". CDI discovery in Quarkus is build-time — there is no runtime fallback for a bean that was never discovered, and the fix is registration, not lookup.
