# Example 1 — Author a small extension

## Prompt

> We need a Quarkus extension that exposes our `SubjectProvider` implementation and a `tenant.required` config flag. Where do the pieces go?

## What the skill should do

1. Fix the line first (3.3.x or 4.0.x) and locate `extension-parent` conventions in that checkout.
2. Lay out the paired modules: `subject-extension-runtime` (beans, SPI impls, config mapping) and `subject-extension-deployment` (Processor, BuildItems, Recorder).
3. Implement the `Processor` that consumes/produces explicit BuildItems and calls into a `Recorder` to register the runtime behavior.
4. Register the `SubjectProvider` bean via BuildItems and map `tenant.required` through the configuration mapping — never relying on a BOM import to create the bean.
5. Define verification: Arc build-time discovery check, `@QuarkusTest` for the config flag, native registration audit.

## Expected output

```
subject-extension/
  runtime/     SubjectProvider impl (@ApplicationScoped), config mapping for tenant.required
  deployment/  SubjectExtensionProcessor (produces ...BuildItem, calls SubjectRecorder),
               SubjectRecorder.register() → runtime bootstrap

Registration: bean via BuildItem in the Processor — BOM import registers nothing.
Verification plan:
  - Arc discovery: build fails fast if the bean is missing (build-time validation).
  - @QuarkusTest: tenant.required=true flips behavior; config mapping asserted.
  - Native: reflection audit for the provider class before the native build.
```

## Failure the skill must avoid

Putting the Recorder/build steps in the runtime module "next to the bean they create". Build steps live only in the deployment module — the runtime artifact is not on the build classpath and the registration would never execute.
