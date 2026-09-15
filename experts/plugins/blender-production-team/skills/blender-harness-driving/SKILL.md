---
name: blender-harness-driving
description: "Drive the Codex Blender Harness from a shell client: launch a session, dispatch the closed request contract, keep the sceneRevision chain coherent, sign action-bound authorizations for gated commands, and verify exported artifacts independently."
---

# Driving the Harness

This is the mechanical layer beneath the domain Skills. It owns the request contract, the
revision chain, transaction snapshots, authorization, and verification. Delegate the actual
modeling, lookdev, jobs, and validation decisions to the precise domain Skill advertised by
`capability.describe`.

## Session and dispatch

Start one session per production task with `scripts/launch_harness.py`, then dispatch through
`scripts/harness_cli.py --descriptor <descriptor> --request <file>`; see
[managed sessions](../blender-managed/SKILL.md). An installed copy may live under a
different root than this repository, so hold the plugin root in one constant rather than
rebuilding paths, and do not restart a session simply because the root moved — the process and
its descriptor stay valid.

Every request is a closed contract: `protocolVersion` `codex-blender/v1`, `sessionId`,
`requestId`, `transactionId`, `command`, `arguments`, and `expectedSceneRevision` for mutations.
Read the receipt from stdout for `status`, `sceneRevision`, `changedObjects`, `warnings`, and
`result` or `error{code,message,retryable}`. Batch a milestone as
`transaction.begin`, mutations, `transaction.commit`; on any failure issue
`transaction.rollback` and stop.

## Revision chain

Take `expectedSceneRevision` from the live response of the previous command; never guess it.
A missing revision is rejected as `STALE_SCENE_REVISION`.

`object.describe`, `mesh.inspect`, and `scene.inspect` look read-only but are dispatched as
mutations: send them inside a transaction with a revision. A revision without an open
transaction fails with `TRANSACTION_NOT_FOUND`.

A transaction is a lease, not a label. `begin` snapshots; each mutation bumps the revision;
`commit` approves the snapshot at the resulting revision. `export.file` requires a snapshot
committed at the current revision or it fails with `MILESTONE_NOT_APPROVED`. After takeover or
re-inspection, begin a new transaction and never reuse a pre-takeover approval.

## Gated commands

`object.delete`, `export.file` with `overwrite`, and other `risk: gated` commands are refused
with `AUTHORIZATION_REQUIRED` until the request carries a claim minted by
`session.authorize {"action": <command>, "requestId": <the exact requestId being sent>,
"userConfirmed": true, "ttlSeconds": N}`. The claim is action- and request-bound, so one
authorization cannot cover a loop; mint a fresh requestId per gated step. Confirm with the user
first, and on refusal report the error code verbatim instead of retrying around it.

## Export parameters

`export.file` accepts `path`, `snapshotId` (required), `sessionId`, `overwrite`, `parameters`.
Keys are whitelisted per format and an unknown key is `INVALID_ARGUMENT`:

- glb / gltf: `use_selection`, `use_visible`, `use_renderable`, `export_apply`, `export_animations`, `export_materials`
- fbx: `use_selection`, `use_visible`, `use_active_collection`, `bake_anim`, `apply_scale_options`
- obj: `export_selected_objects`, `apply_modifiers`, `export_materials`, `export_uv`
- blend: none

There is no `export_cameras` or `export_lights` and no object-type filter, so a mesh-only model
requires temporarily setting studio lights and cameras invisible, exporting with
`use_visible`, then restoring them. Keep the `.blend` exported separately: a project file carries
the studio rig, a GLB or FBX should not. See [export](../blender-export/SKILL.md).

## Verify what you ship

Never trust a receipt alone. Re-hash the file on disk. Parse the container: for GLB, read the
12-byte header plus the JSON and BIN chunks and list `nodes`, `meshes`, `materials`, `cameras`;
for FBX, walk the binary node tree (version at offset 23, 8-byte fields at version >= 7500,
and null records still occupy 25 bytes) and count `Model`, `Geometry`, `Material`, `Camera`.
Then re-import into an empty scene and measure vertices, polygons, triangles, non-manifold and
boundary edges, loose vertices, and world-space bounds. Use `bmesh`: `MeshEdge.is_manifold` no
longer exists in Blender 5.x.

Triangles must agree per object across GLB and FBX; GLB vertex counts are higher because glTF
splits vertices per normal and UV. Assert that construction helpers and QA copies never appear
in an exported node list. Report unverified qualities explicitly rather than implying coverage.

Confirm maturity with `capability.list` and `capability.describe` before relying on a command:
L1 results are query-only and must not be delivered as production output.

Normalise scene scale to real units before lighting; a part built as 90 Blender units reads as
90 m to the renderer and a studio rig sized for a 9 cm part renders it black. When a mesh
operation produces a defect, preserve the broken object as a hidden `*_DEFECTIVE` record in a
`QA_Verify` collection, rebuild the part, and let the export omit it.

For long or high-quality renders, use [background jobs](../blender-background-jobs/SKILL.md);
the synchronous `preview.capture` path is EEVEE-bound and client-timeout-bound.
