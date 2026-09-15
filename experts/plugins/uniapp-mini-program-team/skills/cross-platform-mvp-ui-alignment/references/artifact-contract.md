# 交付物合同

## 差异与裁决表

| 领域 | 平台 A 事实 | 平台 B 事实 | 冲突 | 裁决 | 依据 | 状态 |
|---|---|---|---|---|---|---|

状态：`confirmed`、`inferred`、`needs-decision`、`not-verified`。

## 页面矩阵字段

- `page_id`：稳定 ID。
- `scenario`、`trigger`、`state`、`visible_outcome`、`next_action`。
- `platform_device_coverage`：各平台设备覆盖。
- `asset_path`：规格相对路径。
- `maturity`：`candidate`、`approved-master`、`native-screenshot`。

## Design manifest

```json
{
  "specVersion": "...",
  "designLanguageVersion": "...",
  "scenarioDataVersion": "...",
  "assets": [{
    "pageId": "P01",
    "platform": "android",
    "device": "phone",
    "width": 390,
    "height": 884,
    "path": "android/phone/P01-...png",
    "source": "shared-render-input",
    "maturity": "candidate"
  }]
}
```

尺寸优先服从用户或项目规格。没有约束时，Mobile `390x884`、Tablet `768x1024`、Desktop `1280x1024` 仅作为待确认起点。

验证报告包含检查对象、方法、实际结果、证据路径与结论，明确区分规格一致性、生成成功、资产完整性、视觉批准和原生运行。
