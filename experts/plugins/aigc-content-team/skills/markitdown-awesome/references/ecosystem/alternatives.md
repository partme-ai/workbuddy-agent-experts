# 替代品与生态对比

> 当用户在 markitdown / textract / unstructured / pandoc 之间犹豫时,给出客观对比与选型建议。

| 工具 | 强项 | 弱项 | 何时选它 |
|------|------|------|---------|
| **MarkItDown** | 输出 Markdown 保留结构;插件生态;Python API 简洁 | 对扫描件/复杂排版需外部后端(DI/CU/LLM) | **默认选它**:RAG 预处理、给 LLM 喂文档、Office→MD |
| **textract** | 文本抽取纯干净,跨平台稳定性强 | 不保留结构(纯文本);包大 | 只想拿正文,不关心表格/标题 |
| **unstructured** | 元素级 API(标题/段落/列表分块),自动分块 | 学习曲线略高;体积大 | 已经用 unstructured 生态、需要元素级粒度 |
| **pandoc** | 文档格式互转之王(几十种格式) | OCR 不是它的菜;某些格式转换有边角差异 | 想在 DOCX↔MD↔LaTeX 之间多向转换 |
| **docling** (IBM) | 学术论文级 PDF 解析 | Python-only,生态较小 | 论文级 PDF 解析、表格复杂还原 |
| **Azure Document Intelligence** | 云端高质量 OCR + 表格抽取 | 需 Azure 订阅;按页计费 | 大量扫描件/表格;愿意花钱买质量 |
| **Azure Content Understanding** | 多模态(文档/图像/音频/视频)+ 结构化字段 | 同上 | 需要 YAML front matter、结构化分析器 |

## 选型决策树

```
Q1:文档是不是扫描件/图片为主?
 ├─ 是 → 看预算与云:
 │     ├─ 预算足 + Azure → Azure Document Intelligence
 │     ├─ 预算足 + 多模态 → Azure Content Understanding
 │     └─ 想省钱或本地化 → markitdown + markitdown-ocr
 └─ 否 → Q2

Q2:你主要想要 Markdown 还是纯文本?
 ├─ Markdown → markitdown(默认)
 └─ 纯文本 → textract

Q3:需要在多种文档格式(Word/MD/LaTeX/EPUB)间互转?
 └─ 是 → pandoc
```

## 何时**不要**用 MarkItDown

- 需要像素级保真(请走 OCR + PDF 渲染)
- 想读 Excel 复杂公式/宏(请用 openpyxl/pandas 直接读)
- 需要把 PDF 反向转回 Word(请走 pandoc + LaTeX 中介)
- 处理二进制协议(Protobuf/Parquet 等)

## 与 LangChain / LlamaIndex 的集成

两者都有 `MarkItDownLoader` / 自定义 Document Loader 包装,直接把 `MarkItDown().convert(...)` 喂给它们的 `Document` 对象即可。具体 API 随版本变化,以各自文档为准。