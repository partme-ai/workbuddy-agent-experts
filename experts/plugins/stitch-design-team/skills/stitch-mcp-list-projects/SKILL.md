---
name: stitch-mcp-list-projects
description: Lists all Stitch projects accessible to the user.
---


# List Stitch Projects

**CRITICAL PREREQUISITE:**
**You must ONLY use this skill when the user EXPLICITLY mentions "Stitch".**

This skill lists all Stitch projects accessible to the user.

## Use Case
Invoke this skill when the user wants to resume work on an existing project, or needs to check what projects are currently available.

## Input Parameters

The skill expects you to extract the following information from the user request:
*   `filter` (optional): Filter for projects to list. Defaults to `"view=owned"`.
    *   `"view=owned"`: Projects owned by user.
    *   `"view=shared"`: Projects shared with user.

## Output Schema

Returns an object containing a list of projects:
*   **`projects`**: (Array of Project)
    *   `name`: Resource ID (e.g., `projects/123...`).
    *   `title`: Project title.
    *   `updateTime`: Last modification time.
    *   `thumbnailScreenshot`: Preview image of the project.

## Usage Example

User Input: "Show me my existing projects."

Agent Action:
1.  Identify the user wants to list projects.
2.  Call `list_projects` tool with arguments `{"filter": "view=owned"}`.

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
