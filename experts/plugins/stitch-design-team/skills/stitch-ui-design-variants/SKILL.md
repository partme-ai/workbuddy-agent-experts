---
name: stitch-ui-design-variants
description: Logic skill that generates prompts for alternative design variants e.g. A B testing options.
---


# Stitch Design Variants

This skill acts as a **Variant Generator**. It takes a base design and produces alternative prompts to explore different creative directions.

## Input
*   **Base Spec**: The original Design Spec or Prompt.
*   **Variant Type**:
    *   `LAYOUT`: Keep style, change structure.
    *   `STYLE`: Keep structure, change theme/colors.
    *   `CONTENT`: Keep design, change text/data.

## Output Format (List of Strings)
A list of 3 distinct prompts.

## Logic Rules

### 1. Layout Variants
*   *Variant A*: Standard layout.
*   *Variant B*: Split screen or asymmetrical layout.
*   *Variant C*: Minimalist/Hidden navigation layout.

### 2. Style Variants
*   *Variant A*: Original Theme.
*   *Variant B*: Inverted Theme (Light <-> Dark).
*   *Variant C*: High Contrast / Monochromatic.

## Usage Example
**User**: "Give me 3 style options for this dashboard."
**Output**:
1.  "Desktop Dashboard... **Dark Mode**... Blue accents..."
2.  "Desktop Dashboard... **Light Mode**... Clean white/grey..."
3.  "Desktop Dashboard... **High Contrast**... Black and White..."

## References

- [Examples](examples/usage.md)

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
