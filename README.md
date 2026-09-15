# workbuddy-agent-experts

独立智能体库 + WorkBuddy 组团器：**智能体以独立单元存在，脚本把智能体组装成团队插件**，产出本地 marketplace 供 WorkBuddy 安装。

## 目录约定

```
agents/<id>.md     独立智能体（单一事实源）：frontmatter + 系统提示词
teams/<name>.yaml  团队定义：成员组合、人设、技能、harness 来源
skills/<name>/     随团队分发的技能包（SKILL.md + references/）
assets/logo.png    项目 logo（首次构建自动生成，可替换）
scripts/build.py   组装器：agents + teams → dist/<marketplace>/plugins/<team>/
```

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

产物：`dist/my-experts/{.codebuddy-plugin/marketplace.json, plugins/blender-production-team/}`
（执行面 harness 在构建时从 `teams/*.yaml` 的 `harness.repo` 指向的 codex-blender-plugin 检出 vendor，26 份生产技能收进 `blender-production/references/`。）

## 安装到 WorkBuddy

```bash
# my-experts 是 WorkBuddy 官方的自定义专家通道（应用源码 registerMarketplaceIfNeeded 只注册
# experts + my-experts 两个 marketplace；其余目录一律不注册）
mkdir -p ~/.workbuddy/plugins/marketplaces/my-experts/plugins
cp -R dist/my-experts/.codebuddy-plugin ~/.workbuddy/plugins/marketplaces/my-experts/
rm -rf ~/.workbuddy/plugins/marketplaces/my-experts/plugins/blender-production-team
cp -R dist/my-experts/plugins/blender-production-team ~/.workbuddy/plugins/marketplaces/my-experts/plugins/
# 重启 WorkBuddy；专家/智能体列表会经 scanCustomExperts 读 my-experts 清单列出
```

> 2026-09-15 源码级结论（app.asar 反解）：注册名单硬编码 `experts` + `my-experts`；
> `my-experts/.codebuddy-plugin/marketplace.json` 必须存在且列出插件，否则 scanCustomExperts
> 返回空；无 `experts/custom/<userId>/experts.json` 白名单文件时全部列出。

## 已有团队

| 团队 | 成员 | 插件 |
|---|---|---|
| Blender 3D 生产专家团 | 岚一(主理)/塑岩/骨风/彩澜/影流/核真 | blender-production-team@my-experts |

## 新增一个智能体 / 一个团队

- **加智能体**：`agents/<id>.md` 按上述格式写好即可（独立存在，可被任意团队引用）。
- **加团队**：复制 `teams/3d-production.yaml` 改成员与来源，`python3 scripts/build.py` 后按上节安装。
