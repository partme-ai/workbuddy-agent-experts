# OCR 场景实战示例

> 这是一组"开箱即用"示例,覆盖 OCR 插件最常见的真实场景。所有示例都通过 `markitdown` 的 Python API,不是 CLI(CLI 当前未注册 `--llm-client`/`--llm-model`)。

## 场景 1 — 最简:OpenAI + gpt-4o 处理带图 PDF

```python
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(
    enable_plugins=True,
    llm_client=OpenAI(),
    llm_model="gpt-4o",
)
md.convert("annual_report_with_charts.pdf").markdown
```

## 场景 2 — 扫描 PDF(全页 OCR 回退)

```python
# 扫描件没有任何可选文本,内置转换器会输出空。
# markitdown-ocr 会自动按"无文本页"检测 → 300 DPI 整页送 LLM。
import pathlib
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(enable_plugins=True, llm_client=OpenAI(), llm_model="gpt-4o")
out = pathlib.Path("scans_md"); out.mkdir(exist_ok=True)
for pdf in pathlib.Path("scans").glob("*.pdf"):
    (out / (pdf.stem + ".md")).write_text(md.convert(str(pdf)).markdown, encoding="utf-8")
```

## 场景 3 — Azure OpenAI(企业内合规场景)

```python
import os
from markitdown import MarkItDown
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version="2024-02-01",
)
md = MarkItDown(enable_plugins=True, llm_client=client, llm_model="gpt-4o")
print(md.convert("confidential.docx").markdown)
```

## 场景 4 — PPTX 中"图像描述"优先

```python
# PPTX 转换器会先向 LLM 索要"图像描述",描述优先于 OCR 文本。
# 想强制走 OCR(只要文字不要描述),目前无法通过配置关闭——
# 需要直接修改 _pptx_converter_with_ocr.py。
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(enable_plugins=True, llm_client=OpenAI(), llm_model="gpt-4o")
md.convert("slides_with_diagrams.pptx").markdown
```

## 场景 5 — XLSX 中表格后追加图像 OCR

```python
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(enable_plugins=True, llm_client=OpenAI(), llm_model="gpt-4o")
text = md.convert("product_catalog.xlsx").markdown
# 输出长这样:
#   ## Sheet: Products
#   | SKU | Name | Price |
#   |-----|------|-------|
#   | ... | ...  | ...   |
#
#   ### Images in this sheet:
#   *[Image OCR]
#   12.5mm x 8mm, weight 250g
#   [End OCR]*
```

## 场景 6 — 用本地 vLLM / Ollama(走 OpenAI 兼容协议)

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",   # vLLM / Ollama OpenAI 兼容 endpoint
    # 本地服务通常不校验 api_key;若需传值,使用 os.environ["LOCAL_OPENAI_TOKEN"] 之类
)
from markitdown import MarkItDown
md = MarkItDown(
    enable_plugins=True,
    llm_client=client,
    llm_model="Qwen2-VL-7B-Instruct",      # 任选支持 vision 的本地模型
)
md.convert("handbook.pdf").markdown
```

## 场景 7 — 自定义 OCR Prompt(强调"只输出文字,不评论")

```python
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(
    enable_plugins=True,
    llm_client=OpenAI(),
    llm_model="gpt-4o",
    llm_prompt=(
        "You are an OCR engine. Output ONLY the literal text in the image. "
        "Preserve table layout with Markdown pipes. "
        "Do not describe, summarize, or comment."
    ),
)
md.convert("form_with_tables.pdf").markdown
```

## 场景 8 — 后处理:只保留正文,剥掉 OCR 块

```python
import re

def strip_ocr_blocks(md: str) -> str:
    # 去掉 *[Image OCR]...[End OCR]* 整段
    return re.sub(r"\*\[Image OCR\][\s\S]*?\[End OCR\]\*", "", md).strip()

text = md.convert("deck.pptx").markdown
clean = strip_ocr_blocks(text)
```

## 场景 9 — 离线/受限网络:用 HTTP 代理

```python
import httpx
from openai import OpenAI

http_client = httpx.Client(proxy="http://proxy.local:3128", timeout=60)
client = OpenAI(http_client=http_client)

from markitdown import MarkItDown
md = MarkItDown(enable_plugins=True, llm_client=client, llm_model="gpt-4o")
md.convert("doc.pdf").markdown
```

## 场景 10 — 与 RAG 流水线衔接(转完后写 ChromaDB)

```python
import pathlib
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(enable_plugins=True, llm_client=OpenAI(), llm_model="gpt-4o")
for f in pathlib.Path("kb").glob("*.pdf"):
    chunk = f"<!-- source: {f.name} -->\n" + md.convert(str(f)).markdown
    # rag.index(chunk)
```