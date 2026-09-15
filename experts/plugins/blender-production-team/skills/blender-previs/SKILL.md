---
name: blender-previs
description: "Use when turning a story or shot list into a color-coded white-model previs video in Blender, producing placeholder blocking, exact cut timing, and a machine-readable geometry-to-role map for downstream Seedance video generation."
---

# Blender white-model previs

Previs answers three questions cheaply and deterministically: where the camera is,
when the cut happens, and where every subject stands and moves. Iterate those here,
in Blender, for free — never burn paid video-generation attempts on framing or timing
guesses. This Skill produces a previs package, not a final-quality film: placeholders
have no costume, texture, or limb articulation by design.

## When to use

- The user provides a story, script, or shot list and wants a blocking/timing preview.
- A downstream video request (Seedance/Dreamina) needs a camera-and-timing reference
  video instead of text-only prompting.
- An existing previs shot is rejected and must be re-blocked without touching the others.

Do not use this Skill for lookdev, final renders, or character performance. Route those
to `blender-render-compositing` and `blender-character-animation`.

## Workflow

1. **Read status first.** Call `blender_connection_status`. With no guarded Harness
   session connected, route to `blender-mcp-setup`; never assume Blender exists
   because this Skill was loaded.
2. **Fix the shot table.** Accept a structured shot table conforming to
   [previs-shot-table.schema.json](references/previs-shot-table.schema.json), or derive
   one from prose and get the derivation confirmed before building anything. Every shot
   needs a stable id, integer frame range at the project fps, shot size, camera intent,
   and per-subject position or motion beats. Frame arithmetic is the contract: the shot
   durations must sum to the project total exactly.
3. **Cast the placeholder scene.** One primitive per role, cast from the default
   convention table below unless the user overrides it. Colors must stay visually
   distinguishable from each other and from the environment; one role never shares a
   color with another. Name every placeholder `previs_role_<roleId>` and record the
   full mapping as [previs-map.schema.json](references/previs-map.schema.json) content.
   Add a ground plane and one neutral scale reference.
4. **Block, do not perform.** Keyframe only object location and orientation. Limb
   articulation, facial performance, and physics are intentionally absent; say so in
   the deliverable instead of approximating them.
5. **Camera per shot.** Follow `blender-cinematography` for placement, lens
   intent, and moves. Cuts are hard frame-range boundaries from the shot table; add a
   transition only when the table explicitly requests one.
6. **Render cheap, per shot.** Render each shot as its own frame-range job
   (`job.submit` with `RENDER_ANIMATION_FRAMES`, Workbench or low-sample EEVEE) so a
   rejected shot re-renders alone. Via `blender-background-jobs`.
7. **Stitch with exact cut frames.** Assemble the per-shot clips in the sequencer
   (`COMPOSE_VIDEO`, via `blender-sequence-editing`) and verify the composited
   duration equals the shot-table total in integer frames.
8. **Deliver the previs package:** the previs video, the shot table, the geometry-to-role
   map, and the downstream handoff prompt drafted from
   [seedance-handoff-prompt.md](references/seedance-handoff-prompt.md) — that prompt is
   what `dreamina-3d-from-blender` or `dreamina-video-production` consumes to turn
   this previs into a real shot.
9. **Iterate in place.** A rejected shot keeps its id; re-block and re-render only that
   shot, restitch, and reissue the package. Never renumber shots: downstream references
   and approvals hang off the ids.

## Default color convention

Override as a set, per project, in the geometry-to-role map; never ad hoc per shot.

| Role class | Primitive | Color |
|---|---|---|
| Protagonist | Cube | Light cyan `#7FD4C1` |
| Antagonists / pursuers | Cubes, one each | Dark gray `#4A4A4A` |
| Hero prop (rocket, weapon, macguffin) | Cylinder | Red `#D9483B` |
| Ground vehicle | Box | White `#F2F2F2` |
| Rail or large vehicle | Long box | Teal `#2E8B8B` |
| Environment landmark | Keep real blocking mass, untextured | Neutral gray |

## Never do

- Never claim the previs represents limb motion, performance, or final visuals.
- Never let two roles share one color, or change a role's color mid-project.
- Never move a cut or retime a shot without updating the shot table first.
- Never submit a paid video-generation request from this Skill; producing the handoff
  prompt is where it ends.
- Never treat a rendered previs as approval to skip the user's shot-table review.
