# 管理 Stitch 项目设计系统：反模式与 Gotchas

这些检查处理实际流程偏差；触发后按下列原因和修正采取行动。

| 错误做法 | 后果与正确处理 |
| --- | --- |
| 把 screenId 直接当实例 id | 从 get_project.screenInstances 取 id/sourceScreen。 |
| 提交整个画布对象 | 只传 id 与 sourceScreen。 |
| 把设计系统卡片当页面 | 过滤 DESIGN_SYSTEM_INSTANCE。 |
| 上传成功就称系统应用完成 | 分别验证 create 和 apply。 |
| 本地 DESIGN.md 存在就省略全部 tokens | 只有已验证应用的远程系统才走独立系统通道。 |

## 失败输出契约

先交付本地可完成部分，再指出具体缺项。例如：“已整理把门店后台 DESIGN.md 建为项目系统的本地方案；需要补充：真实 projectId 和可用 MCP schema（确定来源）、可共享的 DESIGN.md 或现有 assetId（决定映射）、待应用屏幕的实例 id/sourceScreen 与修改范围（确定可执行边界）。”

远程写入超时不等于失败：停止依赖该回执的操作，读取 get_project、list_screens、get_screen；没有候选则记录 get_screen 未执行及原因。不得重发同一未知结果的写请求。删除项目前需要明确确认；其他步骤沿用已有授权。

## 禁忌

- 不把上游快照的可选依赖当本机已安装的工具。
- 不把生成文件存在当作渲染、交互或远程验收证据。
- 不将示例标识/演示文案当成真实客户资产。
