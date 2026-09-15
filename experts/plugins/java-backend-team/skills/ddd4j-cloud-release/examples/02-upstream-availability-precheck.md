# Example 2 — Read-only upstream availability precheck

## Prompt

> Our release window opens Friday. Check read-only whether all eight lines' upstream Boot and ddd4j artifacts are actually available — I don't want surprises mid-window.

## What the skill should do

1. Stay read-only — no builds, no deploys.
2. Fix all eight combinations via `ddd4j-cloud-version-selection` and record each branch's SHA.
3. For each line, check the private repository for the required Boot and ddd4j artifacts at the pinned versions.
4. Classify every missing artifact as BLOCKED(upstream) with the exact coordinate.
5. Produce the eight-row readiness table so the team knows which lines can enter the window.

## Expected output

| Line | Boot artifact | ddd4j artifact | Verdict |
|---|---|---|---|
| Hoxton.x | present | present | READY |
| 2020.0.x | present | present | READY |
| 2021.0.x | present | **missing `<coordinate>`** | BLOCKED(upstream) |
| 2022.0.x … 2025.1.x | present | present | READY |

Verdict: 7 of 8 lines ready; 2021.0.x blocked until upstream publishes `<coordinate>`. Evidence: REMOTE read-only check; no builds run.

## Failure the skill must avoid

Reporting "upstream is fine" from a check of one or two lines. The precheck's value is the eight-row table — one missing artifact discovered mid-window turns a scheduled release into an emergency.
