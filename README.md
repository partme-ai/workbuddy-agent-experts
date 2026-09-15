# workbuddy-agent-experts

独立智能体库 + WorkBuddy 组团器：**智能体以独立单元存在，脚本把智能体组装成团队插件**，产出本地 marketplace 供 WorkBuddy 安装。

## 目录约定

```
agents/<id>.md     独立智能体（单一事实源）：frontmatter + 系统提示词
teams/<name>.yaml  团队定义：成员组合、人设、技能、执行面来源
skills/<name>/     本项目自写的调用/编排规范技能
assets/logo.png    项目 logo（首次构建自动生成，可替换）
scripts/build.py   组装器：agents + teams + 兄弟仓库执行面 → experts/
experts/           构建产物（gitignored，确定性可重建）：完整 marketplace 树
                   experts/.codebuddy-plugin/marketplace.json + experts/plugins/<插件>/
```

**源 vs 产物（发行模式）**：`agents/ teams/ skills/ singles.yaml` 是手工编辑的源；
`experts/` 是**预构建产物，随仓库一起提交**——使用者不需要兄弟仓库、不需要构建，
克隆即得完整 marketplace（含 vendor 好的执行面）。维护者改源后跑 `build.py`
重新生成 experts/ 并提交（构建需要本机存在 ../codex-* 兄弟仓库检出）。

### 独立智能体格式（agency-agents-zh 风格 + WorkBuddy 适配块）

```yaml
---
name: blender-modeler          # 唯一 id（英文）
title: 建模专家                  # 中文称号
description: 一句话触发描述。      # 必须单行
color: "#C2410C"               # 头像底色
emoji: 🧱
workbuddy:                     # 组团时的平台适配（可选）
  displayName: {en: Blender Modeling Specialist, zh: Blender 建模专家}
  profession: {en: 3D Modeler, zh: 3D 建模师}
  maxTurns: 120
---
（系统提示词正文）
```

## 构建

```bash
python3 scripts/build.py                 # 全部团队
python3 scripts/build.py teams/3d-production.yaml --out dist
```

产物：`experts/plugins/blender-production-team/`（marketplace 清单在 `experts/.codebuddy-plugin/`）
（执行面 harness 在构建时从 `teams/*.yaml` 的 `harness.repo` 指向的 codex-blender-plugin 检出 vendor，26 份生产技能收进 `blender-production/references/`。）

## 安装到 WorkBuddy（非破坏式）

`python3 scripts/build.py --install` 只替换本构建管理的插件，**保留** my-experts 里
应用 UI 或他方创建的专家（目录与清单条目都保留；安装前实测外部标记幸存）。
my-experts 是应用与本项目共用的通道：应用启动时 `scanCustomExperts` 会对账清单，
所以手工放置的外部插件也会被自动并入。

**安装（macOS / Linux）**

```bash
git clone https://github.com/partme-ai/workbuddy-agent-experts.git
cd workbuddy-agent-experts
./install.sh            # 或 ./install.sh --uninstall 卸载
```

**安装（Windows PowerShell）**

```powershell
git clone https://github.com/partme-ai/workbuddy-agent-experts.git
cd workbuddy-agent-experts
.\install.ps1           # 卸载：.\install.ps1 --uninstall
```

安装器（`scripts/install.py`，纯标准库）把 `experts/` 部署到
`~/.workbuddy/plugins/marketplaces/my-experts/`（官方自定义通道，应用源码只注册
experts + my-experts 两个名字）；同时写 cache 镜像与安装记录（改前自动 .bak 备份）。
**非破坏式**：只替换本套件拥有的插件，应用 UI 或他方创建的专家幸存（已实测）。
装完重启 WorkBuddy（或重开专家选择器）。

> 2026-09-15 源码级结论（app.asar 反解）：注册名单硬编码 `experts` + `my-experts`；
> `my-experts/.codebuddy-plugin/marketplace.json` 必须存在且列出插件，否则 scanCustomExperts
> 返回空；无 `experts/custom/<userId>/experts.json` 白名单文件时全部列出。

## 已吸纳的智能体库（agency-agents-zh 全量）

`python3 scripts/import_agency.py [--force]` 把 [agency-agents-zh] 的 **263 个智能体**导入
`agents/<类目>/<id>.md`（19 个类目：engineering 50 / specialized 60 / marketing 42 / gis 13 / ...）。
导入即转换：中文名→title、文件名→英文 id、描述压单行、色名保留（构建时映射 hex）、
附 `workbuddy:` 适配块（含 categoryId 映射）。正文原样保留。

## 已有团队与单专家

| 团队 | 主理人 + 成员 | 插件 |
|---|---|---|
| Blender 3D 生产专家团 | 岚一 + 塑岩/骨风/彩澜/影流/核真 | blender-production-team@my-experts |
| 工程研发专家团 | 衡工 + 架构/后端/评审/数据库/DevOps/数据 6 专家 | engineering-team@my-experts |
| 设计专家团 | 蕴美 + UX架构/UI/用研/品牌/叙事 5 专家 | design-team@my-experts |
| GIS 空间专家团 | 图澜 + 方案/三维/空间数据/WebGIS/BIM/制图 6 专家 | gis-spatial-team@my-experts |
| 增长营销专家团 | 燃野 + 内容/抖音/B站/SEO/电商 5 专家 | growth-marketing-team@my-experts |
| 质量与安全专家团 | 守拙 + API测试/性能/应用安全/威胁检测/应急 5 专家 | quality-security-team@my-experts |
| 产品与策略专家团 | 明衡 + 产品/趋势/反馈/排期/战略 5 专家 | product-strategy-team@my-experts |
| 财务经营专家团 | 持盈 + 分析/投资/税务/反欺诈/CFO 5 专家 | finance-operations-team@my-experts |
| Google Stitch 专家团 | 织界 + 界面设计/设计系统/代码工程/交付验收 | stitch-design-team@my-experts |
| 图片工厂专家团 | 画枢 + 提示词/生产/评审/恢复（经本地 Codex CLI 出图） | image-factory-team@my-experts |
| 视频工厂专家团 | 影枢 + 导演/编剧/故事板/生产/评审（rough→批准→final） | video-factory-team@my-experts |
| ProcessOn 专家团 | 图叙 + 导图/图解/信息图/审阅 | processon-team@my-experts |
| 即梦设计专家团 | 梦绘 + 图片/视频/评测/付费门禁（图+视频；**声音在画布**） | dreamina-design-team@my-experts |
| 即梦画布专家团 | 布澜 + 建布/多媒(图视频**音频**)/时间线/运营 | dreamina-canvas-team@my-experts |
| 即梦3D视觉专家团 | 幻构 + Blender交接/Seedance制片/网页兜底/恢复（白模视频） | dreamina-3d-team@my-experts |
| 短剧制片厂（薄编排层） | 剧枢 + 导演/编剧/故事板/管线协调；调度即梦设计/3D视觉/视频工厂 | short-drama-studio-team@my-experts |

单专家（expertType: agent）：`singles.yaml` 当前精选 16 个（AI 工程师/无障碍审计/渗透测试/港股合规审查等）；
**改为 `singles: ['*']` 即可把全部 263+ 智能体逐一发布为单专家**。团队 lead 也是单专家发布的一员。

## 新增一个智能体 / 一个团队

- **加智能体**：`agents/<id>.md` 按上述格式写好即可（独立存在，可被任意团队引用）。
- **加团队**：复制 `teams/3d-production.yaml` 改成员与来源，`python3 scripts/build.py` 后按上节安装。

[agency-agents-zh]: https://github.com/wandl/agency-agents-zh
