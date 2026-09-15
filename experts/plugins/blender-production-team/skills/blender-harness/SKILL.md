---
name: blender-harness
description: Launch a managed Blender harness session and dispatch structured JSON commands through harness_cli.py. Covers session bootstrap, the closed request envelope (protocolVersion/sessionId/requestId/transactionId/command/arguments/expectedSceneRevision), receipt verification, error codes, capability maturity levels and background jobs. Use this skill for ANY task that needs to create, modify, inspect or export Blender content.
---

# Blender Harness 调用规范

本技能定义在 WorkBuddy 中驱动 Blender 的**唯一执行通道**。它是平台无关的：启动器 + JSON 命令行客户端 + 运行在 Blender 内的结构化命令注册表。所有命令契约、回执 schema 与验收阈值以本插件随附的 `blender-production` 技能参考文档为准。

## 1. 定位插件目录

本技能位于 `<插件根>/skills/blender-harness/SKILL.md`。插件根目录（含 `scripts/`、`schemas/`、`config/`）即执行入口所在：

```
<插件根>/scripts/launch_harness.py     # 启动托管会话
<插件根>/scripts/harness_cli.py        # 向会话派发命令
```

在 shell 中用 `pwd`/`ls` 确认实际路径后再执行；不要凭记忆猜路径。

## 2. 启动会话（每个生产任务一次）

```bash
mkdir -p <输出根目录>            # 所有产物必须落在该授权目录内
python3 <插件根>/scripts/launch_harness.py \
    --session-id <唯一会话ID> \
    --output-root <输出根目录的绝对路径> \
    --execution-mode auto_with_budget
```

- Blender 可执行文件自动发现（PATH 或 `/Applications/Blender.app/Contents/MacOS/Blender`）；装在别处时传 `--blender <路径>`。
- 启动成功后打印 descriptor（含 `address`、`token`、`descriptorPath`）。**记下 descriptorPath**——后续所有命令都要用它。
- 会话结束后按 descriptor 里的说明关闭；不要留孤儿 Blender 进程。

## 3. 派发命令

把请求写成 JSON 文件再发送（闭合契约，多余字段直接报 `INVALID_REQUEST`）：

```json
{
  "protocolVersion": "codex-blender/v1",
  "sessionId": "<与会话一致>",
  "requestId": "<本次请求唯一ID>",
  "transactionId": "<事务ID>",
  "command": "mesh.inspect",
  "arguments": {}
}
```

```bash
python3 <插件根>/scripts/harness_cli.py \
    --descriptor <descriptorPath> --request <请求.json>
```

### 修改类命令必须走事务（读命令不需要）

凭空编造 `transactionId` 会得到 `TRANSACTION_NOT_FOUND`。正确序列：

1. **`transaction.begin`**（`arguments` 必须为空对象）→ 返回 `snapshotId` 与当前 `sceneRevision`。
2. **修改命令**（如 `object.create_mesh`）：带同一 `transactionId`，并带 `expectedSceneRevision` = begin 返回的 revision；每次成功修改后 revision 递增，下一条命令要跟上。
3. **`transaction.commit`**（`arguments` 为空对象）→ 提交事务，快照进入已批准状态。
4. **`export.file`**：`arguments.snapshotId` 必须**逐字等于** commit 批准的 snapshotId，否则报 `MILESTONE_NOT_APPROVED`。

规则：
- `requestId` 每次唯一；读命令（`*.inspect`、`capability.*`、查询类）不需要事务，也不需要 revision。
- 响应是 JSON：`status` 为 `succeeded` 时核对 `result` 与 `changedObjects`；`failed` 时读 `error.code` 与 `error.message`。

## 4. 常用错误码

| 错误码 | 含义 | 下一步 |
|---|---|---|
| `INVALID_ARGUMENT` | 参数闭合校验失败 | 对照技能参考里的参数表修正，不要换 undocumented 参数 |
| `TRANSACTION_NOT_FOUND` | 事务不存在（未 begin 或已 commit/rollback） | 先 `transaction.begin` 再发修改命令 |
| `STALE_SCENE_REVISION` | expectedSceneRevision 过期（可重试） | 用响应里的当前 revision 重发 |
| `MILESTONE_NOT_APPROVED` | 导出的 snapshotId 未在当前 revision 提交 | 走完整事务：begin → 修改 → commit → export |
| `OUTPUT_NOT_AUTHORIZED` | 目标路径不在授权输出根内 | 改用会话的 output-root 下的路径 |
| `DISK_RESERVE_EXCEEDED` | 磁盘保留策略超限 | 清理空间或换盘；不要绕过 |
| `ROTATION_MODE_MISMATCH` | 姿态通道与骨骼 rotation_mode 不符 | 换匹配通道或先设 rotation_mode |
| `MEDIA_INVALID` | 产物媒体探测不过（编码/帧率） | 按报错的实际值修正输出设置 |
| `CAPABILITY_UNAVAILABLE` | 命令在当前运行模式不可用 | `capability.describe` 查前置条件 |
| `AUTHORIZATION_REQUIRED` | 门禁命令缺授权声明 | 走 `session.authorize`；用户拒绝就如实上报 |

## 5. 能力目录与成熟度

开工前先查，不要假设：

```json
{"command": "capability.list", "arguments": {"domain": "mesh"}}
{"command": "capability.describe", "arguments": {"id": "export.file"}}
```

成熟度分层：**L1** 可查询（产物不可交付）、**L3** 可生产（有 runtime/visual/delivery 证据）、**L4** 可恢复生产。交付任务只允许 L3+ 命令产出。

## 6. 后台任务（长渲染/烘焙）

```json
{"command": "job.submit", "arguments": {"jobId": "render_001", "kind": "RENDER_ANIMATION_FRAMES", "parameters": {...}}}
{"command": "job.status",  "arguments": {"jobId": "render_001"}}
{"command": "job.list",    "arguments": {"state": "running"}}
```

最大并发 2；第三个任务 FIFO 排队；磁盘保留 `max(卷容量20%, 20GB)`，超限时**不落快照、不启进程**。取消用 `job.cancel`。

## 7. 纪律

1. 回执是唯一事实——"应该成功了"不算数。
2. 每个验收断言都要能失败；测量值（计数/误差/哈希/探测）必须进汇报。
3. 门禁（gated/foreground）被拒就如实上报，不重试绕过。
4. 产物路径永远在授权输出根内；导出走 `export.*` 命令而不是直接写 Blender 设置。
