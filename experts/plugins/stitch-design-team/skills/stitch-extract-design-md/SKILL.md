---
name: stitch-extract-design-md
description: 从前端源码提取可追踪的 DESIGN.md；在应用无法构建、需要审计 React/Vue/Svelte/Angular/CSS 视觉 token 或向 Stitch 迁移设计语言时使用。只做截图语义总结用 stitch-design-md。
license: Apache-2.0
---

# 从源码提取设计系统

## 快速开始

1. “从企业微信预约 Web 页的 CSS 提取主色与间距；先给本地可审阅结果。”
2. “构建失败时读取 Angular 模板和主题；保留已有范围与来源。”
3. “比较门店后台深浅主题差异并记录来源；标出缺少的输入和验证状态。”

面向设计师、前端开发者和维护此流程的团队。设计师提供意图与素材，开发者提供工程/工具，团队在交接中保留来源和验收状态。

## 能力边界说明

### ✅ 擅长处理

- 从企业微信预约 Web 页的 CSS 提取主色与间距。
- 构建失败时读取 Angular 模板和主题。
- 比较门店后台深浅主题差异并记录来源。

### ⚠️ 需要素材

- 前端源码根目录。
- 主题、CSS 或组件文件。
- 目标主题及是否需要上传兼容 YAML。

### ❌ 不适用场景及交接

- 只看截图提炼语义 → stitch-design-md。
- 创建全新视觉风格 → stitch-taste-design。
- 远程创建或应用系统 → stitch-manage-design-system，交付 DESIGN.md 作为输入。

## 工作流程

1. 读取 package.json 和目录，确定框架与 CSS 工具链。
2. 按框架读取现有 references 中的提取指南；先主题后组件，记录具体文件与选择器。
3. 提取颜色角色、字体、间距、圆角、组件状态和响应式条件，区分事实和建议。
4. 写 .stitch/DESIGN.md：YAML name/colors 加六节语义文档；未知 Project ID 省略，使用 Source。
5. 核对每个 token 的来源、覆盖关系和模式；未渲染时将氛围标记为推断。

按依赖排序：来源核对 → 本地产物 → 已授权外部操作 → 验证交接。多任务先做当前主路径；缺信息先输出假设草案，再精确列明缺少什么以及用途，不使用“请提供更多背景”的空泛提示。

## 安全与结果验证

不读取无关账号配置，不收集用户密码；凭据只由环境或已授权连接器提供。示例只用演示数据；上传前将客户姓名、电话、订单号替换为演示值，并检查 HTML、截图和文件元数据。禁止将密钥、会话 cookie、base64 全文或签名下载 URL 写入报告/版本库。未经验证的参数、视觉效果、业务数字不得编造；输出注明来源、决策依据、实际执行与尚未验证部分。

- 颜色值可回溯到源码且近似色未被静默合并。
- name/colors YAML 可解析。
- 断点和交互状态区分已观察与建议。

可定制：主题模式、组件范围、语言和路径；例如只提取深色按钮/表单。增值检查：token 溯源表；近似色差异清单；框架按需路由。

## FAQ

**Q1：交付的主要结果是什么？** name: 门店预约；colors.primary: '#2563eb'（演示输入）；Source: src/theme.css 的 --brand-primary；氛围为源码推断，尚未渲染。

**Q2：什么时候应换用其他入口？** 只看截图提炼语义 → stitch-design-md；创建全新视觉风格 → stitch-taste-design；远程创建或应用系统 → stitch-manage-design-system，交付 DESIGN.md 作为输入。

**Q3：缺少输入会怎样？** 先给明确标记的本地假设草案，并列出“需要补充：前端源码根目录；主题、CSS 或组件文件；目标主题及是否需要上传兼容 YAML”。依赖这些输入的写操作不执行。

**Q4：怎样判断完成？** 颜色值可回溯到源码且近似色未被静默合并；name/colors YAML 可解析；断点和交互状态区分已观察与建议。

**Q5：怎样定制？** 主题模式、组件范围、语言和路径；例如只提取深色按钮/表单；未提供时沿用现有项目值并标明假设。

**Q6：是否自动上传、安装或上线？** 只执行当前请求与已有授权覆盖的动作；没有远程回执不称上传成功，没有运行验证不称上线。额外安装或扩大范围需先说明具体影响。

## 按需参考

- 执行详细映射、API 或模板时读 [扩展流程](references/workflow.md)。
- 遇到失败/异常输入时读 [反模式与 Gotchas](references/anti-patterns.md)。
- 涉及边缘场景、兼容性、定制和授权时读 [深度 FAQ](references/faq-deep.md)。
- 需要完整输入输出及验证场景时读 [本地应用示例](examples/local-validation.md)。
- 本地实现依据为当前技能伴随源码及 [固定上游快照](https://github.com/google-labs-code/stitch-skills/tree/0337446dadde6f8c94210444e2aa9d546126480f)；结构遵循 [Agent Skills 规范](https://agentskills.io/specification)。工具当前行为以实际 schema 为准，未连接时不声称已核验线上行为。
