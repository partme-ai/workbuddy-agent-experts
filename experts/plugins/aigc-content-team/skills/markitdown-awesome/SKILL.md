---
name: markitdown-awesome
description: 介绍 MarkItDown(Microsoft 出品的"万物转 Markdown"工具)的能力边界、支持格式、生态(CLI / Python API / 插件 / Docker / Azure 集成),并负责引导 LLM 在面对"把 PDF/PPT/Word/Excel/图片/音频/网页/YouTube 转成 Markdown"这类需求时,正确判断是用 markitdown-awesome 概览、markitdown-cli 命令指导、还是 markitdown-ocr 走 LLM Vision OCR 路径。当用户提到 markitdown、microsoft/markitdown、把 Office 文档转 markdown、把扫描件 OCR 出来、或询问相关替代品(textract、unstructured、pandoc)时,使用本 skill。
license: MIT
---

# MarkItDown — Awesome Overview

> 入口型 Skill:讲清楚 MarkItDown 是什么、解决什么问题、有哪些子能力,以及"下一步该跳到哪个 Skill"。

**离线基线**:基于 [microsoft/markitdown](https://github.com/microsoft/markitdown) 仓库 main 分支(2026-08 时刻)。任何"是否支持某格式 / 某参数是否还存在"的问题,以下方 [官方仓库 README](https://github.com/microsoft/markitdown) 与 [官方 PyPI](https://pypi.org/project/markitdown/) 为最终权威。

---

## When to Use This Skill

✅ **什么时候用本 skill**(只读概览、导航型问题):
- 用户想了解 "MarkItDown 是什么?支持哪些格式?架构长啥样?"
- 用户在多个工具之间二选一:markitdown / textract / unstructured / pandoc / docling
- 用户刚装好 markitdown,需要先理解整体架构再决定细节
- 用户询问"如何自己写一个 MarkItDown 插件 / 自定义 DocumentConverter"
- 用户问 Azure Document Intelligence vs Content Understanding 的区别

❌ **什么时候不该用本 skill**(交给兄弟 Skill):
- 具体 CLI 命令怎么拼、参数怎么传 → `markitdown-cli`
- 嵌入图片 OCR、扫描 PDF 处理、LLM Vision 配置 → `markitdown-ocr`
- 用户明确说"我已经知道要用 markitdown,只想跑一条命令" → `markitdown-cli`

⚠️ **模糊地带**:
- 用户问"OCR 怎么做"但没说是不是图片 → 先用 `markitdown-ocr` 判断;如果只是普通 PDF 转 MD 失败,回退到 `markitdown-cli` 的"-d/--use-docintel"。

---

## Workflow

按以下顺序回答用户的"概览/选型/导航"问题:

### Step 1 — 确认用户目标(分类)

- A 类:**"这是什么"** 类(能力、定位、架构)→ 跳到 §1–§4
- B 类:**"怎么选"** 类(对比其它工具)→ 跳到 §5 + [ecosystem/alternatives.md](references/ecosystem/alternatives.md)
- C 类:**"怎么用"** 类(具体 API/命令)→ 转交 `markitdown-cli`
- D 类:**"OCR / 图像"** 类 → 转交 `markitdown-ocr`

### Step 2 — 提供对应章节

- A 类 → 给出 §1 一句话定位 + §2 支持格式表 + §3 三路径决策树
- B 类 → 给出 [ecosystem/alternatives.md](references/ecosystem/alternatives.md) 决策树 + 推荐
- C/D 类 → 直接给出兄弟 Skill 的入口链接,不再展开

### Step 3 — 给出"下一步跳哪儿"

| 用户原话 | 下一步 Skill |
|---------|-------------|
| "好,我要装 + 跑命令" | `markitdown-cli` |
| "我要扫描件 / 嵌入图片 OCR" | `markitdown-ocr` |
| "我要批量入库 RAG" | `markitdown-cli` + 自己写 Python 循环(参见 [advanced/batch-rag-pipeline.md](examples/advanced/batch-rag-pipeline.md)) |
| "我想写自定义转换器" | 读 [api/converter-lifecycle.md](references/api/converter-lifecycle.md) |

### Step 4 — 收尾:官方资料回链

任何"参数是否还存在"的疑问,以 [官方仓库 README](https://github.com/microsoft/markitdown) 为准;本 skill 的内容是离线基线快照,不应被视为权威最终来源。

### Step 5 — 安全检查

每次涉及 URL / data URI / 文件路径,**先回顾 §6 安全注意**,提示用户避免 SSRF 与未授权路径访问。

### Step 6 — 隐私声明

对外输出前,在回复末尾附"本 Skill 不收集、存储或传输任何用户数据"。

---

## Validation(自检清单)

每次回答前对照检查:

- [ ] 我给出的命令 / 参数是否仍存在于 `__main__.py` argparse?
- [ ] 我给出的 API 是否对应 `_markitdown.py` 中存在的方法?
- [ ] 我有没有混用两个互斥后端(`docintel_*` 与 `cu_*`)?
- [ ] 如果推荐了"某可选特性",是否同时给出 `pip install 'markitdown[特性]'`?
- [ ] 如果用户传入的是 URL,有没有提醒 SSRF 风险?
- [ ] 如果用户的文件包含敏感内容,有没有提醒走私有化后端?

---

## Gotchas

新手最容易踩的坑,按命中频率从高到低:

1. **插件默认关闭** — `MarkItDown()` 不写 `enable_plugins=True`,`markitdown-ocr` 等插件不会生效;但 `--list-plugins` 仍能列出已装的插件。**务必确认 `enable_plugins=True` 或 CLI `-p`**。
2. **`--list-plugins` 与"转文件"互斥** — `__main__.py` 列出插件后立即 `sys.exit(0)`,所以"列出 + 转换"必须在两条命令里分两次跑。
3. **可选依赖未装就报 `MissingDependencyException`** — 看到 "dependencies needed" 字样就是少装 extras;按格式 `pip install 'markitdown[特征]'` 补齐。
4. **CLI 暂无 `--llm-client` / `--llm-model`** — 想从命令行启用 OCR,必须写一个 Python 包装(见 `markitdown-ocr` skill 的 CLI 章节)。
5. **HTTP URL 直接传 `convert()` 会触发真实 GET** — `convert_uri("https://…")` 默认用内置 `requests.Session`;生产环境务必先 `requests.get()` 自管,然后 `convert_response()`。
6. **`file:` URI 不支持非本机 netloc** — `convert_uri("file://server/share/x.pdf")` 会直接抛 `Unsupported file URI` 异常;先把文件 `cp` 到本机。
7. **Azure Document Intelligence 与 Content Understanding 互斥** — 同时传 `docintel_endpoint=` 与 `cu_endpoint=` 会让后者覆盖前者(`__main__.py` 的 `argparse` mutually_exclusive_group)。
8. **PPTX/DOCX 内嵌图片的 OCR 不会自动跑** — 必须装 `markitdown-ocr` 插件并配 `llm_client` + `llm_model`,详见 `markitdown-ocr`。
9. **转换大 PDF 时内存峰值高** — `convert_local` 一次性 `open(path, "rb")` 读全部;`convert_stream` 走 4 KiB chunk 缓冲。如果内存敏感,自己分块读 + 多次 `convert_stream`。
10. **CLI 输出中文乱码** — 终端 `LANG` 不是 UTF-8 时,用 `-o out.md` 而非 stdout 落盘。

---

## 1. 一句话定位

**MarkItDown** 是一个用 Python 编写的轻量级工具,把各类文件与 Office 文档转成结构化 Markdown,目标是"喂给 LLM 之前先做一次干净的结构化"。定位类似 `textract` / `unstructured`,但**优先保留语义结构(标题、列表、表格、链接)** 而不是输出纯文本。

适合:RAG 预处理、给 LLM 喂文档、构建可搜索的知识库、长上下文整理。
**不适合**:需要像素级保真的渲染、需要 OCR 高保真还原扫描件排版(用专门的 OCR 后端)。

## 2. 核心能力与支持格式

| 类别 | 具体格式 | 内置转换器 |
|------|---------|-----------|
| Office 文档 | PDF、PowerPoint(.pptx)、Word(.docx)、Excel(.xlsx/.xls) | `_pdf_converter.py` / `_pptx_converter.py` / `_docx_converter.py` / `_xlsx_converter.py` |
| 媒体 | 图片(EXIF + 可选 LLM 图注)、音频(wav/mp3,需可选依赖) | `_image_converter.py` / `_audio_converter.py` |
| 网页与文本 | HTML、CSV、JSON、XML、纯文本、RSS、Wikipedia、Bing SERP、YouTube URL | `_html_converter.py` / `_csv_converter.py` / `_youtube_converter.py` … |
| 压缩/电子书 | ZIP(迭代展开)、EPUB、Outlook .msg、Jupyter .ipynb | `_zip_converter.py` / `_epub_converter.py` / `_outlook_msg_converter.py` / `_ipynb_converter.py` |

**安装可选依赖**:
```bash
pip install 'markitdown[all]'                 # 全部
pip install 'markitdown[pdf,docx,pptx]'        # 按需
pip install 'markitdown[az-doc-intel]'        # Azure Document Intelligence
pip install 'markitdown[az-content-understanding]'  # Azure Content Understanding
```

可选特性键的完整列表见 [ecosystem/optional-features.md](references/ecosystem/optional-features.md)。

## 3. 三条使用路径(快速决策树)

```
要把"某种文件"转成 Markdown ──┐
                              │
        ┌─────────────────────┼──────────────────────┐
        ▼                     ▼                      ▼
   只想跑 CLI 命令      想嵌入 Python 代码         文件里有图片要 OCR
   ──────────────      ──────────────────         ─────────────────
   ↓ 跳到 markitdown-cli  ↓ 用 MarkItDown() 类    ↓ 跳到 markitdown-ocr
     命令/参数/管道/插件    convert() / convert_stream()
                          / convert_uri() / convert_local()
```

**何时使用本 skill(只读概览)**:
- 用户想了解"MarkItDown 能做什么、不能做什么"
- 用户在多个工具之间二选一(markitdown vs textract vs unstructured vs pandoc)
- 用户刚装好 markitdown,需要先理解整体架构再决定细节
- 用户询问"如何自己写一个 MarkItDown 插件"

**何时跳到兄弟 Skill**:
| 用户诉求 | 跳到 |
|---------|------|
| "markitdown 命令怎么用?参数是啥?管道怎么传?" | `markitdown-cli` |
| "PDF/PPT 里嵌入的扫描图片怎么 OCR?"、"怎么集成 GPT-4o 做 OCR?" | `markitdown-ocr` |
| "我要自己写 markitdown 插件" | 直接读 [官方插件示例](https://github.com/microsoft/markitdown/tree/main/packages/markitdown-sample-plugin) + `_base_converter.py` |

## 4. 架构概览(供 LLM 在生成代码时正确选择 API)

源码核心包:[`packages/markitdown/src/markitdown/`](https://github.com/microsoft/markitdown/tree/main/packages/markitdown/src/markitdown)

```
markitdown/
├── __init__.py         # 暴露 MarkItDown / DocumentConverter / 异常 / 优先级常量
├── _markitdown.py      # 核心类 MarkItDown(注册表、转换分发、插件加载)
├── _base_converter.py  # DocumentConverter 基类 + DocumentConverterResult
├── _stream_info.py     # StreamInfo(mimetype/extension/charset/filename/…)
├── _exceptions.py      # MarkItDownException / MissingDependencyException / …
├── __main__.py         # CLI 入口(argparse)
└── converters/         # 25 个内置转换器(每个文件一个)
```

**两个核心常量**(优先级数字越小越先尝试):
```python
PRIORITY_SPECIFIC_FILE_FORMAT = 0.0   # 精确格式: .docx / .pdf / .xlsx …
PRIORITY_GENERIC_FILE_FORMAT  = 10.0  # 兜底: 文本类、HTML 类
```
插件可以用负数优先级(如 markitdown-ocr 用 `-1.0`)"插队"到内置转换器之前。

**主入口 `MarkItDown` 类**的关键方法(详见 [api/python-api.md](references/api/python-api.md)):

| 方法 | 输入 | 场景 |
|------|------|------|
| `convert(source)` | str/Path/Response/BinaryIO | 自动判断本地路径 vs URI |
| `convert_local(path)` | 本地文件 | 最安全,不发起任何网络请求 |
| `convert_stream(stream, stream_info=…)` | BinaryIO + StreamInfo | 内存/管道流 |
| `convert_uri(uri)` | `file:` / `data:` / `http(s):` URI | 远程资源 |
| `convert_url(url)` | HTTP(S) URL | `convert_uri` 的别名 |
| `convert_response(response)` | `requests.Response` | 自己控制 HTTP 请求 |
| `register_converter(converter, priority=…)` | DocumentConverter | 注册自定义/插件 |

每个 `convert*` 返回 `DocumentConverterResult(text_content=…, markdown=…)`,**默认属性 `markdown` 是真正的 Markdown 字符串**;`text_content` 在多数转换器中与 `markdown` 一致,但插件可以只填 `text_content`。

## 5. 三种"增强后端"对比(决定 OCR/复杂 PDF 走哪条路)

| 后端 | 启用方式 | 适用场景 | 限制 |
|------|---------|---------|------|
| **Azure Document Intelligence** | `MarkItDown(docintel_endpoint=…)` / CLI `-d -e <endpoint>` | 高质量 PDF/扫描件、表格抽取 | 需 Azure 订阅、按页计费 |
| **Azure Content Understanding** | `MarkItDown(cu_endpoint=…)` / CLI `--use-cu --cu-endpoint <endpoint>` | 多模态(文档/图像/音频/视频)、结构化字段、自动选 analyzer | 需 Azure 订阅;`--cu-analyzer` 可自定义 |
| **LLM Vision(本地/OpenAI 兼容)** | `MarkItDown(llm_client=…, llm_model="gpt-4o")` 或装 `markitdown-ocr` 插件 | 图内文字、扫描 PDF、跨云灵活 | 按 token 计费、需可用 vision 模型 |

Azure Document Intelligence 与 Content Understanding 是**互斥**的(`__main__.py` 用 `mutually_exclusive_group` 强制);LLM Vision 与它们正交,可叠加。

## 6. 安全注意(必读)

MarkItDown 以**当前进程权限**执行 I/O。三条最小化攻击面的建议:

1. **净化输入**:不要把不受信任的路径直接交给 `convert()`,否则可能触发 `http(s):`、`file:` URI。
2. **限制访问**:如需处理 URL,自行用 `requests.get()` 拿响应后调 `convert_response()`。
3. **使用最窄 API**:
   - 只要本地文件 → `convert_local()`
   - 需要 URI 控制 → `convert_response()`
   - 完全控制字节流 → `convert_stream()`

## 7. 何时使用本 Skill(完整触发清单)

✅ 适用:
- "MarkItDown 是什么?支持哪些格式?"
- "markitdown、textract、unstructured、pandoc 怎么选?"
- "我想写一个 MarkItDown 插件,该看哪些文件?"
- "Azure Document Intelligence 和 Content Understanding 有什么区别?"
- "我要在 RAG 流水线里把 PDF 转 Markdown,有什么坑?"

❌ 不适用(交给兄弟 Skill):
- 具体 CLI 命令怎么拼、参数怎么传 → `markitdown-cli`
- 嵌入图片 OCR、扫描 PDF 处理、LLM Vision 配置 → `markitdown-ocr`
- 我已经知道要用 markitdown,只是想跑一条命令 → `markitdown-cli`

## 8. 离线示例代码(默认 Base API)

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=False)
result = md.convert("report.pdf")
print(result.markdown)
```

```python
# 安全模式:只允许本地文件,不发起任何网络请求
md = MarkItDown(requests_session=None)  # 但注意 requests_session 默认非 None
md_local = md.convert_local("report.pdf")
print(md_local.markdown)
```

更深入的 Python API 模式见 [api/python-api.md](references/api/python-api.md);
常见场景示例(批处理、URL 抓取、错误处理)见 [basic/common-scenarios.md](examples/basic/common-scenarios.md);
Docker/CI 集成见 [integration/docker-usage.md](examples/integration/docker-usage.md);
RAG 批量入库见 [advanced/batch-rag-pipeline.md](examples/advanced/batch-rag-pipeline.md);
首次上手 5 步走见 [basic/first-conversion.md](examples/basic/first-conversion.md)。

## 9. 官方资料(每次回答前都应交叉核对)

- 仓库 README: <https://github.com/microsoft/markitdown>
- PyPI: <https://pypi.org/project/markitdown/>
- OCR 插件 README: <https://github.com/microsoft/markitdown/blob/main/packages/markitdown-ocr/README.md>
- 插件示例: <https://github.com/microsoft/markitdown/tree/main/packages/markitdown-sample-plugin>
- MCP 服务端: <https://github.com/microsoft/markitdown/tree/main/packages/markitdown-mcp>

## 10. 隐私策略

本 Skill 仅提供本地知识、文档引用与代码示例,**不收集、存储或传输任何用户数据**。访问上述 GitHub/PyPI 链接需遵守用户网络访问要求。