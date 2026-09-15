---
name: blender-production
description: Domain reference library for Blender production work - routing table into 26 specialist references covering modeling, retopology, UV, rigging, animation, hair, simulation, Grease Pencil, materials, compositor, VSE, render, export, background jobs, connector recovery and delivery contracts. Read the routing table first, then only the reference matching your task.
---

# Blender 生产参考库（路由）

本技能是**按需阅读的参考库**：先查路由表找到你的领域，再只读对应的参考文档。参考文档（`references/` 下 26 份）来自插件的生产技能集，包含命令参数表、回执契约、验收阈值与已知限制。**动手前不读对应参考 = 大概率返工。**

## 路由表

| 你的任务 | 先读参考 |
|---|---|
| 建模 / 网格 / 修改器 / 曲线 | `references/codex-blender-modeling.md` |
| 硬表面 / 产品件 / 壳体 | `references/codex-blender-design.md` |
| 重拓扑（可编辑网格） | `references/codex-blender-retopology.md` |
| UV / 纹理密度 / 重叠检查 | `references/codex-blender-uv-texturing.md` |
| 绑定 / 权重 / 变形验证 / Rigify | `references/codex-blender-character-rigging.md` |
| 角色动画 / 长矛交接回归 | `references/codex-blender-character-animation.md` |
| 关键帧 / NLA / 驱动 / 运动路径 | `references/codex-blender-animation.md` |
| 相机 / 运镜 / 摄影 | `references/codex-blender-cinematography.md` |
| 毛发 | `references/codex-blender-hair.md` |
| 布料 / 刚体 / 流体 / 软体 | `references/codex-blender-simulation.md` |
| Grease Pencil | `references/codex-blender-grease-pencil.md` |
| 雕刻 | `references/codex-blender-sculpting.md` |
| 材质 / 着色器 / 烘焙 | `references/codex-blender-materials.md` |
| 灯光 / 渲染 / 通道 | `references/codex-blender-rendering.md` |
| 合成器 | `references/codex-blender-compositing.md` |
| VSE 剪辑 / 代理 / 变速 / 音频 | `references/codex-blender-video-editing.md` |
| 导出（模型/媒体/USD/EXR） | `references/codex-blender-export.md` |
| 后台任务 / 烘焙作业 | `references/codex-blender-background-jobs.md` |
| 会话恢复 / 崩溃恢复 | `references/codex-blender-recover.md` |
| 前台 UI / 人工接管 | `references/codex-blender-foreground.md` |
| Connector（GUI 内运行） | `references/codex-blender-connector.md` |
| Geometry Nodes | `references/codex-blender-geometry-nodes.md` |
| 资产 / 库 / 打包 | `references/codex-blender-assets.md` |
| 快照 / 场景修订 | `references/codex-blender-snapshots.md` |
| 质检 / 交付 / 回执审计 | `references/codex-blender-delivery.md` |

（命名以 `references/` 目录实际文件为准；上表缺的领域先 `capability.list` 查命令再读通用纪律。）

## 通用纪律（所有领域共用）

1. **闭合契约**：命令参数以参考文档的参数表为准；多余参数会被拒绝，这不是 bug。
2. **回执审计**：产物核对存在性、非零大小、SHA-256、格式；模型格式要求隔离重导入验证，媒体走探测。
3. **测量优先**：验收断言必须是测量值（计数、误差、比率、哈希），并配有能失败的对照。
4. **成熟度门槛**：交付物只能来自 L3+ 命令；L1 输出仅供探索。
5. **revision 链**：快照 → 修改 → 导出的 `expectedSceneRevision` 链必须连贯，断链即重做。
6. **如实申报**：没验证的写"未验证"，没跑的平台写"未运行"，阈值没触发的写"未触发"。
