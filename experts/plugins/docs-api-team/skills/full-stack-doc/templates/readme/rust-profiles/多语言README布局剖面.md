# Rust README 剖面：多语言 README 布局

> 用于在单文件双语、双文件双语和主文件加翻译文件之间选择一致、可维护的 README 结构。

## 先选择一种模式

| 模式 | 文件布局 | 适用场景 | 主要风险 |
|---|---|---|---|
| A：标准双文件 | `README.md` + `README.zh-CN.md` | 两种语言都需要完整独立阅读 | 内容漂移 |
| B：兼容现有命名 | `README.md` + `README_CN.md`/`README_zh.md` | 已有外部链接依赖旧文件名 | 命名不统一 |
| C：单文件双语 | 一个 `README.md` 内含两种语言 | 内容短、维护者希望单文件同步 | 文件过长、锚点复杂 |
| D：主语言完整 + 翻译摘要 | 主 README 完整，另一文件摘要 | 维护资源有限 | 两种语言信息不等价 |

对于完整技术项目优先 A；已有成熟仓库优先保留 B，避免无理由重命名破坏外链；只有内容确实较短时使用 C。D 必须明确摘要范围，不能假装完全等价。

## 模式 A：标准双文件

```text
README.md
README.zh-CN.md
```

两个文件保持相同顶级章节顺序。语言导航使用真实相对路径：

```markdown
[English](README.md) | [简体中文](README.zh-CN.md)
```

## 模式 B：兼容现有命名

```text
README.md
README_CN.md
```

或：

```text
README.md
README_zh.md
```

README 模板必须使用实际文件名。若要迁移到 `README.zh-CN.md`：

1. 检索仓库内外可控链接；
2. 更新 Cargo manifest、网站、包注册表和文档链接；
3. 在旧文件保留迁移提示或兼容链接（如果发布环境允许）；
4. 验证 Git 大小写和跨平台行为；
5. 不为了统一命名破坏已有链接。

## 模式 C：单文件双语

```markdown
# Project

[English](#english) | [中文](#中文)

<a id="english"></a>
## English

...

<a id="中文"></a>
## 中文

...
```

不要把每句话写成“英文 / 中文”混排；以完整语言区块组织，代码和事实表可以复用或通过锚点引用。

## 双语一致性契约

以下内容必须逐字符或语义一致：

- crate、模块、feature 和配置键；
- 版本、MSRV、Edition、Resolver 和目标平台；
- 安装、构建、测试和发布命令；
- 功能成熟度、兼容矩阵和安全边界；
- URL、相对路径、许可证和安全联系方式；
- 代码示例及预期输出。

解释性语言可以翻译，但不得让一个语言版本宣称更多已实现能力。

## 同步表

| English section | 中文章节 | Commands identical | Status identical | Links checked |
|---|---|:---:|:---:|:---:|
| Overview | 项目定位 | — | ✅ | ✅ |
| Quick Start | 快速开始 | ✅ | ✅ | ✅ |
| Compatibility | 兼容性 | ✅ | ✅ | ✅ |
| Security | 安全 | — | ✅ | ✅ |

## 自动检查建议

- 提取两份 README 的 H2 章节并检查映射；
- 比较所有 fenced code block 中的命令；
- 比较 crate 名、版本、feature、配置键和 URL；
- 分别验证相对链接与锚点；
- 检查语言导航目标实际存在；
- 生成脚本重复运行第二次应无变化。

## README 完成检查

- [ ] 选择了明确的语言布局模式
- [ ] 语言导航与真实文件名一致
- [ ] 现有非标准翻译文件名没有被意外破坏
- [ ] 两种语言的结构、命令、状态和安全边界一致
- [ ] 单文件双语没有逐句混排造成不可读内容
- [ ] 两份 README 的链接分别验证
