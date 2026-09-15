# Example 5 — Two services, same line, different effective versions

## Prompt

> Service A and Service B both import the 2021.0.x BOM set, but A gets Sentinel 1.8.x and B gets 1.7.x. Both builds are green. Where do we even look?

## What the skill should do

1. Diff the `dependencyManagement` blocks first: compare BOM import order between the two services.
2. Explain the mechanism: whichever BOM declares the version first in import order wins, so `spring-cloud-dependencies`, the Alibaba BOM, and the ddd4j BOM fight for Sentinel's version.
3. Build both effective POMs and pinpoint which import produced which resolved version.
4. Fix at the ownership level: one canonical import order for the line and no service-local pins.
5. Verify the corrected service resolves the same versions, and mark remote/CI tiers honestly.

## Expected output

```
Service A: imports [spring-cloud-dependencies, alibaba BOM, ddd4j BOM]
  → Sentinel resolved from alibaba BOM = 1.8.x
Service B: imports [alibaba BOM, spring-cloud-dependencies, ddd4j BOM]
  → Sentinel resolved from spring-cloud-dependencies = 1.7.x

Root cause: BOM import order changes the effective version.
Fix: canonicalize the order (cloud → alibaba → ddd4j), remove local pins.
Verification: effective POM diff after fix — PASS; CI NOT RUN.
```

## Failure the skill must avoid

"Fixing" Service B by pinning Sentinel 1.8.x directly in its POM. That silences the symptom, deepens the ownership violation, and guarantees the next library diverges the same way.
