# Harness 工作流

## 固定顺序

页面规格 → Stitch 生成 → HTML/尺寸/文案验收 → 用户美术决策：`enhance` / `keep_stitch` / `cancel`。

- `enhance` → ImageGen 美术增强 → OCR/业务门禁 → 确定性语义规范化 → 回灌 Stitch → 可编辑性验证 → 双图对比 → 用户批准 → 正式归档。
- `keep_stitch` → Stitch 原稿可编辑性验证 → 用户批准 → 正式归档。
- `cancel` → 记录取消并终止，不生成、不批准、不归档。

## 执行协议

1. `preflight` 检查系统凭据、唯一插件来源和本地运行条件。
2. `start` 创建不可复用的 run，返回 `stitch.generate`。
3. 每次真实工具调用后，将文件放入当前 run 的 `artifacts/`，再创建 evidence JSON。
4. `resume` 校验文件哈希、门禁与状态，只返回一个下一动作。
5. Stitch 写操作结果未知时，保存 `result: "unknown"`，并尽量绑定脱敏的 `target.project_id` 与 `target.expected_title`，随后进入 `RECONCILING`。只执行 `get_project`、`list_screens` 或 `get_screen`，为每次读取保存晚于 unknown receipt 的带时区时间、response ID、枚举状态、结果哈希和唯一 JSON artifact。`applied` 只接受三者均找到目标。`not_applied` 除兼容旧式明确 not_found 证据外，也接受 project found、与目标项目一致且分页完整的list_screens标题哈希清单不含预期标题，以及因无候选ID而记录的 `get_screen: skipped/no_candidate_id`；错误项目、不完整清单或命中候选均失败关闭。完整 receipt 与最终状态一次提交前始终保持 `RECONCILING`。每次未解对账递增 attempts，第三次转为 `BLOCKED`。
6. Stitch 原稿验收后进入 `AWAITING_ART_DECISION`。向用户逐项展示 `enhance`、`keep_stitch`、`cancel` 并停止。只有用户的新回复严格等于其中一个规范值时，才原样执行 `art-decision --user-response <原文>`；模型、自动评分、旧请求和模糊确认均不能代替或映射本次选择。
7. 仅 `enhance` 分支调用 ImageGen；结果先过尺寸、OCR 和业务断言。Codex 内置视觉可作为 OCR provider，但必须记录实际识别文本；`observed_text_drift` 非空时强制失败。
8. OCR 通过后，对 Stitch 重建的可编辑 HTML 执行确定性 `data-purpose` 规范化。`stitch.normalize` receipt 必须绑定原始/输出 HTML 和显式映射；禁止修改可见文字、样式或其他结构。
9. 将规范化 HTML 上传 Stitch，再重新下载 HTML 和渲染图。探针编辑需保存 before/edited/restored 三份 HTML 与三张 render；edited 哈希必须变化，restored HTML/render 哈希必须分别与 before 完全相等。`keep_stitch` 分支对已接受的 Stitch 源 HTML/render 执行同一探针，不伪造 ImageGen 或回灌证据。
10. `enhance` 分支的双图阶段从 receipts 读取已接受的 ImageGen art render 与最终 Stitch render，禁止接受调用者另传图片；生成 `side-by-side.png`、`overlay.png`、`diff-heatmap.png`，并把两张源图写入 evidence `source_artifacts` 和 receipt `inputs`。未接受 visual receipt 时可原子替换完整三图且失败回滚；一旦通过的 visual receipt 已存在，即使状态更新曾中断，也禁止覆盖。布局分数和五个视觉维度通过后进入 `AWAITING_USER_APPROVAL`。
11. 用户批准文件必须绑定该分支的必需产物：`enhance` 绑定本次所见 HTML、两张最终图和比较图哈希；`keep_stitch` 绑定已接受的 Stitch HTML/render。文件变化会使批准失效。
12. `archive` 只接受 `APPROVED`。若移动对话中已经引用的图片，必须保留可读的相对软连接。
13. 若 archive 已完成原子发布、但 run 状态持久化中断，重新执行同一 `archive --run`；Harness 先复验已发布收据链、批准和哈希，再只补写 `ARCHIVED` 状态。

## 可执行命令

```bash
python scripts/stitch_harness.py spec init --project /absolute/project --page-id login
python scripts/stitch_harness.py status --project /absolute/project --run RUN_ID
python scripts/stitch_harness.py art-decision --project /absolute/project --run RUN_ID --user-response enhance
python scripts/stitch_harness.py reconcile --project /absolute/project --run RUN_ID --evidence /absolute/reconciliation.json
python scripts/setup_harness_runtime.py run compare --project /absolute/project --run RUN_ID --scores /absolute/scores.json
python scripts/stitch_harness.py recover --project /absolute/project --run RUN_ID --reason "只读探针确认远程写入未生效"
python scripts/stitch_harness.py archive --project /absolute/project --run RUN_ID
```

## 状态语义

`passed` 表示对应机器门禁和 receipt 同时有效；`failed` 表示结果明确不合格；`RECONCILING` 表示远程写入结果不确定且只允许读探针；`BLOCKED` 表示三次未解或不能在现有授权内继续。禁止把后两者改写为成功。
