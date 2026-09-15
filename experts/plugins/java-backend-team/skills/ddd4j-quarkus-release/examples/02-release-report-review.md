# Example 2 — Read-only release report review

## Prompt

> A teammate drafted our release report for the 4.0.x publish. Review it read-only — is the evidence complete and the wording safe to send to the security team?

## What the skill should do

1. Stay read-only; audit the report's evidence grading against what actually happened (builds, CI, Security, publish, consumption).
2. Check that Security skips appear as SKIPPED risks, not folded into PASS.
3. Check the SHA discipline: every result tied to the final SHA, not "the branch".
4. Check consumption evidence: clean-cache (`-U`), not a warm-cache claim.
5. Scan for credential leakage in quoted errors (Maven settings, repo URLs with embedded credentials, tokens).

## Expected output

| Check | Draft report says | Verdict |
|---|---|---|
| CI gate | "CI is green on the branch" | **DEFECT** — must be terminal SUCCESS on the final SHA |
| Security | "security OK (1 scan deferred)" | **DEFECT** — SKIPPED must be a named risk, not "OK" |
| Consumption | "artifact available locally" | **DEFECT** — warm cache is not CONSUMED; needs `-U` |
| Redaction | error quote includes `https://user:token@nexus...` | **LEAK** — redact before sending |
| Module inventory | "61/61 modules deployed" | OK |

Revised status: not ready to send — three evidence defects and one redaction leak.

## Failure the skill must avoid

Rubber-stamping the draft because "the build passed". Three of the report's claims overstate evidence and one leaks a credential — the review exists exactly to catch both classes of defect.
