# Example 1 — Dual-line release validation and publish

## Prompt

> Both lines are due: 3.3.x and 4.0.x. We're authorized to publish today. Run the full validation and publish, and show me the report.

## What the skill should do

1. Record each checkout's Git SHA and confirm clean worktrees for both lines.
2. Build each line with its contract toolchain: 3.3.x on Maven 3 / JDK 17, 4.0.x on Maven 4 / JDK 21, and verify the 61-module inventory per deploy.
3. Gate on CI terminal success for the exact final SHAs, and record Security results — SKIPPED stays a risk.
4. Publish to the private repository per line under the explicit authorization, requiring zero exit plus the full inventory.
5. Prove remote availability per line with isolated clean-cache consumption (`-U`), then produce the graded report with redacted errors.

## Expected output

```
Line 3.3.x (SHA 1a2b3c4): build OK (Maven 3 / JDK 17) | 61/61 modules
  CI: terminal SUCCESS on 1a2b3c4 | Security: 1 SKIPPED scan (carried as risk)
  Publish: OK → private repo | Consume: -U clean-cache OK → CONSUMED

Line 4.0.x (SHA 5d6e7f8): build OK (Maven 4 / JDK 21) | 61/61 modules
  CI: terminal SUCCESS on 5d6e7f8 | Security: PASS
  Publish: OK → private repo | Consume: -U clean-cache OK → CONSUMED

Evidence grading: BUILD/CI/PUBLISH/CONSUME = full per line; SECURITY = partial (3.3.x).
Risks: 3.3.x Security skip recorded, owner assigned.
```

## Failure the skill must avoid

Reporting both lines "released" after the builds pass — skipping CI-on-final-SHA and clean-cache consumption would leave the strongest evidence (CONSUMED) unproven while a warm cache pretends otherwise.
