---
name: blender-managed
description: "Start a non-invasive Blender design session without installing a Blender Add-on. Use for new projects or when the user wants to launch Blender."
---

# Managed Blender Session

Use `python3 scripts/launch_harness.py --session-id <unique-id> --output-root <approved-root>`.
For an authorized automatic task add `--execution-mode auto_with_budget` and repeated
`--export-format blend --export-format mp4` for its requested formats; add
`--allow-designed-proxies` only when the user permitted original substitute assets.
Use `--execution-mode review_only` for a read-only session. Omission remains interactive.
The launcher starts `scripts/managed_bootstrap.py` in foreground mode with
`--disable-autoexec`. Do not change Blender preferences. A project path must be an authorized
regular `.blend`; omit it for a new design.

Wait for the private `0600` session descriptor, then communicate through `harness_cli.py`.
Keep Blender alive until the user closes it or authorizes `session.close`. Never fall back to
unreviewed arbitrary Python when the Harness fails to start.

Verify `session.status` reports the requested mode. The temporary Codex Live Session panel and
viewport header expose progress and takeover controls. Use `view.set`, `view.focus`,
`playback.set_frame` and `playback.set` rather than an expert script for UI review.
If no foreground viewport exists, report that specific condition; do not claim the user can
see operations. Read [command reference](../blender-use/references/foreground-policy.md).
