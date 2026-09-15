# {{PRODUCT_NAME}}-{{MODULE_NAME}}-Stitch设计提示词（{{VERSION}}）

> **模板说明**：先填写通用输入，再参考附录中的 ExampleConsole 完整示例。保留示例深度，但必须依据目标模块的数据、状态和设计系统重写提示词。

---

## 1. 生成输入

| 输入 | 填写要求 |
|---|---|
| 产品与版本 | `{{PRODUCT_NAME}}`、`{{VERSION}}` |
| 模块与页面 | `{{MODULE_NAME}}`、页面清单、入口和返回路径 |
| 用户与任务 | 目标角色、核心任务、使用频率、成功标准 |
| 数据与状态 | 字段、筛选、排序、分页、空态、加载、错误、权限、离线状态 |
| 设计约束 | 设计令牌、平台、断点、组件库、无障碍、国际化 |
| 证据 | PRD、UI 规范、接口契约、现有截图或已确认决策 |

## 2. 通用设计生成提示词

```text
Design the "{{MODULE_NAME}}" experience for {{PRODUCT_NAME}} {{VERSION}}.

Goal:
- [Describe the user outcome and measurable success condition.]

Users and tasks:
- [Role]: [primary task]
- [Role]: [secondary task]

Pages and navigation:
- [Page name]: [purpose, entry, exit]

Data and states:
- Fields: [verified fields]
- Filters and actions: [verified controls]
- Cover loading, empty, error, permission-denied, partial-data, and destructive-action confirmation states.

Design system:
- Platform and breakpoints: [web/mobile/desktop and sizes]
- Tokens and components: [source document]
- Accessibility: keyboard navigation, focus order, contrast, labels, and reduced motion.

Output:
- Page hierarchy, component anatomy, state variants, interaction notes, and implementation-ready annotations.
- Mark unsupported assumptions as 待确认; do not invent APIs, metrics, or permissions.
```

## 3. 改写检查

- [ ] 页面名称、业务名词和数据字段来自目标项目。
- [ ] 完整覆盖正常、加载、空、错误、权限和危险操作状态。
- [ ] 不保留附录示例中的实例数量、引擎名称、颜色或页面结构，除非项目证据支持。
- [ ] 与模块 PRD、版本 UI 规则及视觉 DNA 一致。

---

## 附录 A：完整示例 — ExampleConsole 实例中心

> **示例档案**：ExampleConsole。以下内容保留完整案例，仅用于展示提示词颗粒度和页面状态表达。

### A.1 原文标题：{{PRODUCT_NAME}} — 实例中心 Stitch 设计提示词

> **文档说明**：为 [{{PRODUCT_NAME}}-V1界面重构与研发任务清单](../../31、{{PRODUCT_NAME}}-V1%E7%95%8C%E9%9D%A2%E9%87%8D%E6%9E%84%E4%B8%8E%E7%A0%94%E5%8F%91%E4%BB%BB%E5%8A%A1%E6%B8%85%E5%8D%95.md) 中的“实例中心”模块提供 Stitch 设计提示词。该模块负责管理所有已纳管的智能体引擎实例（OpenClaw / ZeroClaw / ExampleEngine）。

---

### A.2 文档信息

| 属性 | 内容 |
| :--- | :--- |
| 文档版本 | V1.0.0 |
| 创建日期 | 2026-03-24 |
| 设计规范 | [{{PRODUCT_NAME}}-视觉与交互DNA规范](../../9、{{PRODUCT_NAME}}-视觉与交互DNA规范.md) |

---

### A.3 设计系统摘要

- **实例状态颜色**：
  - 在线 (Online)：绿色 `#07C160`
  - 异常 (Degraded)：橙色 `#FFAA00`
  - 离线 (Offline)：红色 `#DC2626`
  - 维护中 (Upgrading)：蓝色 `#2563EB`
- **布局**：概览卡片（Summary Cards）+ 实例列表（Table）+ 实例详情（Details）
- **字体**：微软雅黑 (Microsoft YaHei)

---

### A.4 实例中心 — Stitch 提示词

#### A.4.1 提示词：实例列表页面

```
REQUIRED: Font Microsoft YaHei. All UI copy in Chinese.

Design an "实例中心" (Instance Center) page for {{PRODUCT_NAME}}.

Header:
- Title: "实例管理" (20px bold)
- Stats Row: [总实例: 12] [● 在线: 10] [● 异常: 1] [● 离线: 1]
- Buttons: [+ 部署新实例] red button #E63946, [刷新] icon.

Filter Bar:
- Engine Filter: "全部引擎", "OpenClaw", "ZeroClaw", "ExampleEngine".
- Group Filter: "全部生产", "测试环境", "边缘节点".
- Search: "搜索实例名称/ID..."

Data Table:
1. 实例名称 (Icon per engine + Name + ID)
2. 引擎类型 (Badge: OpenClaw / ZeroClaw / ExampleEngine)
3. 所在节点 (Host name link)
4. 健康状态 (Pill: ● 在线 Green / ● 离线 Red)
5. 运行时间 (e.g. 12d 4h)
6. 操作: [控制台] [日志] [设置] [重启/停止] (Dropdown).

Style: High density data view, clear engine distinction, hover effects on rows.
```

#### A.4.2 提示词：实例详情页面

```
REQUIRED: Font Microsoft YaHei. All UI copy in Chinese.

Design the "实例详情" (Instance Detail) page for {{PRODUCT_NAME}}.

Header:
- Breadcrumb: "实例管理 > claw-instance-01"
- Header Actions: [重启] [停止] [删除] red text.

Layout:
- Left Column (70%):
  - Card 1: 运行时概览 (CPU/RAM usage charts, Process ID, Port).
  - Card 2: 最新配置 (Read-only YAML/JSON view).
  - Card 3: 关联扩展 (List of skills/tools active for this instance).
- Right Column (30%):
  - Health History: Small timeline of status changes.
  - Recent Events: Audit logs specific to this instance.
  - Quick Info: Node location, IP address, version.

Style: Dashboard-in-dashboard, use small charts for real-time metrics, clear section titles.
```

---

**文档版本**：V1.0.0  
**最后更新**：2026-03-24  
**文档状态**：✅ 已完成

> **完整示例结束**
