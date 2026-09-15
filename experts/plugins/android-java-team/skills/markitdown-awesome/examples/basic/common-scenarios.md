# 常见场景示例

> 这些示例展示"用 MarkItDown 解决日常问题"的标准写法。
> 涉及到具体 CLI 参数时,跳到兄弟 Skill `markitdown-cli`;涉及到 OCR 时,跳到 `markitdown-ocr`。

## 场景 1 — 把一整个目录的 PDF 转 Markdown 后喂给 LLM

```python
import pathlib
from markitdown import MarkItDown

md = MarkItDown()  # 默认:内置开启 + 插件关闭
out_dir = pathlib.Path("out_md")
out_dir.mkdir(exist_ok=True)

for pdf in pathlib.Path("inbox").glob("*.pdf"):
    result = md.convert_local(str(pdf))
    (out_dir / (pdf.stem + ".md")).write_text(result.markdown, encoding="utf-8")
```

## 场景 2 — 通过 HTTP(S) URL 抓取并转换(限制目标域名)

```python
from markitdown import MarkItDown

md = MarkItDown()
# convert_uri 会自动发起 GET,内部默认 Accept 头为 text/markdown, text/html;q=0.9, …
result = md.convert_uri("https://example.com/article.html")
print(result.markdown)
```

⚠️ 生产环境请自行用 `requests.get()` + `convert_response()`,避免把 SSRF 风险直接交给 MarkItDown。

## 场景 3 — 把 `data:` URI(Base64 内嵌文件)转 Markdown

```python
from markitdown import MarkItDown

md = MarkItDown()
data_uri = "data:application/pdf;base64,JVBERi0xLjQKJ..."
result = md.convert_uri(data_uri)
print(result.markdown)
```

## 场景 4 — 处理 `requests.Response` 对象(完全控制 HTTP)

```python
import requests
from markitdown import MarkItDown

resp = requests.get(
    "https://example.com/whitepaper.pdf",
    timeout=15,
    headers={"User-Agent": "my-rag/1.0"},
)
resp.raise_for_status()

md = MarkItDown()
result = md.convert_response(resp)
print(result.markdown)
```

## 场景 5 — 让 Azure Document Intelligence 接管 PDF/扫描件

```python
import os
from markitdown import MarkItDown

md = MarkItDown(docintel_endpoint=os.environ["DOCINTEL_ENDPOINT"])
result = md.convert_local("scan.pdf")
print(result.markdown)
```

更多 Azure 后端示例见 `markitdown-cli` 的 "Azure 后端" 一节。

## 场景 6 — 优雅地处理"缺依赖 / 不支持的格式"

```python
from markitdown import MarkItDown
from markitdown._exceptions import (
    MissingDependencyException,
    UnsupportedFormatException,
    FileConversionException,
)

md = MarkItDown()
for f in ["a.pptx", "b.xyz", "c.pdf"]:
    try:
        print(f"=== {f} ===")
        print(md.convert_local(f).markdown[:500])
    except MissingDependencyException as e:
        print(f"[依赖缺失] {e} → pip install 'markitdown[对应特性]'")
    except UnsupportedFormatException:
        print(f"[不支持] {f} 不是已知格式")
    except FileConversionException as e:
        print(f"[转换失败] {e}")
```

## 场景 7 — 用 `StreamInfo` 提示类型(从 stdin/字节流读取时)

```python
import io
from markitdown import MarkItDown, StreamInfo

raw = io.BytesIO(open("unknown_blob", "rb").read())
md = MarkItDown()
result = md.convert_stream(raw, stream_info=StreamInfo(mimetype="application/pdf"))
print(result.markdown)
```

## 场景 8 — 让 markitdown-ocr 插件接管 PDF/DOCX/PPTX/XLSX 的图像 OCR

详见兄弟 Skill `markitdown-ocr`。简短预览:

```python
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(enable_plugins=True, llm_client=OpenAI(), llm_model="gpt-4o")
print(md.convert_local("scanned_with_images.pdf").markdown)
```