---
name: stitch-mcp-list-screens
description: Lists all screens contained within a specific project.
---


# List Screens

**CRITICAL PREREQUISITE:**
**You must ONLY use this skill when the user EXPLICITLY mentions "Stitch".**

Lists all screens contained within a specific project.

## Use Case
Invoke this skill to browse the history of generated designs in a project or to find a specific screen to reference or iterate upon.

## Input Parameters

The skill expects you to extract the following information from the user request:
*   `projectId` (required): Bare project ID string, for example `123456`; never add the `projects/` prefix.

## Output Schema

Returns an object with `screens` array:
*   **`screens`**:
    *   `name`: Resource identifier (e.g., `projects/123/screens/abc`).
    *   `title`: Auto-generated title.
    *   `screenshot`: Thumbnail URL.
    *   `deviceType`: The device type of the screen.

## Usage Example

User Input: "Show me all screens in this project."

Agent Action:
1.  Extract project ID.
2.  Call `list_screens` with the bare ID: `{"projectId": "123456"}`.

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
