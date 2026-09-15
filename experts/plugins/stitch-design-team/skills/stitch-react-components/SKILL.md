---
name: stitch-react-components
description: 将 Stitch HTML/屏幕转换或同步为 React/Vite 组件；需要 token、组件 Props 和导航一致性校验时触发。shadcn 原语迁移、数据看板、React Native 或视频使用各自规范入口。
license: Apache-2.0
---

# Stitch 转 React 组件

## 快速开始

1. “把门店预约 Stitch 页转 React 组件；先给本地可审阅结果。”
2. “修复桌面品牌标识没有返回首页的问题；保留已有范围与来源。”
3. “将新的设计 token 同步到已有 React 页面；标出缺少的输入和验证状态。”

面向设计师、前端开发者和维护此流程的团队。设计师提供意图与素材，开发者提供工程/工具，团队在交接中保留来源和验收状态。

## 能力边界说明

### ✅ 擅长处理

- 把门店预约 Stitch 页转 React 组件。
- 修复桌面品牌标识没有返回首页的问题。
- 将新的设计 token 同步到已有 React 页面。

### ⚠️ 需要素材

- 目标 React 工程与现有工具链。
- 指定 Stitch 屏幕或有来源的缓存资产。
- 路由表、主题和组件行为契约。

### ❌ 不适用场景及交接

- React Native 原生界面 → stitch-react-native。
- shadcn 原语迁移 → stitch-shadcn-ui。
- Remotion 走查视频 → stitch-remotion，交付屏幕资产清单。

## 工作流程

1. 检索所需屏幕 HTML/截图，保留 ID 字符串与来源时间；缓存按授权复用或刷新。
2. 从当前 HTML 和 DESIGN.md 提取 token 到目标工程，避免覆盖安装 Skill 的示例资源。
3. 拆组件、数据与 hooks，使用 readonly Props；保持目标项目约定。
4. 接入既有路由；品牌 logo 和桌面导航可返回首页，移动底栏隐藏时桌面仍有入口。
5. 执行脚本 AST 检查、项目类型/构建检查与比例合适的视图验证，分开报告各层证据。

按依赖排序：来源核对 → 本地产物 → 已授权外部操作 → 验证交接。多任务先做当前主路径；缺信息先输出假设草案，再精确列明缺少什么以及用途，不使用“请提供更多背景”的空泛提示。

## 安全与结果验证

不读取无关账号配置，不收集用户密码；凭据只由环境或已授权连接器提供。示例只用演示数据；上传前将客户姓名、电话、订单号替换为演示值，并检查 HTML、截图和文件元数据。禁止将密钥、会话 cookie、base64 全文或签名下载 URL 写入报告/版本库。未经验证的参数、视觉效果、业务数字不得编造；输出注明来源、决策依据、实际执行与尚未验证部分。

- AST 仅证明解析、Props 和字面 className hex 检查。
- 所有主题角色来源于当前设计。
- 首页链接和各路由都有可验证目标。

可定制：页面范围、目标目录、路由器、主题模式、刷新策略。增值检查：同步来源；桌面/移动导航核对；AST 能力边界。

## FAQ

**Q1：交付的主要结果是什么？** 输入桌面顶栏“门店预约”与路由 / → 使用既有路由 Link to="/"；截图与 HTML 来源记录在 .stitch；AST 通过不替代浏览器点击测试。

**Q2：什么时候应换用其他入口？** React Native 原生界面 → stitch-react-native；shadcn 原语迁移 → stitch-shadcn-ui；Remotion 走查视频 → stitch-remotion，交付屏幕资产清单。

**Q3：缺少输入会怎样？** 先给明确标记的本地假设草案，并列出“需要补充：目标 React 工程与现有工具链；指定 Stitch 屏幕或有来源的缓存资产；路由表、主题和组件行为契约”。依赖这些输入的写操作不执行。

**Q4：怎样判断完成？** AST 仅证明解析、Props 和字面 className hex 检查；所有主题角色来源于当前设计；首页链接和各路由都有可验证目标。

**Q5：怎样定制？** 页面范围、目标目录、路由器、主题模式、刷新策略；未提供时沿用现有项目值并标明假设。

**Q6：是否自动上传、安装或上线？** 只执行当前请求与已有授权覆盖的动作；没有远程回执不称上传成功，没有运行验证不称上线。额外安装或扩大范围需先说明具体影响。

## 按需参考

- 执行详细映射、API 或模板时读 [扩展流程](references/workflow.md)。
- 遇到失败/异常输入时读 [反模式与 Gotchas](references/anti-patterns.md)。
- 涉及边缘场景、兼容性、定制和授权时读 [深度 FAQ](references/faq-deep.md)。
- 需要完整输入输出及验证场景时读 [本地应用示例](examples/local-validation.md)。
- 本地实现依据为当前技能伴随源码及 [固定上游快照](https://github.com/google-labs-code/stitch-skills/tree/0337446dadde6f8c94210444e2aa9d546126480f)；结构遵循 [Agent Skills 规范](https://agentskills.io/specification)。工具当前行为以实际 schema 为准，未连接时不声称已核验线上行为。
