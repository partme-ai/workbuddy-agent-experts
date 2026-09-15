# Stitch 语义设计系统文档：本地应用验证

使用以下完整演示源作为可复制输入。只读取源码、编写文档，不需要真实项目 ID 或远程写入。

## 快速开始：输入 HTML 与样式

输入：“把这份门店预约 HTML/CSS 整理为六节 DESIGN.md。只记录可观察值，未渲染部分标明推断。”

演示源逻辑路径：demo/appointments.html。

```html
<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>门店预约</title>
<style>
:root { --primary:#2563eb; --canvas:#ffffff; --text:#111827; --surface:#f3f4f6; }
body { margin:0; color:var(--text); background:var(--canvas); font:400 16px/1.5 system-ui,"PingFang SC",sans-serif; }
main { max-width:960px; margin:auto; padding:24px; }
h1 { font-size:24px; font-weight:700; }
header { display:flex; align-items:center; justify-content:space-between; gap:16px; }
button { border:0; border-radius:8px; padding:12px 16px; color:var(--canvas); background:var(--primary); font:inherit; }
article { padding:16px; border-radius:12px; background:var(--surface); }
@media (max-width:600px) { main { padding:16px; } header { flex-direction:column; align-items:stretch; } }
</style>
</head>
<body><main><header><h1>我的预约</h1><button>新建预约</button></header><article>暂无预约</article></main></body>
</html>
```

## 典型场景：完整预期 DESIGN.md

下列代码块就是预期文档，不是生成文档的步骤说明。这里的 Source 指向上方演示输入的逻辑文件名；执行真实项目任务时使用真实存在的路径。

```markdown
# Design System: 门店预约

**Source:** demo/appointments.html（本示例输入的 HTML 与内联 CSS）
**Evidence:** 已读取演示源码，未执行浏览器渲染；没有关联 Stitch 项目。

## 1. Visual Theme & Atmosphere

浅色画布和单一行动色构成清晰的预约列表界面。24px 页面内边距、紧凑顶栏与一个空态容器来自源码；“简洁、易扫读”的氛围是源码推断，尚未视觉确认。

## 2. Color Palette & Roles

- 画布白 (#ffffff)：body 背景及主按钮文字，来源 --canvas。
- 行动蓝 (#2563eb)：主按钮背景，来源 --primary。
- 正文深灰 (#111827)：body 内容文字，来源 --text。
- 容器浅灰 (#f3f4f6)：预约空态容器背景，来源 --surface。

## 3. Typography Rules

正文使用 system-ui、PingFang SC、sans-serif 的字体序列，400 字重、16px 字号、1.5 行高，来自 body。标题为24px、700字重，来自 h1。按钮继承正文排版；未声明额外字距和自定义字体资产。

## 4. Component Stylings

主按钮标签“新建预约”，行动蓝底、画布白字，8px 圆角，纵向12px/横向16px内边距，无边框。
空态容器显示“暂无预约”，容器浅灰背景、12px圆角、16px内边距。
源码没有自定义阴影、hover、focus 或错误态；若新增这些状态，应作为后续建议，不能称为已观察的设计。

## 5. Layout Principles

主内容最大宽度960px，水平居中，通常内边距24px。顶栏采用横向弹性布局、两端分布和16px间隔。
当视口不大于600px时，内容内边距改为16px，顶栏纵向排列并拉伸子项。源码没有侧边栏、底部导航或多列表格。

## 6. Design System Notes for Stitch Generation

复用此浅色预约列表结构：顶部“我的预约”与“新建预约”，主区为预约内容或“暂无预约”空态。
在内联 token 模式使用画布白 (#ffffff)、行动蓝 (#2563eb)、正文深灰 (#111827)、容器浅灰 (#f3f4f6)，保留上述圆角和响应式规则。
若未来核验项目级系统已应用，则把视觉 token 交给系统通道，生成提示只写内容、布局和交互。任何未观察的输入框、状态、统计数据均另标建议，不新增虚构业务指标。
```

验证：六节均有实际内容；所有色值和几何值能映射到输入选择器；没有虚构 Project ID、已渲染结论或业务数据。

## 高级场景：文档是否能指导下一屏

输入：“只依据上面的 DESIGN.md，说明预约详情页可复用什么，不生成页面。”

预期回答：“可复用四个颜色角色、system-ui/PingFang SC 排版、960px主区和600px响应规则；详情字段与错误/焦点状态尚未在源中定义，需要作为新增需求或建议。未生成屏幕。”

验证：可以恢复已有 palette/layout，不能把未观察的详情字段冒充来源事实。

## 异常处理

输入：“只知道页面名‘门店预约’，没有 HTML 或截图。”

本地假设草案：“这是拟议文档：页面目的暂按顾客查看预约理解；已观察 token 为0，颜色/排版/几何待来源确认。需要补充实际 HTML/CSS 或截图，以填充色值角色和布局证据。不会覆盖既有 DESIGN.md，也不会声称语义 lint 已通过。”

这份部分草案不属于完整六节产物，明确保留未完成状态；不能用它给出来源已验证的结论。

## 避免误触发

输入：“深入读取 Vue SFC、SCSS 和主题配置，找出 token 的覆盖关系。”

输出：“使用 stitch-extract-design-md，交接源码目录与目标主题；本入口负责提炼后的语义文档和核对，不替代框架专门提取。”
