---
name: stitch-delivery-harness
description: Use when a Stitch screen must become a complete high-fidelity delivery with editable HTML, art enhancement, verification, user approval, and traceable archival.
license: Apache-2.0
---

# Stitch 可编辑设计交付

把页面交付当作一个有限、可恢复的证据流程。通用状态由插件 Harness 管理；业务项目只保存规格、产物、receipts 和批准归档。不能以工具成功文本标记完成。

## 快速开始

- “把已确认的 Stitch 登录页做成可编辑 HTML 与美工稿闭环。”
- “继续这个 Harness run，先告诉我下一项缺什么证据。”
- “对比回灌后的 Stitch 页面和 ImageGen 稿，批准前不要归档。”

适合需要可交付设计的产品、设计和前端团队；只想查询 Stitch 项目或做一次轻量编辑时使用对应单操作 Skill。

## 能力边界说明

### ✅ 擅长

- 完成 Stitch 原稿交付，或在用户明确选择后完成 Stitch 与 ImageGen 的高保真闭环。
- 验证 HTML、尺寸、文案、业务规则和可编辑性。
- 生成比较证据并在批准后归档。

### ⚠️ 需要素材或能力

- 页面规格和设计语言。
- 可用的 Stitch、ImageGen、OCR及视觉评估工具。
- 用户对最终候选稿的明确批准。

### ❌ 不适用

- 单纯查询项目或屏幕：使用 Stitch 读取 Skill。
- 只生成一次页面且不要求交付闭环：使用生成屏幕 Skill。
- 无授权发布、删除远程项目或代替用户批准：停止并说明所需授权。

## 入口

1. 完整读取项目的 `.stitch/specs/<page-id>.json`。
2. 从本 Skill 向上两级定位插件根目录，调用：

   ```bash
   python /absolute/plugin/root/scripts/stitch_harness.py spec init --project /absolute/project --page-id page-id
   python /absolute/plugin/root/scripts/stitch_harness.py start --project /absolute/project --spec page-id
   ```

3. `spec init` 只创建不存在的 starter spec，绝不覆盖现有规格；用户确认后再 `start`。
4. 已有运行使用 `status` 或 `resume`，不得重新创建 run。
5. Stitch 原稿验收后，Harness 必须停在 `AWAITING_ART_DECISION`，逐项向用户展示：`enhance`（二次图片生成）、`keep_stitch`（保留 Stitch 原稿）或 `cancel`（取消），然后结束当前执行并等待新回复。只有用户新回复严格等于其中一个规范值时，才把该原文传给 `art-decision --user-response`；“确认”“继续”“做按”“可以”等模糊回复必须继续追问，不得代选、翻译、同义映射或从旧消息推断。
6. 只执行 Harness 返回的 `next_action`；调用真实 Stitch、ImageGen、OCR 或视觉评估工具后，用 `stitch_harness.evidence_writer.EvidenceWriter` 的对应类型方法生成 evidence，再调用 `resume --evidence`。
7. 选择 `enhance` 后，双图比较执行 `python scripts/setup_harness_runtime.py run compare ...`；输入只能从当前 run 的 imagegen 与 roundtrip receipts 派生。选择 `keep_stitch` 时不调用 ImageGen，直接对已接受的 Stitch HTML/render 做可逆编辑探针。
8. `provider_generated` 严格核对 Provider 设备与缩放；`imported_editable_html` 仍要求一个与规格画布完全一致的真实 render artifact。OCR 报告任何 `observed_text_drift` 都失败。增强分支回灌前必须生成 `stitch.normalize` receipt，只允许声明的 `data-purpose` 一对一替换。

## 硬门禁

- Stitch 写入超时或回执未知：进入 `RECONCILING`，只用项目/屏幕读取工具对账，不直接重发；读探针形成 evidence 后执行 `reconcile --evidence`，三次仍未知转为 `BLOCKED`。
- `BLOCKED` 只有明确原因的 `recover --reason "..."` 能恢复；普通 `resume` 不得绕过。
- 尺寸取页面规格的内容画布，不取浏览器外框或设备像素比。
- 回灌后必须重新下载 HTML 和渲染图，并完成探针编辑与恢复。
- 不相信 `edit_screens` 的成功文本；语义修正必须通过确定性本地规范化、HTML 上传和重新下载后的哈希/DOM 验证。
- `SOURCE_ACCEPTED` 不授权 ImageGen；缺少明确的用户美术决策时必须停在 `AWAITING_ART_DECISION`。
- 自动门禁全部通过后只能进入 `AWAITING_USER_APPROVAL`。
- 向用户同时展示最终 Stitch 渲染、美工稿和并排比较图；没有明确批准，不调用 `approve` 或 `archive`。
- 凭据只经当前进程或受限用户配置交给本地 stdio 代理；不读取、打印或写入 evidence。

## 停止条件

状态为 `BLOCKED`、未知写入尚未对账、达到三轮上限、缺少真实工具回执或等待用户批准时立即停止，并返回当前 run ID、已通过门禁、失败门禁和下一项所需证据。

信息不足时先执行只读 `status`，基于现有规格给出当前状态和缺项；不猜资源 ID、尺寸、文案或批准结果。多页面请求按已批准 backlog 顺序逐页执行，一个页面未完成不并发归档下一页。

可定制内容来自页面规格：画布、主题、固定文案、可编辑区域、业务断言、视觉阈值和归档位置。不得在运行中静默改写规格。

## FAQ

**没有页面规格？** 先创建并让用户确认规格，不启动 run。

**工具说成功就可以继续吗？** 不可以；必须下载文件并校验哈希和对应门禁。

**写操作超时怎么办？** 保存 unknown，进入显式 `RECONCILING`，只读对账；三次未解转为 `BLOCKED`，不得盲重试。

**OCR 通过能批准吗？** 不能；OCR 只是一个自动门禁。

**可以直接移动最终图片吗？** 可以，但旧会话路径必须保留相对软连接并验证哈希。

**敏感数据怎么处理？** 使用演示数据；evidence 不保存 Key、Cookie、Header、base64或签名 URL。

## 按需参考

- 执行或恢复完整闭环时读取 [工作流](references/workflow.md)。
- 创建外部工具回执时读取 [证据合同](references/evidence-contracts.md)。
- 遇到错误恢复或边缘场景时读取 [反模式](references/anti-patterns.md) 和 [深度 FAQ](references/faq-deep.md)。
- 首次验证桌面登录页时读取 [WeKefu 登录样例](examples/wekefu-login.md)。
