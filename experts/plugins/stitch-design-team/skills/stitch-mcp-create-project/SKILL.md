---
name: stitch-mcp-create-project
description: Creates a new Stitch project container. Use this when starting a new design task, app idea, or fresh workspace.
license: Complete terms in LICENSE.txt
---


## When to use this skill

**CRITICAL PREREQUISITE:**
**You must ONLY use this skill when the user EXPLICITLY mentions "Stitch".**

**ALWAYS use this skill when:**
- The user wants to start a **new** design task or app idea **using Stitch**.
- The user asks to "create a Stitch project", "start a new app in Stitch".
- The user switches context to a completely different domain (e.g., from "Medical App" to "Gaming App") and needs a clean slate.
- You need to obtain a `projectId` before generating screens.

**Trigger phrases include:**
- "Create a new Stitch project" (创建新 Stitch 项目)
- "Start a new Stitch app" (开始一个新 Stitch 应用)
- "Initialize Stitch workspace" (初始化 Stitch 工作区)

## How to use this skill

1.  **Analyze the User Request**: Extract a meaningful `title` for the project.
    *   *User*: "Design a cyberpunk blog." -> *Title*: "Cyberpunk Blog"
    *   *User*: "Make a login page." -> *Title*: "Login Page Project" (Generic)

2.  **Call the MCP Tool**: Invoke `create_project` with the `title`.
    *   If your client namespaces MCP tools, call `mcp__<serverName>__create_project`.

3.  **Handle the Output (CRITICAL)**:
    *   The tool returns a `name` field (e.g., `projects/123456`).
    *   **YOU MUST EXTRACT THE NUMERIC ID**.
    *   *Example*: `projects/123456` -> `123456`.
    *   Store **BOTH** the full name (`projects/123...`) and the numeric ID (`123...`) in your context.
    *   **Usage Rule**:
    *   Use **Numeric ID** (`123...`) for `generate_screen_from_text` and `list_screens`.
    *   Use **Full Name** (`projects/123...`) for `get_project`.
    *   Use **Screen Full Name** (`projects/123.../screens/abc...`) as the `name` for `get_screen`.

## Best Practices

1.  **Meaningful Titles**: Always try to infer a descriptive title. Avoid "Untitled Project".
2.  **One Project per Domain**: Encourage users to keep related screens (Login, Home, Settings) in the same project. Only create a new project if the domain changes.
3.  **Context Persistency**: Explicitly tell the user: "I've created project 'X' (ID: 123). I will use this for our design session."

## Keywords

**English keywords:**
create project, new project, start app, initialize, setup, workspace, container, new design, project id, stitch project

**Chinese keywords (中文关键词):**
创建项目, 新建项目, 开始设计, 初始化, 建立工程, 新应用, 项目ID, 启动项目

## References

- [Examples](examples/usage.md)

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
