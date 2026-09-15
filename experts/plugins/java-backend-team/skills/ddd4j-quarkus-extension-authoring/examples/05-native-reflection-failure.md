# Example 5 — Extension passes JVM tests, fails native build

## Prompt

> Our extension's tests all pass in JVM mode, but the native build just failed with a "class not found by reflection" style error. The tests were green this morning — what changed?

## What the skill should do

1. Read the failure as a native-image registration gap, not a regression: reflection-based access that works in JVM mode fails at native build unless explicitly registered.
2. Identify the reflectively accessed classes (from the native build error) and check the extension's reflection/serialization registration list.
3. Check whether the missing registrations should come from the deployment module's build steps (preferred, automatic for consumers) or a manual registration file (last resort).
4. Warn that a green JVM suite is expected here — a native test is not equal to a JVM test, so the fix must be validated with a native build, not a rerun of JVM tests.
5. Update the verification plan so native tests run where the contract requires them.

## Expected output

```
Diagnosis: native build reached code that reflects over TenantHeaders without a
registration entry.
  - Reflective access: TenantHeaders (constructor + fields) via header-binding helper.
  - Registration list (deployment module): TenantHeaders ABSENT.

Fix: register via the deployment module's build steps so every consumer gets the
registration at build time; avoid a manual registration file that consumers would
have to maintain.

Verification: JVM suite green (expected — proves nothing here); rerun the NATIVE
build/test. Evidence after fix: TEST(native) pending.
```

## Failure the skill must avoid

"Rerun the tests, must be flaky" — or adding `@RegisterReflectionForBinding`-style entries ad hoc in the consumer app. The registration belongs in the extension's deployment module so the fix holds for every consumer.
