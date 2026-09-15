---
name: stitch-mcp-get-project
description: Retrieves the detailed metadata of a specific Stitch project.
---


# Get Stitch Project Details

**CRITICAL PREREQUISITE:**
**You must ONLY use this skill when the user EXPLICITLY mentions "Stitch".**

## Constraints

**Do NOT use this skill if:**
*   You already have both `projectId` and `screenId` and your goal is to get screen details or code. Use `stitch-mcp-get-screen` directly instead.

This skill retrieves the detailed metadata of a specific Stitch project.

## Use Case
Invoke this skill when you need to know the context of a project (e.g., its default theme, device type) before generating new screens, or to verify project existence.

## Input Parameters

The skill expects you to extract the following information from the user request:
*   `name` (required): The resource name of the project. Format: `projects/{project_id}`.

## Resource Path Parsing

If the user provides a resource path or URL, use the following rules to extract the project name:

1.  **Format**: `web application/stitch/projects/{projectId}`
    *   **Logic**: Extract `projectId` and construct the name as `projects/{projectId}`.

2.  **Format**: `projects/{projectId}`
    *   **Logic**: Use the string as is.

3.  **Format**: `https://stitch.withgoogle.com/projects/{projectId}`
    *   **Logic**: Extract `projectId` and construct the name as `projects/{projectId}`.

**Example**: Input "Describe web application/stitch/projects/12345", Call `get_project(name="projects/12345")`.

## Output Schema

Returns a `Project` object including:
*   `name`, `title`, `createTime`, `updateTime`
*   `designTheme`: Detailed theme settings.
*   `screenInstances`: List of screen instances currently in the project.

## Usage Example

User Input: "What is the theme of project 'projects/123'?"

Agent Action:
1.  Identify the user wants details of a specific project.
2.  Extract project name "projects/123".
3.  Call `get_project` tool with arguments `{"name": "projects/123"}`.

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
