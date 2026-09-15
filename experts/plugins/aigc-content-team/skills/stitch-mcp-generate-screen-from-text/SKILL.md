---
name: stitch-mcp-generate-screen-from-text
description: 调用 Stitch generate_screen_from_text 将已准备的页面提示生成视觉屏幕；用户明确要求用 Stitch 文本生成或编排器进入生成步骤时触发。提示润色、已有屏幕编辑与代码实现应走相应入口。
license: Apache-2.0
---

# Stitch 文本生成屏幕

## 快速开始

1. “按已准备提示生成门店预约移动页；先给本地可审阅结果。”
2. “在已知项目创建订单桌面线框图；保留已有范围与来源。”
3. “生成中断后核对是否已有结果；标出缺少的输入和验证状态。”

面向设计师、前端开发者和维护此流程的团队。设计师提供意图与素材，开发者提供工程/工具，团队在交接中保留来源和验收状态。

## 能力边界说明

### ✅ 擅长处理

- 按已准备提示生成门店预约移动页。
- 在已知项目创建订单桌面线框图。
- 生成中断后核对是否已有结果。

### ⚠️ 需要素材

- 真实纯 projectId 字符串。
- 结构明确且无敏感内容的 prompt。
- 目标 viewport 与当前工具实时 schema。

### ❌ 不适用场景及交接

- 仅写或改提示词 → stitch-ui-prompt-architect。
- 修改既有屏幕/生成变体 → stitch-ui-designer。
- 输出可运行程序 → 对应组件转换技能，交付实际屏幕HTML。

## 工作流程

1. 读取当前 MCP schema，保留 ID 为字符串；只发送 schema 当前暴露的字段，未暴露 `deviceType` 或 `modelId` 时必须省略。
2. 核对项目和结构提示，已应用系统时遵循 architect 的独立系统通道。
3. 调用一次 generate_screen_from_text，记录返回session/outputComponents及成功或未知状态。
4. 通过 `list_screens` 的纯 `projectId` 获取真实 screen ID，再用 `get_screen` 的 `name: projects/{project}/screens/{screen}` 读取结果，并用 `get_project` 核对归属。
5. 验证截图和HTML；中断不重发同一写调用，先 get_project/list_screens/get_screen 对账；无候选记明 get_screen 未执行原因。
6. 用 `get_screen` 顶层 `deviceType`、`width`、`height` 核对设备保真：提供方可能忽略请求的设备（2026-09-14 实测：三条写路径请求 `TABLET` 均返回 `DESKTOP 2560×2048`）。设备不一致时停止并如实报告，不要改用 `edit_screens` 或 `generate_variants` 重试。提供方尺寸是设备像素，`390×884` 返回 `780×1768`（2×），不要按 1px 误差处理。

按依赖排序：来源核对 → 本地产物 → 已授权外部操作 → 验证交接。多任务先做当前主路径；缺信息先输出假设草案，再精确列明缺少什么以及用途，不使用“请提供更多背景”的空泛提示。

## 安全与结果验证

不读取无关账号配置，不收集用户密码；凭据只由环境或已授权连接器提供。示例只用演示数据；上传前将客户姓名、电话、订单号替换为演示值，并检查 HTML、截图和文件元数据。禁止将密钥、会话 cookie、base64 全文或签名下载 URL 写入报告/版本库。未经验证的参数、视觉效果、业务数字不得编造；输出注明来源、决策依据、实际执行与尚未验证部分。

- 模型和设备属于当前schema而非历史猜测。
- sessionId不被当screenId。
- 写成功与资产下载/视觉验证分开记录。

可定制：设备、已验证模型、prompt、项目、输出资产目录。增值检查：schema实时核对；session与screen区分；写中断恢复。

## FAQ

**Q1：交付的主要结果是什么？** 本地输入 projectId='123'、Tablet 768x1024、三段预约提示 → 只含 projectId/prompt 的待调用参数草案；没有工具回执则 screenId 未确认，不虚构。

**Q2：什么时候应换用其他入口？** 仅写或改提示词 → stitch-ui-prompt-architect；修改既有屏幕/生成变体 → stitch-ui-designer；输出可运行程序 → 对应组件转换技能，交付实际屏幕HTML。

**Q3：缺少输入会怎样？** 先给明确标记的本地假设草案，并列出“需要补充：真实纯 projectId 字符串；结构明确且无敏感内容的 prompt；目标 viewport 与当前实时 schema”。依赖这些输入的写操作不执行。

**Q4：怎样判断完成？** 模型和设备属于当前schema而非历史猜测；sessionId不被当screenId；写成功与资产下载/视觉验证分开记录。

**Q5：怎样定制？** 设备、已验证模型、prompt、项目、输出资产目录；未提供时沿用现有项目值并标明假设。

**Q6：是否自动上传、安装或上线？** 只执行当前请求与已有授权覆盖的动作；没有远程回执不称上传成功，没有运行验证不称上线。额外安装或扩大范围需先说明具体影响。

## 按需参考

- 执行详细映射、API 或模板时读 [扩展流程](references/workflow.md)。
- 遇到失败/异常输入时读 [反模式与 Gotchas](references/anti-patterns.md)。
- 涉及边缘场景、兼容性、定制和授权时读 [深度 FAQ](references/faq-deep.md)。
- 需要完整输入输出及验证场景时读 [本地应用示例](examples/local-validation.md)。
- 本地实现依据为当前技能伴随源码及 [固定上游快照](https://github.com/google-labs-code/stitch-skills/tree/0337446dadde6f8c94210444e2aa9d546126480f)；结构遵循 [Agent Skills 规范](https://agentskills.io/specification)。工具当前行为以实际 schema 为准，未连接时不声称已核验线上行为。
