---
name: stitch-ui-design-spec-uviewpro
description: uView Pro design spec for Stitch. Outputs hard-constraints prefix or selector JSON and assembled prompt.
---


# uView Pro Design Spec (uView Pro / Vue 3)

**Constraint**: Only use this skill when the user explicitly mentions "Stitch".

## Purpose

This skill makes the uView Pro design spec executable in two modes:

1) **Prefix mode**: output a paste-ready **Hard constraints prefix** for Stitch `[Context]`.
2) **Selector mode**: output `CONTRACT_SELECTION_JSON_V1` and then an assembled Stitch prompt that injects only the required component/state snippets.

## Trigger Keywords

Prefer this skill when the user request includes any of:

- `uview-pro`, `uviewpro`, `uview pro`

Chinese trigger keywords (only for triggering):

- `uview pro`
- `uview 3.0`

## Source of Truth

- `references/contract.md`
- `references/examples.md`
- `references/official.md`

## Output (STRICT)

Decide the mode by the user intent:

- If the user asks for **beautify/polish/refine an existing screen**, or asks for **selector / JSON / contracts.include / states.include** → use **Selector mode**.
- Otherwise → use **Prefix mode**.

### Prefix mode

Return exactly one code block:

```text
[Hard constraints prefix]
- Framework: uView Pro (uni-app / Vue 3).
- Design Tokens:
  - Colors: Primary=#3c9cff, Success=#5ac725, Warning=#f9ae3d, Danger=#f56c6c, Info=#909399.
  - Typography: Unit rpx. Main Title 32rpx. Content 28rpx.
  - Radius: Base 8rpx, Card 16rpx, Circle 9999px.
- Component Contracts (Prefix: u-; uView Pro uses same tag prefix as uView 2, package uview-pro):
  - Buttons: <u-button type="primary" shape="circle">.
  - Layout: <u-row>, <u-col span="...">, <u-gap>.
  - Forms: <u-form :model="form">, <u-form-item>, <u-input border="none">, <u-code>.
  - Navbar: <u-navbar title="..." :autoBack="true">.
  - List: <u-swipe-action>, <u-index-list>, <u-waterfall>, <u-list>, <u-grid>.
  - Icons: <u-icon name="photo">.
- JS Utilities:
  - Use uni.$u.toast(), uni.$u.route(), uni.$u.http.post().
  - Use <script setup lang="ts">.
```

### Selector mode

Return exactly two code blocks, in this order, with no extra prose:

1) Contract selection JSON:

```json
{
  "version": "CONTRACT_SELECTION_JSON_V1",
  "designSystem": "uview-pro",
  "mode": "selector",
  "contracts": { "include": [] },
  "states": { "include": [] }
}
```

2) Final Stitch prompt:

```text
[Context]
(Paste Hard Constraints Prefix here)
(Add "Layout Invariants" from contract.md if beautifying)

[Layout]
(Describe the macro layout structure, e.g., "Mobile Column Layout with Navbar")

[Components]
(Inject component snippets matching the JSON selection above)
```

## References

- [Contract](references/contract.md)
- [Examples](references/examples.md)
- [Official Docs](references/official.md)

## 国内适配

- 支持中文文档和中文注释
- 示例代码兼容国内开发环境
- 提供中文 FAQ 和常见问题解答

## 能力边界

### ✅ 适用场景
- 当你需要使用此技能对应的技术栈时
- 当项目需要遵循最佳实践时
- 当需要快速上手或深入理解核心概念时

### ⚠️ 需要注意
- 复杂业务逻辑需要结合具体场景调整
- 性能优化需要根据实际数据量评估

### ❌ 不适用场景
- 不相关的技术栈或框架
- 需要完全自定义的特殊场景

## 使用流程

### Step 1: 环境准备
确保开发环境已安装必要的依赖和工具。

### Step 2: 配置初始化
根据项目需求进行基础配置。

### Step 3: 核心功能使用
按照示例代码实现核心功能。

### Step 4: 测试验证
运行测试确保功能正常。

### Step 5: 部署上线
完成开发后进行部署和监控。
