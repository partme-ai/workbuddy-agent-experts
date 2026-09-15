---
name: stitch-shadcn-ui
description: 为 Stitch 来源的 React 页面选择、迁移和验证 shadcn/ui 原语、主题和 registry 内容时触发。首次通用 HTML 转 React 用 stitch-react-components；不自动迁移无关工程。
license: Apache-2.0
---

# Stitch 的 shadcn/ui 迁移

## 快速开始

1. “把预约表单迁为 shadcn Input/Button；先给本地可审阅结果。”
2. “迁移订单详情 Dialog 并保留键盘行为；保留已有范围与来源。”
3. “比较 registry 源码与现有主题 tokens；标出缺少的输入和验证状态。”

面向设计师、前端开发者和维护此流程的团队。设计师提供意图与素材，开发者提供工程/工具，团队在交接中保留来源和验收状态。

## 能力边界说明

### ✅ 擅长处理

- 把预约表单迁为 shadcn Input/Button。
- 迁移订单详情 Dialog 并保留键盘行为。
- 比较 registry 源码与现有主题 tokens。

### ⚠️ 需要素材

- 目标工程与 components.json。
- Stitch 资产及当前组件行为。
- Tailwind/React 版本和待迁移范围。

### ❌ 不适用场景及交接

- 通用 React 页面转换 → stitch-react-components。
- 原生 App → stitch-react-native。
- 业务登录或支付服务 → 项目接口流程，提交表单行为契约。

## 工作流程

1. 读取当前工程版本和 Stitch HTML/截图，明确只迁移的组件。
2. 先读 migration-guide，核对原 Props、状态、键盘与主题。
3. 检索当前可用 registry 工具和组件源，审查依赖与变更再应用。
4. 按现有 cn/cva/主题约定迁移一个组件并保留可访问性，验证后再处理下一个。
5. 运行目标类型/lint/build 与键盘/主题检查；verify-setup.sh 仅是 Tailwind3 启发式，不代表 Tailwind4 或全部通过。

按依赖排序：来源核对 → 本地产物 → 已授权外部操作 → 验证交接。多任务先做当前主路径；缺信息先输出假设草案，再精确列明缺少什么以及用途，不使用“请提供更多背景”的空泛提示。

## 安全与结果验证

不读取无关账号配置，不收集用户密码；凭据只由环境或已授权连接器提供。示例只用演示数据；上传前将客户姓名、电话、订单号替换为演示值，并检查 HTML、截图和文件元数据。禁止将密钥、会话 cookie、base64 全文或签名下载 URL 写入报告/版本库。未经验证的参数、视觉效果、业务数字不得编造；输出注明来源、决策依据、实际执行与尚未验证部分。

- 保留 Dialog 焦点恢复与键盘关闭。
- registry 源和依赖实际审查。
- 浅/深主题及焦点可见性经验证。

可定制：registry、原语、主题、variant、目标组件和迁移顺序。增值检查：逐组件迁移；版本分流；可访问性回归清单。

## FAQ

**Q1：交付的主要结果是什么？** 预约表单 label htmlFor="phone" + Input id="phone"；保留错误 aria-describedby；不把电话号码写入示例。

**Q2：什么时候应换用其他入口？** 通用 React 页面转换 → stitch-react-components；原生 App → stitch-react-native；业务登录或支付服务 → 项目接口流程，提交表单行为契约。

**Q3：缺少输入会怎样？** 先给明确标记的本地假设草案，并列出“需要补充：目标工程与 components.json；Stitch 资产及当前组件行为；Tailwind/React 版本和待迁移范围”。依赖这些输入的写操作不执行。

**Q4：怎样判断完成？** 保留 Dialog 焦点恢复与键盘关闭；registry 源和依赖实际审查；浅/深主题及焦点可见性经验证。

**Q5：怎样定制？** registry、原语、主题、variant、目标组件和迁移顺序；未提供时沿用现有项目值并标明假设。

**Q6：是否自动上传、安装或上线？** 只执行当前请求与已有授权覆盖的动作；没有远程回执不称上传成功，没有运行验证不称上线。额外安装或扩大范围需先说明具体影响。

## 按需参考

- 执行详细映射、API 或模板时读 [扩展流程](references/workflow.md)。
- 遇到失败/异常输入时读 [反模式与 Gotchas](references/anti-patterns.md)。
- 涉及边缘场景、兼容性、定制和授权时读 [深度 FAQ](references/faq-deep.md)。
- 需要完整输入输出及验证场景时读 [本地应用示例](examples/local-validation.md)。
- 本地实现依据为当前技能伴随源码及 [固定上游快照](https://github.com/google-labs-code/stitch-skills/tree/0337446dadde6f8c94210444e2aa9d546126480f)；结构遵循 [Agent Skills 规范](https://agentskills.io/specification)。工具当前行为以实际 schema 为准，未连接时不声称已核验线上行为。
