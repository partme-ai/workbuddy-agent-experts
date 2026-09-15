---
name: stitch-react-native
description: 将 Stitch 屏幕转为 React Native 或同步现有原生组件；目标是 iOS/Android 的 View、Text、StyleSheet 和原生导航时触发。React DOM 或 Vite Web 页面使用 stitch-react-components。
license: Apache-2.0
---

# Stitch 转 React Native

## 快速开始

1. “将门店预约稿转 iOS/Android 表单；先给本地可审阅结果。”
2. “把运营列表改为原生 FlatList；保留已有范围与来源。”
3. “同步当前 Stitch 主题到既有 RN 工程；标出缺少的输入和验证状态。”

面向设计师、前端开发者和维护此流程的团队。设计师提供意图与素材，开发者提供工程/工具，团队在交接中保留来源和验收状态。

## 能力边界说明

### ✅ 擅长处理

- 将门店预约稿转 iOS/Android 表单。
- 把运营列表改为原生 FlatList。
- 同步当前 Stitch 主题到既有 RN 工程。

### ⚠️ 需要素材

- 目标 RN 工程与实际依赖版本。
- 所选 Stitch 屏幕或获准复用的 HTML/截图。
- 平台、导航及 token 约束。

### ❌ 不适用场景及交接

- React/Vite 浏览器 UI → stitch-react-components。
- Jetpack Compose 或 SwiftUI 实现 → 对应平台开发流程，交付设计映射。
- 真实支付、登录或推送集成 → 项目业务接口流程，保留 UI 状态契约。

## 工作流程

1. 按用户选定屏幕检索 HTML/截图与元数据，缓存来源一致且允许复用时直接使用。
2. 提取当前项目 token 到 src/theme.ts；保留来源与同步时间。
3. 将 div→View、文本→Text、button→Pressable、长列表→FlatList；用 StyleSheet 与当前 RN 版本能力映射。
4. 按工程惯例拆组件/数据/hooks，连接既有原生导航，保留 readonly Props、safe-area 与无障碍标签。
5. 使用脚本做有限 AST 检查，再执行现有类型检查；模拟器验收另行记录，不把脚本通过当原生运行成功。

按依赖排序：来源核对 → 本地产物 → 已授权外部操作 → 验证交接。多任务先做当前主路径；缺信息先输出假设草案，再精确列明缺少什么以及用途，不使用“请提供更多背景”的空泛提示。

## 安全与结果验证

不读取无关账号配置，不收集用户密码；凭据只由环境或已授权连接器提供。示例只用演示数据；上传前将客户姓名、电话、订单号替换为演示值，并检查 HTML、截图和文件元数据。禁止将密钥、会话 cookie、base64 全文或签名下载 URL 写入报告/版本库。未经验证的参数、视觉效果、业务数字不得编造；输出注明来源、决策依据、实际执行与尚未验证部分。

- 无 DOM 元素/浏览器事件且所有文本位于 Text。
- theme token 来自当前源，Image 有尺寸。
- 检查 iOS/Android 的 safe-area、导航和键盘状态。

可定制：目标 iOS/Android、工程路径、既有导航、主题和刷新范围。增值检查：Web→Native 映射；长列表选择；平台差异与可访问性检查。

## FAQ

**Q1：交付的主要结果是什么？** 输入 <button>确认预约</button> → <Pressable accessibilityRole="button" accessibilityLabel="确认预约"><Text>确认预约</Text></Pressable>；事件由目标 onPress 契约提供。

**Q2：什么时候应换用其他入口？** React/Vite 浏览器 UI → stitch-react-components；Jetpack Compose 或 SwiftUI 实现 → 对应平台开发流程，交付设计映射；真实支付、登录或推送集成 → 项目业务接口流程，保留 UI 状态契约。

**Q3：缺少输入会怎样？** 先给明确标记的本地假设草案，并列出“需要补充：目标 RN 工程与实际依赖版本；所选 Stitch 屏幕或获准复用的 HTML/截图；平台、导航及 token 约束”。依赖这些输入的写操作不执行。

**Q4：怎样判断完成？** 无 DOM 元素/浏览器事件且所有文本位于 Text；theme token 来自当前源，Image 有尺寸；检查 iOS/Android 的 safe-area、导航和键盘状态。

**Q5：怎样定制？** 目标 iOS/Android、工程路径、既有导航、主题和刷新范围；未提供时沿用现有项目值并标明假设。

**Q6：是否自动上传、安装或上线？** 只执行当前请求与已有授权覆盖的动作；没有远程回执不称上传成功，没有运行验证不称上线。额外安装或扩大范围需先说明具体影响。

## 按需参考

- 执行详细映射、API 或模板时读 [扩展流程](references/workflow.md)。
- 遇到失败/异常输入时读 [反模式与 Gotchas](references/anti-patterns.md)。
- 涉及边缘场景、兼容性、定制和授权时读 [深度 FAQ](references/faq-deep.md)。
- 需要完整输入输出及验证场景时读 [本地应用示例](examples/local-validation.md)。
- 本地实现依据为当前技能伴随源码及 [固定上游快照](https://github.com/google-labs-code/stitch-skills/tree/0337446dadde6f8c94210444e2aa9d546126480f)；结构遵循 [Agent Skills 规范](https://agentskills.io/specification)。工具当前行为以实际 schema 为准，未连接时不声称已核验线上行为。
