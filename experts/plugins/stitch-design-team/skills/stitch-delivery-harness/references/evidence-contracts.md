# 外部证据合同

Stitch、ImageGen、OCR和视觉评估由真实工具执行；本地 Harness 只接收以下脱敏 envelope：

Stitch source evidence 通过后不会直接请求 ImageGen，而是进入 `AWAITING_ART_DECISION`。美术决策不是外部工具 evidence；它只接受用户严格回复的 `enhance`、`keep_stitch` 或 `cancel`，通过 `art-decision --user-response` 写入独立 receipt。命令不提供可伪装来源的 `--source user`，也不接受或映射模糊确认。`enhance` 才允许后续 imagegen evidence；`keep_stitch` 的 editability evidence 必须绑定当前 run 已接受的 Stitch source HTML/render；`cancel` 不接受后续 evidence。

```json
{
  "schema_version": 1,
  "step": "imagegen",
  "provider": {"name": "provider", "tool": "tool-name", "model": "reported-version"},
  "invoked_at": "2026-09-14T00:00:00Z",
  "source_artifacts": [{"path": "artifacts/source.png", "sha256": "64-lowercase-hex"}],
  "artifacts": [{"path": "artifacts/art.png", "sha256": "64-lowercase-hex", "mime": "image/png", "width": 1350, "height": 768}],
  "result": {"status": "generated"}
}
```

路径必须位于当前 run；哈希在写 evidence 前从实际文件计算。不得保存 API Key、Cookie、Authorization/Header、base64 全文或带签名下载 URL。供应商只返回成功文本却没有产物时，不创建通过 evidence。

OCR 的 `result.texts` 保存识别文本数组；视觉评估的 `result.scores` 必须包含 `hierarchy`、`density`、`color`、`component_quality`、`completion`，并携带 `layout_score`。未知写入只保存 `schema_version`、`step` 和 `result: "unknown"`，不得伪造资源 ID。

使用 `EvidenceWriter` 的 `stitch_generation`、`imagegen`、`ocr`、`roundtrip`、`editability` 和 `visual_review` 方法生成类型化 envelope。`imagegen` 必须传真实 `width`/`height`。`editability` 必须输入 before/edited/restored HTML 与 render 六个文件，写出六个唯一 `semantic_role`；任一 result 哈希不等于实际 artifact 哈希、edited 未变化或 restored 不等于 before，Harness 均拒绝。`visual_review` 的 source artifacts 只能来自当前 run 的 imagegen/roundtrip receipts。

`not_applied` 与 `applied` reconciliation 都必须包含三条类型化 `read_probes`：每条使用唯一的 `get_project`、`list_screens` 或 `get_screen`，并提供带时区 `invoked_at`、唯一 `response_id`、枚举 `status`、`result_sha256` 和唯一的 run-local `application/json` artifact。artifact 自身 SHA 必须匹配文件，result SHA 必须匹配解析后的规范结果；artifact JSON 也执行递归敏感信息检查。裸工具名列表不能授权重试。

每个 probe artifact 的 JSON 必须逐字段等于声明的 tool、invoked_at、response_id、status，并包含布尔结果 `result.target_found`；`get_screen: skipped` 还必须且只能包含 `reason: "no_candidate_id"`。新式 `list_screens=found/false` 结果还必须包含与unknown目标一致的 `project_id`、`complete:true` 和最多100个唯一小写SHA-256 `title_hashes`；Harness计算规范化预期标题哈希并验证其不在清单中。`result_sha256` 是该 result 的规范JSON哈希。`applied` 要求三工具均为 `found/true`；错误项目、不完整清单、命中预期标题、矛盾、陈旧、symlink或路径逃逸证据一律拒绝。

receipt 追加使用 run-local pending journal：journal、receipt、manifest 三个持久化边界中的任一中断，下一次加载都会校验 identity/hash/previous-chain 后完成该追加或失败关闭。比较图覆盖锁同时检查通过的 `visual-judge` receipt；即使状态提交中断，只要 receipt 已接受，就禁止重写三张比较图。
