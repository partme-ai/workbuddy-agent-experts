# Current design-system tool contracts

Read the connected MCP schema before every write. The current catalog exposes these request shapes; do not add historical theme, font, device, roundness, color-variant, `name`, or `projectId` fields where they are not present.

## `upload_design_md`

```json
{"projectId":"123", "designMdBase64":"<encoded in process>"}
```

## `create_design_system`

```json
{"projectId":"123"}
```

The response returns `assetId`. Do not infer token fields that are absent from the live schema.

## `create_design_system_from_design_md`

```json
{"selectedScreenInstance":{"id":"<instance-id>","sourceScreen":"projects/123/screens/abc"}}
```

## `update_design_system`

```json
{"assetId":"<asset-id>"}
```

## `list_design_systems`

```json
{"projectId":"123"}
```

## `apply_design_system`

```json
{"selectedScreenInstances":[{"id":"<instance-id>","sourceScreen":"projects/123/screens/abc"}]}
```

`selectedScreenInstances` contains only fields accepted by the live `SelectedScreenInstance` definition. Never freeze model, device, font, or color-variant enum lists in this reference; use exact values from the connected schema when such fields reappear.
