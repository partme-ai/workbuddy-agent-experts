---
name: stitch-ui-prompt-architect
description: 润色模糊 UI 需求或将已有 Design Spec/框架契约转为 Stitch 三段提示词时触发；产物仅为可复制文本。实际生成屏幕由 stitch-ui-designer 执行。
license: Apache-2.0
---

> **来源声明**：本技能包含源自 [google-labs-code/stitch-skills](https://github.com/google-labs-code/stitch-skills)
> （Apache License 2.0，完整文本见同目录 `LICENSE.txt`；上游为非 Google 官方支持产品）的内容。
> 本项目对其进行了改编与整合，原内容版权归 Google LLC 及其贡献者所有。

# Stitch 提示词设计

## 快速开始

1. “润色门店预约页的模糊 Stitch 提示；先给本地可审阅结果。”
2. “把 TABLET Spec 和 uView Pro 契约组装为提示；保留已有范围与来源。”
3. “为既有屏幕只增加搜索栏编写精确编辑描述；标出缺少的输入和验证状态。”

面向设计师、前端开发者和维护此流程的团队。设计师提供意图与素材，开发者提供工程/工具，团队在交接中保留来源和验收状态。

## 能力边界说明

### ✅ 擅长处理

- 润色门店预约页的模糊 Stitch 提示。
- 把 TABLET Spec 和 uView Pro 契约组装为提示。
- 为既有屏幕只增加搜索栏编写精确编辑描述。

### ⚠️ 需要素材

- 页面目的、内容与目标设备。
- 可选 Design Spec、DESIGN.md 或框架名。
- 项目系统是否已应用及执行模式。

### ❌ 不适用场景及交接

- 实际生成/编辑屏幕 → stitch-ui-designer。
- 提取视觉语言文档 → stitch-design-md。
- 直接实现前端代码 → 对应组件技能，提供本提示和源资产。

## 工作流程

1. 短/模糊需求走 Path A；已有 Spec/命名框架走 Path B，尊重已批准要求。
2. 明确 platform、purpose 和真实文案；缺项给标注假设的可用提示。
3. 根据可观察的系统状态分流：已应用系统的新屏去掉主题tokens；prompt-only/legacy内联；targeted-edit只写请求的差值。
4. 输出 [Context]、[Layout]、[Components] 三段，布局编号，控件有具体标签和状态。
5. 检查框架contract只包含当前屏幕需要的内容；禁止编造数据/统计，不调用生成工具。

按依赖排序：来源核对 → 本地产物 → 已授权外部操作 → 验证交接。多任务先做当前主路径；缺信息先输出假设草案，再精确列明缺少什么以及用途，不使用“请提供更多背景”的空泛提示。

## 安全与结果验证

不读取无关账号配置，不收集用户密码；凭据只由环境或已授权连接器提供。示例只用演示数据；上传前将客户姓名、电话、订单号替换为演示值，并检查 HTML、截图和文件元数据。禁止将密钥、会话 cookie、base64 全文或签名下载 URL 写入报告/版本库。未经验证的参数、视觉效果、业务数字不得编造；输出注明来源、决策依据、实际执行与尚未验证部分。

- 三段顺序和设备明确。
- 已应用系统提示不重复hex/font/theme/radius。
- 编辑只覆盖请求区域。

可定制：设备、路径A/B、框架、文案、系统状态和目标区域。增值检查：模糊词转组件；双路径三段契约；系统/内联/编辑分流。

## FAQ

**Q1：交付的主要结果是什么？** [Context] 门店预约平板页，只编辑顶栏。 / [Layout] 1. 在头像前放搜索输入。 / [Components] 标签“搜索订单”，占位“输入订单号”，清除动作与焦点态。

**Q2：什么时候应换用其他入口？** 实际生成/编辑屏幕 → stitch-ui-designer；提取视觉语言文档 → stitch-design-md；直接实现前端代码 → 对应组件技能，提供本提示和源资产。

**Q3：缺少输入会怎样？** 先给明确标记的本地假设草案，并列出“需要补充：页面目的、内容与目标设备；可选 Design Spec、DESIGN.md 或框架名；项目系统是否已应用及执行模式”。依赖这些输入的写操作不执行。

**Q4：怎样判断完成？** 三段顺序和设备明确；已应用系统提示不重复hex/font/theme/radius；编辑只覆盖请求区域。

**Q5：怎样定制？** 设备、路径A/B、框架、文案、系统状态和目标区域；未提供时沿用现有项目值并标明假设。

**Q6：是否自动上传、安装或上线？** 只执行当前请求与已有授权覆盖的动作；没有远程回执不称上传成功，没有运行验证不称上线。额外安装或扩大范围需先说明具体影响。

## 按需参考

- 执行详细映射、API 或模板时读 [扩展流程](references/workflow.md)。
- 遇到失败/异常输入时读 [反模式与 Gotchas](references/anti-patterns.md)。
- 涉及边缘场景、兼容性、定制和授权时读 [深度 FAQ](references/faq-deep.md)。
- 需要完整输入输出及验证场景时读 [本地应用示例](examples/local-validation.md)。
- 本地实现依据为当前技能伴随源码及 [固定上游快照](https://github.com/google-labs-code/stitch-skills/tree/0337446dadde6f8c94210444e2aa9d546126480f)；结构遵循 [Agent Skills 规范](https://agentskills.io/specification)。工具当前行为以实际 schema 为准，未连接时不声称已核验线上行为。
