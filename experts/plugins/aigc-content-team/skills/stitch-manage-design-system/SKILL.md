---
name: stitch-manage-design-system
description: 查询、创建、更新或应用 Stitch 项目级设计系统；当已有 DESIGN.md 要关联远程项目，或需对指定屏幕应用现有系统时触发。单纯提取源码 token 不触发远程写入。
license: Apache-2.0
---

# 管理 Stitch 项目设计系统

## 快速开始

1. “把门店后台 DESIGN.md 建为项目系统；先给本地可审阅结果。”
2. “给预约列表和详情两屏应用现有系统；保留已有范围与来源。”
3. “只读核对项目当前设计系统与屏幕实例；标出缺少的输入和验证状态。”

面向设计师、前端开发者和维护此流程的团队。设计师提供意图与素材，开发者提供工程/工具，团队在交接中保留来源和验收状态。

## 能力边界说明

### ✅ 擅长处理

- 把门店后台 DESIGN.md 建为项目系统。
- 给预约列表和详情两屏应用现有系统。
- 只读核对项目当前设计系统与屏幕实例。

### ⚠️ 需要素材

- 真实 projectId 和可用 MCP schema。
- 可共享的 DESIGN.md 或现有 assetId。
- 待应用屏幕的实例 id/sourceScreen 与修改范围。

### ❌ 不适用场景及交接

- 只写本地设计文档 → stitch-design-md。
- 从源码提取样式 → stitch-extract-design-md。
- 修改业务接口或数据库 → 目标项目开发流程，附设计系统对组件的映射。

## 工作流程

1. 查询 get_project、list_design_systems 和所需屏幕，保留真实资源 ID 字符串。
2. 检查 DESIGN.md 的 name/colors、颜色角色、字体和圆角；没有原素材时只生成标为建议的本地草案。
3. 已有授权覆盖上传时上传文档，记录返回的 sourceScreen 和 screenInstance.id；否则提交具体资产清单。
4. 按当前 schema 调用 create_design_system_from_design_md，或用现有系统；不把本地文件存在视为远程已应用。
5. apply_design_system 仅传选中实例的 id/sourceScreen，过滤 DESIGN_SYSTEM_INSTANCE；读取回执并更新目标项目 metadata。

按依赖排序：来源核对 → 本地产物 → 已授权外部操作 → 验证交接。多任务先做当前主路径；缺信息先输出假设草案，再精确列明缺少什么以及用途，不使用“请提供更多背景”的空泛提示。

## 安全与结果验证

不读取无关账号配置，不收集用户密码；凭据只由环境或已授权连接器提供。示例只用演示数据；上传前将客户姓名、电话、订单号替换为演示值，并检查 HTML、截图和文件元数据。禁止将密钥、会话 cookie、base64 全文或签名下载 URL 写入报告/版本库。未经验证的参数、视觉效果、业务数字不得编造；输出注明来源、决策依据、实际执行与尚未验证部分。

- selectedScreenInstances 不含 x/y/width/height。
- 系统 assetId 来自 list_design_systems。
- 上传、创建、应用分别有状态，失败不串行继续。

可定制：系统名称、主题、指定实例列表、仅查询/创建/应用模式。增值检查：实例过滤；系统与屏幕分阶段状态；项目级 token 去重。

## FAQ

**Q1：交付的主要结果是什么？** 离线输入实例 {id:'demo-i',sourceScreen:'projects/123/screens/a',x:9} → 请求实例只保留 id/sourceScreen；未调用 apply。

**Q2：什么时候应换用其他入口？** 只写本地设计文档 → stitch-design-md；从源码提取样式 → stitch-extract-design-md；修改业务接口或数据库 → 目标项目开发流程，附设计系统对组件的映射。

**Q3：缺少输入会怎样？** 先给明确标记的本地假设草案，并列出“需要补充：真实 projectId 和可用 MCP schema；可共享的 DESIGN.md 或现有 assetId；待应用屏幕的实例 id/sourceScreen 与修改范围”。依赖这些输入的写操作不执行。

**Q4：怎样判断完成？** selectedScreenInstances 不含 x/y/width/height；系统 assetId 来自 list_design_systems；上传、创建、应用分别有状态，失败不串行继续。

**Q5：怎样定制？** 系统名称、主题、指定实例列表、仅查询/创建/应用模式；未提供时沿用现有项目值并标明假设。

**Q6：是否自动上传、安装或上线？** 只执行当前请求与已有授权覆盖的动作；没有远程回执不称上传成功，没有运行验证不称上线。额外安装或扩大范围需先说明具体影响。

## 按需参考

- 执行详细映射、API 或模板时读 [扩展流程](references/workflow.md)。
- 遇到失败/异常输入时读 [反模式与 Gotchas](references/anti-patterns.md)。
- 涉及边缘场景、兼容性、定制和授权时读 [深度 FAQ](references/faq-deep.md)。
- 需要完整输入输出及验证场景时读 [本地应用示例](examples/local-validation.md)。
- 本地实现依据为当前技能伴随源码及 [固定上游快照](https://github.com/google-labs-code/stitch-skills/tree/0337446dadde6f8c94210444e2aa9d546126480f)；结构遵循 [Agent Skills 规范](https://agentskills.io/specification)。工具当前行为以实际 schema 为准，未连接时不声称已核验线上行为。
