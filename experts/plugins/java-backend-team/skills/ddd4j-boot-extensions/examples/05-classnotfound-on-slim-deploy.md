# Example 5 — ClassNotFoundException on a slim deploy

## Prompt

> Our slim deployment image drops "unused" libraries to shrink it, and now the service won't start — `ClassNotFoundException` from somewhere in the extensions. It worked with the full image. Why does an optional module hard-crash the app?

## What the skill should do

1. Name the defect: the extension's classpath guard checks a class that is not the library's actual trigger class, so the guard passes while the library is absent — the optional extension becomes a hard startup dependency.
2. Read the guard in the extension's AutoConfiguration on the line and compare the guarded class with the classes the code path actually loads.
3. Identify the divergence: guard on a shim/interface that ships with ddd4j itself, while the bean methods reference the real third-party classes.
4. Fix the guard to test a class from the third-party library itself, and confirm the enabled switch also backs off the whole assembly.
5. Add the classpath-missing state to the test suite so slim deployments are covered before the next incident.

## Expected output

```
Failure: startup → NoClassDefFoundError in the Excel extension on the
slim image (library removed).

Root cause: @ConditionalOnClass guards <ddd4j-internal shim class>,
which is always present. The @Bean methods reference the removed
third-party classes → assembly runs and crashes.

Fix:
  1. guard on a class from the third-party library itself
  2. verify the off switch backs off the whole assembly
  3. add classpath-missing to the three-state test suite

Post-fix slim-image test: context green, extension skipped. PASS.

Evidence: SOURCE (guard read) + behavior TEST RUN (slim image).
```

## Failure the skill must avoid

Adding the library back to the slim image as the "fix". The extension is still not truly optional — the next slimming pass (or a library exclusion for a CVE) reproduces the crash, only later and in production.
