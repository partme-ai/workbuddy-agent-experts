---
name: stitch-ui-designer
description: 编排 Stitch 屏幕的新建、导入、编辑或变体生成；用户明确要求用 Stitch 实际创建或修改设计时触发。只润色提示词用 stitch-ui-prompt-architect，只写设计文档用 stitch-design-md。
license: Apache-2.0
---

# Stitch 设计执行编排

## 快速开始

1. “用 Stitch 生成门店预约平板页；先给本地可审阅结果。”
2. “只修改既有订单页顶部搜索区；保留已有范围与来源。”
3. “按批准数量生成布局变体并核验资产；标出缺少的输入和验证状态。”

面向设计师、前端开发者和维护此流程的团队。设计师提供意图与素材，开发者提供工程/工具，团队在交接中保留来源和验收状态。

## 能力边界说明

### ✅ 擅长处理

- 用 Stitch 生成门店预约平板页。
- 只修改既有订单页顶部搜索区。
- 按批准数量生成布局变体并核验资产。

### ⚠️ 需要素材

- 目标项目及新建/编辑/变体意图。
- 界面需求、设备和已有设计系统。
- 可用工具 schema、目标屏幕及写入范围。

### ❌ 不适用场景及交接

- 只需可复制提示词 → stitch-ui-prompt-architect。
- 只生成 DESIGN.md → stitch-design-md。
- 实现后台接口或发布网站 → 目标开发/部署流程，交付设计与资产。

## 工作流程

1. 检测实际工具；无 MCP 时输出 prompt-only 并明确未生成。
2. 复用项目，按需读取 spec/框架 contract；uviewpro 匹配优先于 uview。
3. 核对已应用 designSystem；新屏的系统 ID 单独传，提示中不重复主题tokens，legacy/prompt-only保留内联token。
4. 用 architect 的三段提示按意图 dispatch generate_screen_from_text/edit_screens/generate_variants；ID保留字符串，参数按当前 schema。
5. 取得 outputComponents、项目及屏幕资产，验证实际图像并保存来源；非幂等写中断先三项读探针，未知结果不重发。

按依赖排序：来源核对 → 本地产物 → 已授权外部操作 → 验证交接。多任务先做当前主路径；缺信息先输出假设草案，再精确列明缺少什么以及用途，不使用“请提供更多背景”的空泛提示。

## 安全与结果验证

不读取无关账号配置，不收集用户密码；凭据只由环境或已授权连接器提供。示例只用演示数据；上传前将客户姓名、电话、订单号替换为演示值，并检查 HTML、截图和文件元数据。禁止将密钥、会话 cookie、base64 全文或签名下载 URL 写入报告/版本库。未经验证的参数、视觉效果、业务数字不得编造；输出注明来源、决策依据、实际执行与尚未验证部分。

- edit/variant 的 selectedScreenIds 来自实际查询。
- MOBILE/DESKTOP/TABLET 与请求一致。
- get_project/list_screens/get_screen 对账，无候选记录原因。

### 设备保真必须按实测值判定

判定依据是 `get_screen` 的**顶层** `deviceType`、`width`、`height`；`screenInstance` 不保证带这些字段。生成后先读这三个值再判定，不能只看"调用成功"。

- 提供方不保证遵守请求的设备。2026-09-14 实测：三条写路径（`generate_screen_from_text`、`edit_screens`、`generate_variants`）请求 `TABLET` 全部返回 `DESKTOP 2560×2048`；另有一次 `MOBILE` 请求同样回退为 `DESKTOP`。命中回退时**停止**并如实报告，不要改试另外两条路径——它们会以同样方式回退，只会多产生无用产物。
- 提供方尺寸是设备像素：`390×884` 的视口返回 `780×1768`（2×）。这是缩放而不是误差，不要追网页画布上显示的 1px 差值。
- 判定规则：设备与请求一致（请求 `AGNOSTIC` 时跳过该条），且宽高是画布的整数倍、横纵倍数相同。Harness 的 `validate_screen_device` 据此**失败关闭**；未通过就不得标记完成，也不得作为该设备的交付物上报。

可定制：设备、框架contract、生成/编辑/变体模式、数量和资产目录。增值检查：意图路由；系统token分流；中断写对账。

## FAQ

**Q1：交付的主要结果是什么？** 离线编辑请求：仅在 TABLET 订单页头像前加“搜索订单”输入；保留其余布局；准备 edit_screens 参数，实际远程调用0。

**Q2：什么时候应换用其他入口？** 只需可复制提示词 → stitch-ui-prompt-architect；只生成 DESIGN.md → stitch-design-md；实现后台接口或发布网站 → 目标开发/部署流程，交付设计与资产。

**Q3：缺少输入会怎样？** 先给明确标记的本地假设草案，并列出“需要补充：目标项目及新建/编辑/变体意图；界面需求、设备和已有设计系统；可用工具 schema、目标屏幕及写入范围”。依赖这些输入的写操作不执行。

**Q4：怎样判断完成？** edit/variant 的 selectedScreenIds 来自实际查询；MOBILE/DESKTOP/TABLET 与请求一致；get_project/list_screens/get_screen 对账，无候选记录原因。

**Q5：怎样定制？** 设备、框架contract、生成/编辑/变体模式、数量和资产目录；未提供时沿用现有项目值并标明假设。

**Q6：是否自动上传、安装或上线？** 只执行当前请求与已有授权覆盖的动作；没有远程回执不称上传成功，没有运行验证不称上线。额外安装或扩大范围需先说明具体影响。

## 按需参考

- 执行详细映射、API 或模板时读 [扩展流程](references/workflow.md)。
- 遇到失败/异常输入时读 [反模式与 Gotchas](references/anti-patterns.md)。
- 涉及边缘场景、兼容性、定制和授权时读 [深度 FAQ](references/faq-deep.md)。
- 需要完整输入输出及验证场景时读 [本地应用示例](examples/local-validation.md)。
- 本地实现依据为当前技能伴随源码及 [固定上游快照](https://github.com/google-labs-code/stitch-skills/tree/0337446dadde6f8c94210444e2aa9d546126480f)；结构遵循 [Agent Skills 规范](https://agentskills.io/specification)。工具当前行为以实际 schema 为准，未连接时不声称已核验线上行为。
