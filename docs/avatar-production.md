# WorkBuddy 专家头像生产规范

本规范用于 `workbuddy-agent-experts` 中全部团队与单专家的主图、团队图和成员头像生产。
事实依据为仓库内保存的 WorkBuddy 官方规范与官方内容创作团队样本：

- `docs/workbuddy-official/avatar-spec.md`
- `docs/workbuddy-official/team-spec.md`
- `docs/workbuddy-official/ai-content-creator-team/`

## 资产契约

### 团队插件

- 团队主图：`teams/<team-id>/logo.png`
- 成员头像：`teams/<team-id>/avatars/<agent-id>.png`
- 构建产物：`experts/plugins/<team-id>/avatars/`

### 单专家插件

- 单专家主图从对应 Agent MD 的身份、能力、工作方式和领域元素生成。
- 构建产物保持 `avatars/expert.png` 契约。

## 视觉规则

1. 团队主图必须表现多人真实协作场景，不能使用抽象徽章代替。
2. 成员头像必须是正面半身职业人物，职业道具和背景元素取自对应 Agent MD。
3. 同组统一漫画笔触、轮廓、暖光、柔影、背景主色和环境语言。
4. 同组成员通过人物外观、服装、姿态、道具和专业背景区分。
5. 团队图与成员图的重要人物和道具必须处于圆形安全区。
6. 不生成文字、字母、数字、商标、水印或不可读的界面文本。
7. 不根据 Agent ID 武断推断性别；以角色设定为准，未指定时保持团队成员多样性。

## 分类色系

| categoryId | 主色系 |
|---|---|
| 01-ProductDesign | 暖橙、珊瑚 |
| 02-Engineering | 蓝、靛青、紫，少量琥珀高光 |
| 03-GameSpatial | 紫、红渐变 |
| 04-DataAI | 青、蓝绿 |
| 05-MarketingGrowth | 红、橙 |
| 06-ContentCreative | 粉、洋红 |
| 07-SalesCommerce | 金、琥珀 |
| 08-FinanceInvestment | 深蓝、金色强调 |
| 09-OperationsHR | 海军蓝、灰蓝 |
| 10-ProjectQuality | 绿色、祖母绿 |
| 11-SecurityCompliance | 深灰蓝、冷青 |
| 12-IndustryConsultant | 深青、银色强调 |

同一分类中的不同团队必须调整明度、辅助色与场景，避免视觉混淆；同一团队不得跨色系漂移。

## 生成流程

1. 读取 `plugin.json` 的团队描述、分类、成员和头像文件名。
2. 逐个读取成员 Agent MD，不使用只有职业名的通用 Prompt。
3. 为团队建立一份固定的风格锚点：色板、光线、笔触、环境和人物多样性。
4. 先生成团队主图，再把通过审查的团队图作为所有成员头像的图像参考。
5. 每个成员单独生成，保持团队风格锚点，只改变角色身份与职业元素。
6. 生成源使用 1024x1024；验收后缩放为 512x512 PNG，并控制在 500KB 内。
7. 写入源资产目录后重新执行构建，检查 `plugin.json` 引用的所有头像均存在。

## 验收门禁

- 文件名和 manifest 完全一致。
- 正方形、512x512、PNG/JPG、单文件不超过 500KB。
- 32px 圆形裁切下人物身份仍可辨识。
- 团队图能看出协作，而不是多人合影或人物拼贴。
- 成员图与团队图属于同一画风和色系。
- 角色的核心职业元素能从 Agent MD 找到来源。
- 无乱码、伪文字、商标、水印和敏感内容。

## 非覆盖式评审

新一轮设计先保存为 `logo-v2.png` 和 `<agent-id>-v2.png`。通过视觉审查后，再明确替换正式文件。这样可以保留旧资产并支持逐团队回滚。
