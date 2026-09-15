# 编剧插件功能与架构

日期：2026-09-13。状态：规划基线。
公共规范：[数据契约](https://github.com/partme-ai/creative-production-workbench/blob/main/docs/superpowers/specs/contracts.md)、[执行条件](https://github.com/partme-ai/creative-production-workbench/blob/main/docs/superpowers/specs/operations.md)。

## 1. 职责

小说、故事与已有剧本的分析、改编、大纲、分场剧本和语义拆解。输入：SourceMaterial / SourceSpan、改编目标、目标集数/时长、锁定原作事实与素材策略。输出：StoryBible、Outline、EpisodeOutline、Screenplay / Scene、BreakdownCandidate、SourceCoverage。

决定故事和对白；不自行生成导演镜头路线，不编排实际付费图片/视频，不代替工作台资产/版本服务。

## 2. 工作流与拟定 Skills

下列是计划中的 Skill，尚未生成 SKILL.md 或声称可以调用。

| Skill 计划名 | 用途 | 可观察行为 |
|---|---|---|
| codex-script-source | 读取与原文覆盖 | 按章节增量读原文，提取事实、事件与实体别名，绑定 source_id/revision/span；记录未提供和未处理范围。 |
| codex-script-adapt | 改编策略 | 依据用户的目标长度和风格给出保留、合并、删减和原创新增；原文事实与创作推断分别标注。 |
| codex-script-outline | 大纲与分集 | 输出总纲、集纲和场次目标；记录人物动机、伏笔、事件顺序与人物知识边界。 |
| codex-script-screenplay | 分场剧本 | 场次含标题、内外景/时段、角色、冲突、动作、对白、入出状态和来源；保护人工锁定段落。 |
| codex-script-breakdown | 语义拆解 | 提取角色、地点、服装、道具、声音和VFX需求，提供候选 AssetSpec；同一实体不重复建ID。 |
| codex-script-revision | 改写与交付 | 提交候选 revision，返回改编说明/覆盖报告；结束到剧本的请求，或在完整制作授权下交接 Director。 |

```mermaid
flowchart LR
    Context[工作台上下文与固定版本] --> Plan[编剧领域规划]
    Plan --> Draft[结构化候选结果]
    Draft --> Check[领域评估与引用检查]
    Check --> Commit[MCP原子写入]
    Commit --> View[工作台即时展示]
    View --> Change[用户批注/修订]
    Change --> Context
```

## 3. 执行协议

1. 通过 workbench_project_context 读取项目目标、相关实体与固定版本。缺上下文时分页读取，不重复导入原文。
2. 如存在同一任务已接受结果，先检查输入 revision 是否变化；不因换新对话而重复执行。
3. 用 workbench_task_claim 领取无冲突任务，绑定租约和 input_refs。
4. 宿主执行本插件领域创作；写入前按契约检查数据形状、ID、来源和时长。
5. document_commit / shot_batch_commit / asset_spec_commit 返回服务生成 revision、hash 和 event cursor。
6. 超时先按 operation_id 核查是否已落盘；不可直接重复产生用户可见实体。
7. 保存候选的技术成功与领域内容评估分离。需要用户评审时在工作台集中呈现问题，不每个中间字段弹窗。
8. 完整制作任务在授权停点前继续；仅本领域任务则交付对应制作包。

## 4. 质量与异常

必须包含以下行为测试/评估：别名人物、倒叙、原文缺章、长章分块、改编新增误标、人工锁定对白、跨章人物知识泄漏、相同操作重放。

每份候选显示来源版本、生成方式、未解决问题和人工锁定项。不能将 Schema 通过、关键词存在或模型自评分替代内容验收。

用户改动产生新 revision；插件读取 change_list 并只重做受影响结果。上游原文/剧本更新不直接删除下游图像或视频，标注 stale 并保留已选定版本。

## 5. 与其他插件协作

| 来源 | 本插件处理 | 下游 |
|---|---|---|
| 工作台存储的固定版本输入 | 编剧领域创作与候选评估 | 工作台新 revision |
| 用户界面批注 | 分类为本领域修改或跨领域 ChangeProposal | 相应任务重新规划 |
| 当前不存在的图片/白模/声音 | 登记明确规格与素材需求 | 经授权的现有生产插件 |
| 过期上游数据 | 标记依赖变化，重取必要上下文 | 不盲目复用旧报价/生产请求 |

插件互不直接调用内部代码。宿主负责路由和流程；所有结果关联到同一项目。

## 6. 交付清单

交付 StoryBible、Outline、EpisodeOutline、Screenplay / Scene、BreakdownCandidate、SourceCoverage 的结构化版本、用户可读视图/导出、上游依赖列表、出处或改编说明、未解决问题、任务执行回执。

集成实施前必须固定 contracts.lock.json 的工作台 commit 与 schema SHA；计划版本不是运行兼容性证明。

## 7. 发行边界

本轮不安装、不创建 marketplace entry。实现阶段再依据真实可用 Skills 创建 .codex-plugin/plugin.json；插件 ID 使用 codex-script，repo 名带 -plugin，与现有组织仓库命名一致。若脚手架要求包目录与ID相同，放在 plugins/codex-script 并在发行目录保持同名，不为绕过规范改变用户仓库名。
