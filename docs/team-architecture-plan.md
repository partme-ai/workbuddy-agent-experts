# 12 插件 → WorkBuddy 专家团组织规划（讨论稿 v1，2026-09-15）

状态：**待用户拍板，未实施**。拍板后按现有 build 机制落地（多源 vendor / 中性化 / 非破坏安装全复用）。

## 一、能力底座盘点（实测）

| 插件 | 技能 | 执行通道 | 后端 / 账本 | 现状 |
|---|---|---|---|---|
| codex-blender-plugin | 27 | harness CLI（192 命令） | 本地 Blender，无外部付费 | ✅ 已建团队（30 技能+能力目录） |
| codex-dreamina-3d-plugin | 6 | MCP（Dreamina Design） | **即梦付费**，submit-once 门禁 | ❌ |
| codex-dreamina-design-plugin | 17 | CLI（47 scripts）+ MCP | **即梦付费**，真实 submit_id 门禁 | ❌ |
| codex-dreamina-canvas-plugin | 13 | CLI（10 scripts） | 即梦（auth 流程） | ❌ |
| codex-processon-plugin | 7 | MCP (http) + 7 scripts | ProcessOn（API key） | ❌ |
| codex-image-factory-plugin | 4 | CLI（**经本地 Codex CLI**） | **Codex 账户配额** | ✅ 已建团队 |
| codex-video-factory-plugin | 7 | node CLI | 本地合成，无外部付费 | ✅ 已建团队 |
| codex-stitch-design-plugin | 43 | MCP stdio proxy | Google Stitch | ✅ 已建团队 |
| director / script / storyboard | 0（方法论） | — | — | ✅ 已并入视频工厂 references |
| codex-maya-plugin | 4 | maya_adapter bridge | 本地 Maya（**本机未装**） | ❌ 暂缓 |

## 二、跨插件链路（已验证状态）

| 链路 | 状态 | 证据 |
|---|---|---|
| **blender → 即梦3D → Seedance 视频**（"白模视频"） | ✅ 通 | `codex-dreamina-3d-from-blender`（交接契约稳定标记）+ `auto-seedance`（auto_with_budget、quote 超限即停、submit-once 恢复、独立验证下载） |
| maya → 即梦3D | ❌ 断 | 3 处字段断点（capability_probe 路径、交接字段名），且本机无 Maya |
| 导演/剧本/故事板 → 视频工厂 | ✅ 已整合 | 以 references/ 方法论随视频工厂团队分发 |
| 图片工厂 ↔ 即梦设计 | 平行双轨 | **不同后端不同账本**：Codex 账户配额 vs 即梦付费，同名能力（文生图）但验收口径与故障域不同 |

## 三、两种组织方式的代价

**方案 A：每仓库一团队**（一一对应）
- 优点：边界清晰、独立演进、配额账本天然隔离。
- 缺点：12 仓库 → 15+ 团队；跨仓库场景（短剧全链路）没有归属，用户要自己跨团队接力。

**方案 B：大整合**（图片工厂吞所有图源、视频工厂吞所有视频源）
- 优点：入口少。
- 缺点（硬伤）：①**技能触发稀释**——WorkBuddy 按技能 description 触发，单团队 50-80 技能会互相打架（我们最大的 Stitch 团队 44 技能已接近上限）；②**配额账本混淆**——Codex 与即梦的预算/门禁/验收口径不同，合在一起编排者必错；③单插件 vendor 10+ 仓库，体积与故障域失控。

**方案 C（推荐）：执行团队按"后端账本"划分 + 场景由交接契约与编排层承载**

1. 执行团队（新增 4 个，每个对应一个独立账本/执行面）：
   - **ProcessOn 专家团**（processon，7 技能 + MCP 调用规范）
   - **即梦设计专家团**（dreamina-design，17 技能；图/视频/声音多模态，即梦付费门禁）
   - **即梦画布专家团**（dreamina-canvas，13 技能）
   - **即梦3D视觉专家团**（dreamina-3d，6 技能；**含 from-blender 交接与 auto-seedance 白模视频场景**）
2. **不合并** 图片工厂（Codex 后端）与即梦设计（即梦后端）：双轨保留，用户按账号与风格选择。
3. **blender 与 3D 视觉保持两团队 + 交接契约**，而非合并成巨型团队：blender 团队（30 技能）负责建模与预览交付，3D 视觉团队的 from-blender 技能消费交接产物走 Seedance——这是上游已验证的集成点，合并只会带来技能稀释。
4. maya 暂不建团队：交接断点未修 + 本机无 Maya；修通后作为 3D 视觉团队的第二 DCC 源并入。
5. （可选，二期）**短剧制片厂**：一个薄编排团队——成员为导演/编剧/故事板方法论 + 编排职责，调度"即梦设计（生素材）/ 即梦3D视觉（白模视频）/ 视频工厂（合成）"三个执行团队，自身不 vendor 执行技能。

## 四、落地后的全景（方案 C）

执行团队 11 → **15**：Blender 3D 生产 / Stitch / 图片工厂 / 视频工厂 / ProcessOn / 即梦设计 / 即梦画布 / 即梦3D视觉 + 已有 7 个领域团队（工程/设计/GIS/增长营销/质量安全/产品策略/财务经营）；16 单专家不变。

## 五、待拍板的决策点

1. 新增 4 个执行团队按方案 C 建？（若同意，机制全复用，一次交付）
2. blender+3D：两团队+交接契约（推荐）还是合并巨型团队？
3. 二期要不要"短剧制片厂"编排团队？
4. 图片工厂（Codex 后端）与即梦设计双轨保留，确认？
5. maya 暂缓，确认？
