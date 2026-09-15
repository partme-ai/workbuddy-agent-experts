# Example 5 — Configuration silently absent after Boot 3 upgrade

## Prompt

> After moving to Boot 3 on the new ddd4j line, our custom starter's beans vanished. No errors at startup, the class is on the classpath, and the config file still lists it. What happened?

## What the skill should do

1. Name the likely cause first: Boot 3.x+ no longer reads `spring.factories` for auto-configuration — it reads `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`.
2. Verify which registration file the line actually uses, and which file the starter ships — the old entry sitting in `spring.factories` is silently ignored, hence no startup error.
3. Check the conditions as a second gate even after fixing registration (`@ConditionalOnClass`, `@ConditionalOnProperty`), since a silent condition failure looks identical.
4. Migrate the entry rather than copying code blindly across lines — Boot/JDK API differences mean the class itself may also need line-specific adaptation.
5. Prove the fix with a context test that asserts the beans exist, then re-check the disable path still works.

## Expected output

```
Diagnosis:
  starter ships:      META-INF/spring.factories (Boot 2.x mechanism)
  Boot line reads:    META-INF/spring/...AutoConfiguration.imports
  result:             entry ignored, no error, zero beans ← matches symptom

Fix:
  1. add the configuration entry to AutoConfiguration.imports
  2. re-verify conditions on this line (API differences vs Boot 2)
  3. context test: default on / user override / disabled = 0 beans

Evidence: SOURCE (registration files read) + context TEST planned.
```

## Failure the skill must avoid

Debugging the configuration class or the user's application code. The empty `AutoConfiguration.imports` produces no warning anywhere — reading `spring.factories` and seeing the entry there makes the wiring look correct, which is exactly the trap.
