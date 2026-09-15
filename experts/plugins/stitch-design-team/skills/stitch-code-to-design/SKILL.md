---
name: stitch-code-to-design
description: 将已有前端应用迁入 Stitch；用户要求把 React、Vue、Angular 等页面导入、同步为 Stitch 设计时触发。只提取 HTML 或只写 DESIGN.md 时使用对应提取技能。
license: Apache-2.0
---

# 前端源码导入 Stitch

## 快速开始

1. “把企业微信预约管理 Web 页导入 Stitch；先给本地可审阅结果。”
2. “将 Vue 门店排班页连同视觉规范迁移；保留已有范围与来源。”
3. “按 /orders、/settings 两条路由生成可追踪导入清单；标出缺少的输入和验证状态。”

面向设计师、前端开发者和维护此流程的团队。设计师提供意图与素材，开发者提供工程/工具，团队在交接中保留来源和验收状态。

## 能力边界说明

### ✅ 擅长处理

- 把企业微信预约管理 Web 页导入 Stitch。
- 将 Vue 门店排班页连同视觉规范迁移。
- 按 /orders、/settings 两条路由生成可追踪导入清单。

### ⚠️ 需要素材

- 源码目录和可运行 URL 或构建产物。
- 实际 projectId 与目标路由列表。
- 上传范围和可共享的脱敏页面状态。

### ❌ 不适用场景及交接

- 只保存本地 HTML → stitch-extract-static-html。
- 只记录源码设计 token → stitch-extract-design-md。
- 后端数据迁移或上线 → 交给目标项目迁移或部署流程，提供路由和资产清单。

## 工作流程

1. 核对路由、来源提交及目标项目；以请求的页面为界，不扩展到整个应用。
2. 按 stitch-extract-static-html 生成每条路由的独立 HTML，先检查资产闭合与脱敏。
3. 按 stitch-extract-design-md 从当前源码生成 .stitch/DESIGN.md，保留 YAML name/colors 和来源。
4. 在已有上传授权范围内用 stitch-manage-design-system 建立项目系统，记录返回的 sourceScreen 与实例 id。
5. 用 stitch-upload-to-stitch 上传 HTML，title 为路由，generated-by 为 stitch-extract-static-html；读取项目/屏幕确认，再报告文件、系统和屏幕映射。

按依赖排序：来源核对 → 本地产物 → 已授权外部操作 → 验证交接。多任务先做当前主路径；缺信息先输出假设草案，再精确列明缺少什么以及用途，不使用“请提供更多背景”的空泛提示。

## 安全与结果验证

不读取无关账号配置，不收集用户密码；凭据只由环境或已授权连接器提供。示例只用演示数据；上传前将客户姓名、电话、订单号替换为演示值，并检查 HTML、截图和文件元数据。禁止将密钥、会话 cookie、base64 全文或签名下载 URL 写入报告/版本库。未经验证的参数、视觉效果、业务数字不得编造；输出注明来源、决策依据、实际执行与尚未验证部分。

- 每条路由都有 HTML、来源和真实返回 ID。
- DESIGN.md 与 HTML 来自同次快照。
- 上传状态未确认时保留本地产物并停止后续写入。

可定制：路由列表、视口、主题和输出目录；例如只处理 /orders、1280×800、深色。增值检查：路由到屏幕映射；HTML/设计系统同源检查；分阶段恢复清单。

## FAQ

**Q1：交付的主要结果是什么？** 路由 /orders → 本地 .stitch/orders.html；DESIGN.md 来源 src/theme.css；远程状态未执行，等待已授权上传阶段。

**Q2：什么时候应换用其他入口？** 只保存本地 HTML → stitch-extract-static-html；只记录源码设计 token → stitch-extract-design-md；后端数据迁移或上线 → 交给目标项目迁移或部署流程，提供路由和资产清单。

**Q3：缺少输入会怎样？** 先给明确标记的本地假设草案，并列出“需要补充：源码目录和可运行 URL 或构建产物；实际 projectId 与目标路由列表；上传范围和可共享的脱敏页面状态”。依赖这些输入的写操作不执行。

**Q4：怎样判断完成？** 每条路由都有 HTML、来源和真实返回 ID；DESIGN.md 与 HTML 来自同次快照；上传状态未确认时保留本地产物并停止后续写入。

**Q5：怎样定制？** 路由列表、视口、主题和输出目录；例如只处理 /orders、1280×800、深色；未提供时沿用现有项目值并标明假设。

**Q6：是否自动上传、安装或上线？** 只执行当前请求与已有授权覆盖的动作；没有远程回执不称上传成功，没有运行验证不称上线。额外安装或扩大范围需先说明具体影响。

## 按需参考

- 执行详细映射、API 或模板时读 [扩展流程](references/workflow.md)。
- 遇到失败/异常输入时读 [反模式与 Gotchas](references/anti-patterns.md)。
- 涉及边缘场景、兼容性、定制和授权时读 [深度 FAQ](references/faq-deep.md)。
- 需要完整输入输出及验证场景时读 [本地应用示例](examples/local-validation.md)。
- 本地实现依据为当前技能伴随源码及 [固定上游快照](https://github.com/google-labs-code/stitch-skills/tree/0337446dadde6f8c94210444e2aa9d546126480f)；结构遵循 [Agent Skills 规范](https://agentskills.io/specification)。工具当前行为以实际 schema 为准，未连接时不声称已核验线上行为。
