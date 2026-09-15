---
name: blender-production
description: Domain reference library routing into every Blender production skill (modeling, retopology, UV, rigging, animation, hair, simulation, Grease Pencil, materials, render/compositing, VSE, export, jobs, recovery, connector, Jimeng upload). Read the routing table, then only the skill matching your task.
---

# Blender 生产参考库（路由）

本技能是**按需阅读的路由**：先在下表找到你的领域，再去读对应的一等技能（`skills/` 目录内全部可用）。
**动手前不读对应技能 = 大概率返工。** 命令参数与验收阈值以各技能文档为准。

| 技能 | 覆盖 |
|---|---|
| `blender-background-jobs` | Run snapshot-isolated Blender exports, durable animation frame sequences, explicit frame recovery, verified video composition, still renders, and simulation baking without blocking the foreground scene. |
| `blender-character-animation` | Animate a registered Blender character rig and a single interactive prop with editable timing, IK controls, constraints, and continuity checks. |
| `blender-character-rigging` | Build and inspect editable Blender armatures, skin weights, IK controls, pole targets, joint limits, and prop constraints for character work. |
| `blender-cinematography` | Design and validate Blender cameras, lenses, subject aiming, path motion, focus, framing, and controlled handheld response. |
| `blender-connector` | Connect Codex to an already-open Blender window through the pinned PartMe Blender MCP Add-on. |
| `blender-curves` | Build editable Blender paths, profiles, cables, rails, or curve-driven props using registered curve commands. |
| `blender-design` | Turn a user's idea into a Blender scene through milestone-based modeling, materials, lighting, camera, and animation commands. |
| `blender-export` | Export an approved Blender snapshot to verified model, image, video, EXR, USD, or Alembic artifacts using compatible receipt contracts. |
| `blender-grease-pencil` | Create editable Blender Grease Pencil layers, materials, frame drawings, and mixed 2D/3D scenes with structured stroke data. |
| `blender-hair` | Create and inspect native Blender Hair Curves from explicit surface-local strand points, radii, and bound source surfaces. |
| `blender-hard-surface` | Create editable hard-surface, product, mechanical, or prop geometry with registered Blender mesh, modifier, collection, and recipe commands. |
| `blender-harness` | Launch a managed Blender harness session and dispatch structured JSON commands through harness_cli.py. Covers session bootstrap, the closed request envelope (protocolVersion/sessionId/requestId/transactionId/command/arguments/expectedSceneRevision), receipt verification, error codes, capability maturity levels and background jobs. Use this skill for ANY task that needs to create, modify, inspect or export Blender content. |
| `blender-harness-driving` | Drive the Codex Blender Harness from a shell client: launch a session, dispatch the closed request contract, keep the sceneRevision chain coherent, sign action-bound authorizations for gated commands, and verify exported artifacts independently. |
| `blender-inspect` | Inspect an active Blender scene read-only before the agent designs, modifies, previews, or exports it. |
| `blender-jimeng-web` | Use an already enabled official Jimeng Blender uploader to render or select a local video and create a Jimeng Web handoff link. |
| `blender-managed` | Start a non-invasive Blender design session without installing a Blender Add-on. Use for new projects or when the user wants to launch Blender. |
| `blender-mcp-setup` | Set up or diagnose the plugin-owned Blender MCP connection when Blender is missing, the Add-on is disabled, Start MCP Server has not been clicked, or no guarded Harness session is discoverable. |
| `blender-preview` | Capture fresh camera, front, side, and top Blender previews for milestone review or visual diagnosis. |
| `blender-previs` | Use when turning a story or shot list into a color-coded white-model previs video in Blender, producing placeholder blocking, exact cut timing, and a machine-readable geometry-to-role map for downstream Seedance video generation. |
| `blender-procedural-modeling` | Build or update reusable Blender Geometry Nodes systems and parameterized environments with version-probed node and socket semantics. |
| `blender-quality-validation` | Measure Blender geometry, character, prop, collision, motion, and camera acceptance criteria against explicit objects, frames, proxies, and tolerances. |
| `blender-recover` | Rollback a failed Blender milestone or resume from the latest confirmed checkpoint without replaying uncommitted commands. |
| `blender-render-compositing` | Configure Blender Eevee or Cycles, render passes, color management, material baking, dependency packing, compositor nodes, and verified extended exports. |
| `blender-retopology` | Set up, project, transfer data layers for, and validate editable retopology surfaces against source meshes using registered retopo commands. |
| `blender-scene-assembly` | Organize Blender scenes, collections, object identity, transforms, visibility, and authorized reusable assets without losing editability or provenance. |
| `blender-sculpt-surface` | Create and refine Blender surface detail with topology-bound masks, displacement, foreground sculpt strokes, voxel remesh, Multires, and cleanup modifiers. |
| `blender-sequence-editing` | Assemble editable Blender VSE timelines from images, image sequences, scenes, movies, text, and sound, including timing, speed, transitions, audio fades, compositor modifiers, and verified local output. |
| `blender-simulation` | Configure and validate Blender rigid-body, collision, cloth, soft-body, smoke, point-cache, and fluid-cache workflows. |
| `blender-tracking` | Load approved footage, create normalized Blender tracking markers, solve a foreground camera, set up the scene, and validate reprojection error. |
| `blender-use` | Route requests to managed or Connector Blender workflows when a user wants to create, modify, review, save, or export a Blender design. |
| `blender-uv-material` | Prepare UVs and physically based Blender materials for editable product or character assets, including texture color-space and normal-map semantics. |

## 通用纪律（所有领域共用）

1. **闭合契约**：命令参数以技能文档的参数表为准；多余参数会被拒绝，这不是 bug。
2. **回执审计**：产物核对存在性、非零大小、SHA-256、格式；模型格式要求隔离重导入验证，媒体走探测。
3. **测量优先**：验收断言必须是测量值（计数、误差、比率、哈希），并配有能失败的对照。
4. **成熟度门槛**：交付物只能来自 L3+ 命令；L1 输出仅供探索（查 `blender-capabilities`）。
5. **revision 链**：快照 → 修改 → 导出的 `expectedSceneRevision` 链必须连贯，断链即重做。
6. **如实申报**：没验证的写"未验证"，没跑的平台写"未运行"，阈值没触发的写"未触发"。
