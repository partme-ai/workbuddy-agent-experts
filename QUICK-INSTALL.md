# WorkBuddy 智能体专家团 — 快速安装

**55 个插件**：39 个专家团（语言开发 / 情报调研 / 内容生产 / QA·DevOps / 设计…）+ 16 个单专家。

## 安装（三选一）

**① macOS 安装器（推荐，双击图形化安装）**

下载 Release 的 `WorkBuddy-Experts-v1.0.0.pkg` → 双击 → 继续 → 安装 → 重启 WorkBuddy。
未签名 pkg 首次打开如遇"无法验证开发者"：系统设置 → 隐私与安全性 → 仍要打开（仅首次）。

**② Windows / zip**

```bash
unzip workbuddy-agent-experts-v1.0.0.zip && cd workbuddy-agent-experts-v1.0.0
.\install.ps1            # Windows PowerShell
bash install.sh          # macOS / Linux（需 Python 3.8+）
```

**② clone 仓库安装（可 git pull 更新）**

```bash
git clone https://github.com/partme-ai/workbuddy-agent-experts.git
cd workbuddy-agent-experts && bash install.sh
```

**③ 从源码构建（需要同级克隆技能仓，见仓库 README）**

```bash
python3 scripts/build.py && bash install.sh
```

安装完成 → **重启 WorkBuddy**（或重开专家选择器）→ 专家列表出现 `my-experts` 分组。

## 卸载

- macOS：双击 `/Library/Application Support/WorkBuddyExperts/卸载专家团.command`
- 通用：`python3 scripts/install.py --uninstall`

只移除本包安装的插件，不动其他数据。

## 图标

每个团队插件自带圆角图标（`avatars/team.png`），成员各有配色头像。想换官方图标：
把自定义 PNG 放到仓库 `teams/<团队id>/logo.png` 后重新构建，或直接替换
`~/.workbuddy/plugins/marketplaces/my-experts/plugins/<团队id>/avatars/team.png`。

## 系统要求

- WorkBuddy（桌面版）
- 安装脚本仅需 Python 3.8+（macOS/Linux 自带）；Windows 用 PowerShell 脚本
