---
name: stitch-upload-to-stitch
description: 将已授权的本地图片或 HTML 安全上传到指定 Stitch 项目，并将 Markdown 路由到远程 upload_design_md；只生成本地文件、检索项目或部署网站时不触发。
license: Apache-2.0
---

# 上传本地资产到 Stitch

## 快速开始

1. “上传脱敏的门店预约页 HTML；先给本地可审阅结果。”
2. “上传品牌 DESIGN.md 供系统创建；保留已有范围与来源。”
3. “上传用户提供的演示稿 PNG；标出缺少的输入和验证状态。”

面向设计师、前端开发者和维护此流程的团队。设计师提供意图与素材，开发者提供工程/工具，团队在交接中保留来源和验收状态。

## 能力边界说明

### ✅ 擅长处理

- 上传脱敏的门店预约页 HTML。
- 将品牌 DESIGN.md 路由到 MCP `upload_design_md`。
- 上传用户提供的演示稿 PNG。

### ⚠️ 需要素材

- 真实 projectId。
- 支持格式的已审核本地文件。
- 通过 `platform_secret_provider()` 读取的凭据与上传授权。

### ❌ 不适用场景及交接

- 远程套用设计系统 → stitch-manage-design-system。
- 从代码生成上传文件 → stitch-code-to-design。
- 公开部署网站 → 目标部署流程，交付 HTML 资产包。

## 工作流程

1. 核对文件路径、大小、类型和目标项目，确保授权覆盖这些内容。
2. 图片/HTML 脚本通过 `platform_secret_provider()` 使用环境优先、用户配置兜底的凭据链；CLI 不接受密钥或服务根地址参数。
3. Markdown 不走私有 REST 脚本；读取文件后在进程内编码，并调用当前 MCP `upload_design_md`。
4. 私有 REST 固定到 `https://stitch.googleapis.com` 并单次发送；禁止重定向和自动重试。
5. 用 `get_project` 的项目资源名、`list_screens` 的纯项目 ID、`get_screen` 的 `name: projects/{project}/screens/{screen}` 对账。

按依赖排序：来源核对 → 本地产物 → 已授权外部操作 → 验证交接。多任务先做当前主路径；缺信息先输出假设草案，再精确列明缺少什么以及用途，不使用“请提供更多背景”的空泛提示。

## 安全与结果验证

不读取无关账号配置，不收集用户密码；凭据只由环境或已授权连接器提供。示例只用演示数据；上传前将客户姓名、电话、订单号替换为演示值，并检查 HTML、截图和文件元数据。禁止将密钥、会话 cookie、base64 全文或签名下载 URL 写入报告/版本库。未经验证的参数、视觉效果、业务数字不得编造；输出注明来源、决策依据、实际执行与尚未验证部分。

- argv/日志/报告不含密钥、base64 或完整响应。
- PNG/JPG/JPEG/WEBP 映射 screenshot，HTML/HTM 映射 htmlCode；Markdown 使用 `upload_design_md`。
- REST 只接受当前 `results[].screen` 响应并输出校验后的 screen name。

可定制：title、generated-by、文件路径。服务根地址不可定制。增值检查：配置凭据；小输出 ID 交接；无自动重试和重定向。

## FAQ

**Q1：交付的主要结果是什么？** 本地 HTML 请求使用 htmlCode、text/html 和 DOCUMENT；远程执行后只交付经过类型、格式与项目归属校验的 screen/instance 标识。完整离线输入、请求和模拟回执见本地应用示例；请求构造不代表上传成功。

**Q2：什么时候应换用其他入口？** 远程套用设计系统 → stitch-manage-design-system；从代码生成上传文件 → stitch-code-to-design；公开部署网站 → 目标部署流程，交付 HTML 资产包。

**Q3：缺少输入会怎样？** 先给明确标记的本地假设草案，并列出“需要补充：真实 projectId；支持格式的已审核本地文件；通过运行环境注入的 STITCH_API_KEY 与上传授权”。依赖这些输入的写操作不执行。

**Q4：怎样判断完成？** argv/日志/报告不含密钥、base64 或完整响应；本地 REST 和远程 Markdown 路径分离；返回的 screen name 已经只读对账。

**Q5：怎样定制？** title、generated-by、文件路径；服务根地址固定为 Google 官方 origin。

**Q6：是否自动上传、安装或上线？** 只执行当前请求与已有授权覆盖的动作；没有远程回执不称上传成功，没有运行验证不称上线。额外安装或扩大范围需先说明具体影响。

## 按需参考

- 执行详细映射、API 或模板时读 [扩展流程](references/workflow.md)。
- 遇到失败/异常输入时读 [反模式与 Gotchas](references/anti-patterns.md)。
- 涉及边缘场景、兼容性、定制和授权时读 [深度 FAQ](references/faq-deep.md)。
- 需要完整输入输出及验证场景时读 [本地应用示例](examples/local-validation.md)。
- 本地实现依据为当前技能伴随源码及 [固定上游快照](https://github.com/google-labs-code/stitch-skills/tree/0337446dadde6f8c94210444e2aa9d546126480f)；结构遵循 [Agent Skills 规范](https://agentskills.io/specification)。工具当前行为以实际 schema 为准，未连接时不声称已核验线上行为。
