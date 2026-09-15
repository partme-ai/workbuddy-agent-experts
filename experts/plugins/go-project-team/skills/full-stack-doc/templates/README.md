# Templates

Ready-to-copy Markdown templates for the general product documentation standard.

## Quick Start

1. Copy templates from the appropriate directory
2. Replace `{{PRODUCT_NAME}}` with the product name in **both filenames and content**
3. Replace `{{VERSION}}` with the version identifier (e.g., `V1`) for version-level docs
4. Replace `{{MODULE_NAME}}` with the module short name for module-level docs
5. Fill in `{{DATE}}` dates, `{{OWNER}}` author names, and other placeholders
6. Follow the inline `{例如：...}` guidance to populate each section
7. Read [`placeholder-protocol.md`](../references/placeholder-protocol.md) before bulk replacement; do not replace JSON/code braces
8. Keep full examples labeled, and remove optional patterns that do not match the target product

## Template Directories

| Directory | Contents | Count | Description |
|:---|:---|:---:|:---|
| [`root/`](root/) | Root-level standard docs | 10 | 产品级规划文档，与版本无关 |
| [`version/`](version/) | Per-version standard docs | 7 | 版本级实施文档，每个版本目录一套 |
| [`module/`](module/) | Per-module PRD / Stitch / UI triplet | 3 | 可选，按功能模块细化 |
| [`delivery/`](delivery/) | Tech details + delivery phase docs | 5 | 可选，研发交付阶段 |
| [`readme/`](readme/) | Project README template family | 5 | Java、Rust、插件、技能生态专用模板及完整参考模板 |
| [`architecture/`](architecture/) | Complete architecture template family | 1 + 7 profiles | 通用架构母模板及运行时、插件、边缘、消息、AI、控制面剖面 |

## Root Templates (10)

Root 文档为产品级基线，覆盖从品牌到功能的完整规划链：

| # | Template | Key outcome |
|:---:|:---|:---|
| 1 | `1、命名与品牌说明.md` | 品牌定位、命名规则、产品边界、品牌家族关系 |
| 2 | `2、术语表与词汇表.md` | 产品/架构/业务/平台术语、缩略词、使用规则 |
| 3 | `3、市场与商业分析.md` | 有来源与置信度的市场机会、TAM/SAM/SOM、竞品、商业模式 |
| 4 | `4、技术与可行性分析.md` | 有验证证据的可行性、安全、性能、成本与风险结论 |
| 5 | `5、技术方案与路线.md` | 技术选型、ADR、里程碑、部署与回滚决策 |
| 6 | `6、产品与版本规划.md` | 产品定位、版本矩阵、路线图、发布策略与成功指标 |
| 7 | `7、领域模型设计.md` | 与真实复杂度匹配的领域边界、规则、事件与接口 |
| 8 | `8、系统架构设计.md` | 可实施的边界、数据流、安全、部署、观测与失败处理 |
| 9 | `9、视觉与交互DNA规范.md` | 可测试的设计令牌、组件、动效、响应式与无障碍规则 |
| 10 | `10、功能菜单与版本规划.md` | 信息架构、菜单、权限、路由、版本与用户旅程一致 |

## Version Templates (7)

版本文档为某一具体版本（如 V1）的实施级细化：

| # | Template | Description |
|:---:|:---|:---|
| 1 | `1、需求调研文档.md` | 用户调研、访谈、场景分析 |
| 2 | `2、需求分析文档.md` | 用户故事、功能规则、验收标准 |
| 3 | `3、系统架构设计.md` | 版本级架构细化、技术决策 |
| 4 | `4、功能与界面规划.md` | 模块划分、界面规划 |
| 5 | `5、PRD文档.md` | 版本级需求规格说明 |
| 6 | `6、功能菜单与版本规划.md` | 版本级菜单与功能规划 |
| 7 | `7、UI设计说明.md` | 页面结构、组件、动效、切图 |

## Module Templates (3)

模块文档为版本内某一功能模块的三件套：

| Template | Description |
|:---|:---|
| `模块-PRD.md` | 模块级产品需求文档，含功能规则、数据、交互 |
| `模块-Stitch设计提示词.md` | AI 设计生成提示词（英文） |
| `模块-UI设计说明.md` | 页面结构、组件使用、动效、适配、切图 |

## Delivery Templates (5)

交付文档为研发过程中的阶段性输出：

| # | Template | Description |
|:---:|:---|:---|
| 1 | `1、技术细分模板.md` | 技术栈、架构拆分、接口、数据库、工时、风险 |
| 2 | `2、功能提测模板.md` | 提测范围、环境、功能清单、部署步骤 |
| 3 | `3、测试结果模板.md` | 测试统计、问题汇总、发布建议 |
| 4 | `4、上线通知模板.md` | 上线范围、时间窗口、回滚计划 |
| 5 | `5、项目运维模板.md` | 部署架构、监控、故障处理、备份 |

## Project README Template Family (5)

