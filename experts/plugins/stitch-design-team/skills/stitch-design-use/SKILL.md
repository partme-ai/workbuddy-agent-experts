---
name: stitch-design-use
description: Stitch Design 根路由；当用户要用 Stitch 完成从认证、读取、生成、设计系统、资产处理到完整交付的任务时，选择最窄的下游 Skill，不直接扩大远程写入授权。
---

# 使用 Stitch Design

## 快速开始

- “用 Stitch 看一下我现有项目和屏幕。”
- “用 Stitch 生成移动端页面并迭代。”
- “把这个页面完成从生成、对比到验收归档的完整交付。”

面向设计师、产品、前端开发者和交付负责人。该入口只负责判断路径、输入和授权，不以路由成功代替下游执行证据。

## 路由表

| 意图 | 选择 |
| --- | --- |
| 首次使用、缺凭据、认证失败 | `stitch-local-setup` |
| 列项目 | `stitch-mcp-list-projects` |
| 读项目详情 | `stitch-mcp-get-project` |
| 列屏幕 | `stitch-mcp-list-screens` |
| 读单屏详情/资源 | `stitch-mcp-get-screen` |
| 创建、生成、编辑、变体 | `stitch-ui-designer` |
| 创建、更新、列出或应用设计系统 | `stitch-manage-design-system` |
| 本地准备 HTML/图片，不发送远程请求 | `stitch-extract-static-html` 或目标转换 Skill |
| 明确上传已审核 HTML/图片或 DESIGN.md | `stitch-upload-to-stitch` |
| 明确下载单屏 HTML/截图 | `stitch-mcp-get-screen` 获取 URL，再按授权保存到指定目录 |
| 删除远程项目 | `stitch-delete-project` |
| 规格、双图比较、批准、归档的完整交付 | `stitch-delivery-harness` |

## 能力边界说明

### ✅ 擅长处理

- 将读取请求路由到最窄的只读 Skill。
- 将写入请求路由到设计器或设计系统管理器，并保留批准边界。
- 将完整交付请求路由到 Harness，区分生成与验收完成。

### ⚠️ 需要素材

- 用户要完成的 Stitch 目标和当前阶段。
- 可验证的项目/屏幕资源标识或待创建目标。
- 写入、上传、删除所需的明确范围与授权。

### ❌ 不适用场景及交接

- 仅讨论通用 UI 原则 → `stitch-ued-guide`。
- 仅实现已有设计的前端代码 → 对应框架转换 Skill。
- ChatGPT 网页连接器任务 → 使用该环境授权的连接器流程，本地 setup 不适用。

## 工作方式

先执行 `scripts/stitch_setup.py check`；缺失时转 `stitch-local-setup`，不从环境变量是否存在推断整体配置。一次选择一个主路由；读取可直接执行，远程写入沿用用户当前明确授权，删除必须由专用 Skill 再确认。未知写结果先读取对账，不盲目重试。

## FAQ

**Q1：为什么需要根路由？** 让认证、读、写、资产和完整交付使用各自的安全合同。

**Q2：只是看项目会调用写工具吗？** 不会，读取走专用只读 Skill。

**Q3：缺少凭据怎么办？** 转 `stitch-local-setup`，执行配置检查与隐藏输入流程。

**Q4：本地资产任务会自动上传吗？** 不会。本地准备走提取或转换 Skill；只有用户明确上传并给出目标项目时才进入 `stitch-upload-to-stitch`。Markdown 由该 Skill 转到远程 `upload_design_md`。

**Q5：何时用 Harness？** 用户要求从规格到比较、批准和归档的完整可验证交付时。

**Q6：路由完成是否等于任务完成？** 不等于；必须以目标 Skill 的实际回执和验收证据为准。

明确下载本地资产时使用 `stitch_local_download_assets`；若 `list_screens` 未返回屏幕列表，必须把已由 `get_screen`/生成结果验证且属于同一项目的资源名放入 `screenNames`。上传已审核 HTML/图片时使用 `stitch_local_upload_asset`。两者属于 0.6.0 起提供的本地能力；0.7.4 增加可审计的引用资源 best-effort 导出与无候选ID对账，0.7.5 增加 Stitch 原稿验收后的显式美术决策门，0.7.6 删除可自称用户来源的参数并要求用户严格回复规范选项，0.7.7 增加导入可编辑 HTML 来源、OCR 漂移失败和确定性语义规范化 receipt，0.7.8 将布局比较升级为忽略纹理与色彩增强的粗粒度边缘算法，0.7.3 增加缺少凭据时自动打开本地 Token 页面。真实 Provider Canary 证据仍见已发布的 [live-canary-acceptance.md](../../docs/live-canary-acceptance.md)。

## 按需参考

- 复杂组合请求见 [路由工作流](references/workflow.md)。
- 常见误路由见 [反模式](references/anti-patterns.md)。
- 边缘场景见 [深度 FAQ](references/faq-deep.md)。
- 离线路由示例见 [本地验证示例](examples/local-validation.md)。
