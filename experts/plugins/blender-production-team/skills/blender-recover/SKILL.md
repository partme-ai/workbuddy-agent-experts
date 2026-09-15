---
name: blender-recover
description: "Rollback a failed Blender milestone or resume from the latest confirmed checkpoint without replaying uncommitted commands."
---

# Blender Recovery

Inspect transaction and checkpoint state first. Roll back the active transaction and require
`restoration=confirmed` before continuing. After a crash, reopen the latest committed checkpoint
and replay committed idempotent requests only.

Never retry a timed-out mutation whose status is unknown. Query status first. If restoration
fails, stop mutations and preserve the recovery evidence.
