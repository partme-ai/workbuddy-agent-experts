# Stitch 的 shadcn/ui 迁移：反模式与 Gotchas

这些检查处理实际流程偏差；触发后按下列原因和修正采取行动。

| 错误做法 | 后果与正确处理 |
| --- | --- |
| 强行对 Tailwind4 执行 init -p | 沿用现有 v4 工具链。 |
| 覆盖已有 customized ui 源码 | 逐项 diff 后迁移。 |
| 移除 aria/keyboard handler | 保留 primitives 的交互语义。 |
| 诊断exit0即通过 | 读取所有诊断并运行工程正式检查。 |
| 把第三方 registry 当可信命令 | 先检查源码/依赖再应用。 |

## 失败输出契约

先交付本地可完成部分，再指出具体缺项。例如：“已整理把预约表单迁为 shadcn Input/Button的本地方案；需要补充：目标工程与 components.json（确定来源）、Stitch 资产及当前组件行为（决定映射）、Tailwind/React 版本和待迁移范围（确定可执行边界）。”

远程写入超时不等于失败：停止依赖该回执的操作，读取 get_project、list_screens、get_screen；没有候选则记录 get_screen 未执行及原因。不得重发同一未知结果的写请求。删除项目前需要明确确认；其他步骤沿用已有授权。

## 禁忌

- 不把上游快照的可选依赖当本机已安装的工具。
- 不把生成文件存在当作渲染、交互或远程验收证据。
- 不将示例标识/演示文案当成真实客户资产。
