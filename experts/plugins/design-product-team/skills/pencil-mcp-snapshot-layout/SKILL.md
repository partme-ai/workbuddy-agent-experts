---
name: pencil-mcp-snapshot-layout
description: Get page layout structure snapshot. Use when you need to understand the current page's DOM-like tree structure to prepare for layout adjustments.
license: Apache-2.0
---


## Tools

This skill is designed to call the Pencil MCP tool:

*   `snapshot_layout`

If your client namespaces MCP tools, it may appear as `mcp__pencil__snapshot_layout`.

## When to use this skill

### Intent Recognition (CRITICAL)
Even if a trigger phrase matches, you must **verify the user's intent**:
1.  Is the user explicitly asking to use "Pencil"?
2.  Is the current conversation context clearly about "Pencil" design tasks?

**If the answer is NO, do NOT use this skill.** (e.g., "Analyze layout" might refer to HTML/CSS layout analysis).

**CRITICAL PREREQUISITE:**
**You must ONLY use this skill when the user EXPLICITLY mentions "Pencil".**

**ALWAYS use this skill when:**
- You need to understand the hierarchy and layout relationship of nodes **in Pencil**.
- You are planning to move or align elements and need their current bounds.
- You need to check for "problems" like clipped content or overlapping elements.
- The user asks to "Analyze layout" or "Check structure" **of a Pencil design**.

**Trigger phrases include:**
- "Pencil snapshot layout" (Pencil 布局快照)
- "Analyze Pencil page structure" (分析 Pencil 页面结构)
- "Check Pencil layout problems" (检查 Pencil 布局问题)
- "Get Pencil node hierarchy" (获取 Pencil 节点层级)

## Input Parameters

*   **`filePath`** (string, optional): Path to access a specific `.pen` file. Default is active document.
*   **`maxDepth`** (integer, optional): 
    *   Limit how deep to descend in the node tree. 
    *   **Recommendation**: Always specify a reasonable limit (e.g., 2 or 3) to avoid context overflow.
    *   `0` means only top-level nodes.
*   **`parentId`** (string, optional): Only return layout for this node's subtree.
*   **`problemsOnly`** (boolean, optional): 
    *   Set to `true` to only return nodes with layout issues (e.g., clipped by parent).
    *   Default: `false`.

## How to use this skill

1.  **Determine Scope**: Do you need the whole page (`maxDepth=1`) or a specific section (`parentId=...`)?
2.  **Call Tool**: `snapshot_layout(...)`.
3.  **Analyze Output**: The result is a tree structure with layout information (bounds, constraints).

## Examples

### 1. Simple: Top Level Snapshot
Get the layout of the top-level frames to see where empty space might be.
See [1-top-level.json](examples/1-top-level.json).

### 2. Medium: Specific Frame Layout
Get the layout structure of a specific frame to understand its children's positioning.
See [2-specific-frame.json](examples/2-specific-frame.json).

### 3. Complex: Layout Problems
Check for layout issues (like clipped content) deep within a specific section.
See [3-layout-problems.json](examples/3-layout-problems.json).

## Keywords

**English keywords:**
snapshot layout, layout analysis, node hierarchy, structure check, bounds check, layout problems

**Chinese keywords (中文关键词):**
布局快照, 布局分析, 节点层级, 结构检查, 边界检查, 布局问题

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