| Template | Use for |
|---|---|
| [`readme/README-Java项目模板.md`](readme/README-Java项目模板.md) | Java libraries, SDKs, starters, frameworks, and Maven multi-module projects |
| [`readme/README-Rust项目模板.md`](readme/README-Rust项目模板.md) | Rust crates and Cargo workspaces; combine with [`readme/rust-profiles/`](readme/rust-profiles/) for domain-specific coverage |
| [`readme/README-插件项目模板.md`](readme/README-插件项目模板.md) | Host plugins, adapters, connectors, and event bridges |
| [`readme/README-技能包与生态目录模板.md`](readme/README-技能包与生态目录模板.md) | Agent Skill packages, catalogs, marketplaces, and navigation hubs |
| [`readme/README模板.md`](readme/README模板.md) | Complete reference/source library and unmatched services, CLI, desktop, or example projects |

Before using them, read [`readme-template-guide.md`](../references/readme-template-guide.md) to choose the closest project type, combine hybrid cases, and derive facts from manifests, source, CI, release metadata, and governance files.

### Rust domain profiles (7)

| Profile | Purpose |
|---|---|
| [`rust-profiles/README.md`](readme/rust-profiles/README.md) | Selection, composition and conflict rules |
| [`文档与文件格式处理剖面.md`](readme/rust-profiles/文档与文件格式处理剖面.md) | Format capabilities, round-trip fidelity, templates, backends, resources and hostile inputs |
| [`上游兼容与移植剖面.md`](readme/rust-profiles/上游兼容与移植剖面.md) | API/behavior/data parity, upstream provenance and migration |
| [`大型工具箱Workspace剖面.md`](readme/rust-profiles/大型工具箱Workspace剖面.md) | Capability catalog, facade exports, feature costs and multi-crate release |
| [`认证与安全框架剖面.md`](readme/rust-profiles/认证与安全框架剖面.md) | Token/session lifecycle, authorization, adapters, stores and threat model |
| [`纯设计阶段剖面.md`](readme/rust-profiles/纯设计阶段剖面.md) | Honest README for repositories without a buildable implementation |
| [`多语言README布局剖面.md`](readme/rust-profiles/多语言README布局剖面.md) | Separate, legacy-named and single-file bilingual layouts |

## Architecture Template Family (1 + 7 profiles)

[`architecture/架构设计文档模板.md`](architecture/架构设计文档模板.md) is a 24-section architecture contract covering drivers, context, current/target state, decisions, layers, modules, runtime, flows, lifecycle, data, protocols, configuration, security, reliability, resources, deployment, observability, extensions, compatibility, validation, and delivery.

Generated outputs must be named `<Stem>-Architecture.md` or `<Stem>-Architecture.zh_CN.md`. The Chinese filename uses `zh_CN` exactly; component, profile, platform, and version qualifiers belong in `<Stem>`.

| Profile | Purpose |
|---|---|
| [`architecture/profiles/README.md`](architecture/profiles/README.md) | Selection, composition, and conflict rules |
| [`运行时与应用平台架构剖面.md`](architecture/profiles/运行时与应用平台架构剖面.md) | Technology stack, process mapping, bootstrap, concurrency, and deployment profiles |
| [`插件与扩展体系架构剖面.md`](architecture/profiles/插件与扩展体系架构剖面.md) | Extension points, manifests, lifecycle, isolation, and compatibility |
| [`边缘与嵌入式架构剖面.md`](architecture/profiles/边缘与嵌入式架构剖面.md) | Hardware budgets, autonomy, HAL, device security, OTA, and reconnect |
| [`消息与事件驱动架构剖面.md`](architecture/profiles/消息与事件驱动架构剖面.md) | Topic, Schema, ACK, ordering, idempotency, retry, DLQ, and backpressure |
| [`AI-Agent与RAG架构剖面.md`](architecture/profiles/AI-Agent与RAG架构剖面.md) | Agent main chain, deterministic boundaries, memory, RAG, tools, and evaluation |
| [`可观测性与控制面架构剖面.md`](architecture/profiles/可观测性与控制面架构剖面.md) | Telemetry, cardinality, desired/actual state, command receipts, and drift |

Read [`architecture-template-guide.md`](../references/architecture-template-guide.md) before combining the master with profiles. Preserve unique existing protocol, resource, failure, and security details when standardizing a document.

## Authoring Guidelines

- **每份文档头部必须包含** H1 标题 + `>` blockquote 文档说明 + 版本号 + 日期
- **每份文档尾部必须包含** 文档版本 / 创建日期 / 最后更新 / 文档状态
- **章节编号严格递增**：`## 1.` → `## 2.` → ...；子节使用 `### N.M`
- **表格使用 `:---` 左对齐**
- **Mermaid 图前后保留空行**
- **中英混排加空格**：`OpenAI 模型` 而非 `OpenAI模型`
- **跨文档引用使用相对路径**：`[术语表](2、{{PRODUCT_NAME}}-术语表与词汇表.md)`
- **质量以证据和可执行结果为准**，不以行数、表格数或图表数凑量
- **示例与事实分离**：完整示例保留，但必须标注；目标项目信息只能来自证据或显式假设

See [`SKILL.md`](../SKILL.md) for the complete workflow, [`structure.md`](../references/structure.md) for mappings, and [`quality-rubric.md`](../references/quality-rubric.md) for completion criteria.
