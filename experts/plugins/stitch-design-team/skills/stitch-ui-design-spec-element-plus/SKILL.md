---
name: stitch-ui-design-spec-element-plus
description: Element Plus design spec for Stitch. Outputs hard-constraints prefix or selector JSON and assembled prompt.
---


# Element Plus Design Spec (Element Plus / Vue 3)

**Constraint**: Only use this skill when the user explicitly mentions "Stitch".

## Purpose

This skill makes the Element Plus design spec executable in two modes:

1) **Prefix mode**: output a paste-ready **Hard constraints prefix** for Stitch `[Context]`.
2) **Selector mode**: output `CONTRACT_SELECTION_JSON_V1` and then an assembled Stitch prompt that injects only the required component/state snippets.

## Trigger Keywords

Prefer this skill when the user request includes any of:

- `element`, `element-plus`, `el-plus`, `element-ui`

Chinese trigger keywords (only for triggering):

- `element 风格`
- `饿了么组件库`
- `后台管理系统` (if context implies Element Plus)

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
- Framework: Element Plus (Vue 3).
- Design Tokens:
  - Colors: Primary=#409EFF (Blue), Success=#67C23A, Warning=#E6A23C, Danger=#F56C6C, Info=#909399.
  - Typography: Font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", Arial, sans-serif.
  - Radius: Small=2px, Base=4px, Round=20px.
- Component Contracts:
  - Layout: Use <el-row :gutter="20"> and <el-col :span="...">. Container: <el-container>, <el-header>, <el-main>.
  - Buttons: Use <el-button type="primary" plain/round>.
  - Forms: Use <el-form>, <el-form-item>, <el-input>, <el-select>, <el-switch>, <el-checkbox>.
  - Data: <el-table>, <el-descriptions>, <el-timeline>, <el-carousel>, <el-empty>.
  - Cards: Use <el-card shadow="hover"> with #header slot.
  - Icons: Use <el-icon><Edit /></el-icon> (from @element-plus/icons-vue).
  - Navigation: <el-menu>, <el-breadcrumb>, <el-tabs>, <el-steps>.
  - Feedback: Use ElMessage.success() for JS feedback, <el-alert>, <el-dialog>, <el-drawer>.
- Layout Invariants:
  - Always use 24-column grid system.
  - Use el-space for inline spacing.
```

### Selector mode

Return exactly two code blocks, in this order, with no extra prose:

1) Contract selection JSON:

```json
{
  "version": "CONTRACT_SELECTION_JSON_V1",
  "designSystem": "element-plus",
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
(Describe the macro layout structure, e.g., "Admin Dashboard Layout with Sidebar")

[Components]
(Inject component snippets matching the JSON selection above)
```

## References

- [Contract](references/contract.md)
- [Examples](references/examples.md)
- [Official Docs](references/official.md)

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

## 常见陷阱 (Gotchas)

1. **版本兼容性**：注意框架版本与依赖库的兼容性，不同版本 API 可能有差异
2. **配置文件格式**：配置文件格式错误是最常见的问题，建议使用编辑器的语法检查
3. **环境变量**：确保所有必要的环境变量已正确设置，敏感信息不要硬编码
4. **依赖冲突**：多版本共存时注意依赖冲突，使用 lock 文件锁定版本
5. **性能陷阱**：大数据量场景下注意性能优化，避免 N+1 查询等常见问题

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
