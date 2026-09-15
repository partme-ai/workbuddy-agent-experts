# Skill routing reference

Read this only when a request spans multiple Blender domains or when a command advertises conditional Skills.

## Naming rule

Every Skill uses `blender-<clear-action-or-domain>`, lowercase ASCII and hyphens. The folder and frontmatter name must match. Lifecycle names (`use`, `managed`, `connector`, `inspect`, `preview`, `export`, `recover`) follow the same convention used by the Maya and Dreamina 3D sibling plugins.

## Routing matrix

| Intent or command | Primary Skill | Add when needed |
|---|---|---|
| Session launch/open scene | managed or connector | inspect before mutation |
| Scene hierarchy/assets | scene-assembly | inspect |
| Mesh/product/prop | hard-surface | curves, UV-material |
| Armature/weights/constraints | character-rigging | character-animation |
| Action/F-Curve/NLA/prop timing | character-animation | quality-validation, cinematography |
| Camera path/framing/handheld | cinematography | quality-validation |
| Geometry Nodes | procedural-modeling | hard-surface for source assets |
| Sculpt surface | sculpt-surface | hair or simulation only when requested |
| Hair Curves | hair | sculpt-surface for source geometry |
| Rigid/cloth/soft/fluid | simulation | background-jobs for baking |
| Render/compositor/bake/pack | render-compositing | export |
| Grease Pencil | grease-pencil | cinematography for delivery camera |
| Camera tracking | tracking | render-compositing for tracked masks |
| VSE timeline | sequence-editing | export/background-jobs |
| Shot-list blocking / white-model previs | previs | cinematography, sequence-editing, background-jobs |
| Numeric acceptance | quality-validation | the owning production Skill |

## Conditional jobs

- `job.submit(kind=EXPORT|RENDER_STILL)` → background-jobs + render-compositing.
- `job.submit(kind=RENDER_ANIMATION_FRAMES)` → background-jobs + render-compositing.
- `job.submit(kind=COMPOSE_VIDEO)` → background-jobs + sequence-editing.
- `job.submit(kind=BAKE_POINT_CACHES)` → background-jobs + simulation.
- `job.status/cancel/recover/resume` → background-jobs; resume is explicit and frame-sequence-only.

Never infer upload, payment, extension installation or overwrite authorization from a domain route.

## Failure routing

- Missing foreground VIEW_3D/CLIP_EDITOR → report the required editor; do not use expert Python as a substitute.
- Stale topology or scene revision → inspect again and create a fresh selection/transaction.
- Failed milestone with no user takeover → recover; after takeover, preserve user edits and begin from a new inspection.
- Missing optional extension → report unavailable and stop; do not install automatically.
