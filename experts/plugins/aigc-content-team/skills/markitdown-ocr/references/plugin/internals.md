# markitdown-ocr 插件内部机制

> 给"想理解/修改/扩展插件"的读者。本文档基于 [`packages/markitdown-ocr/`](https://github.com/microsoft/markitdown/tree/main/packages/markitdown-ocr) main 分支源码。

## 1. 入口点发现

`packages/markitdown-ocr/pyproject.toml`:

```toml
[project.entry-points."markitdown.plugin"]
ocr = "markitdown_ocr"
```

MarkItDown 通过 `importlib.metadata.entry_points(group="markitdown.plugin")` 拿到 `markitdown_ocr` 模块,然后**自动调用模块级的 `register_converters(markitdown_instance, **kwargs)`**。

## 2. `register_converters(markitdown, **kwargs)`

```python
def register_converters(markitdown: MarkItDown, **kwargs):
    llm_client = kwargs.get("llm_client")
    llm_model  = kwargs.get("llm_model")
    llm_prompt = kwargs.get("llm_prompt")

    ocr_service = None
    if llm_client and llm_model:
        ocr_service = LLMVisionOCRService(
            client=llm_client, model=llm_model, default_prompt=llm_prompt,
        )

    PRIORITY_OCR_ENHANCED = -1.0   # 负数 → 先于内置 (0.0) 试用

    markitdown.register_converter(PdfConverterWithOCR(ocr_service=ocr_service),  priority=-1.0)
    markitdown.register_converter(DocxConverterWithOCR(ocr_service=ocr_service), priority=-1.0)
    markitdown.register_converter(PptxConverterWithOCR(ocr_service=ocr_service), priority=-1.0)
    markitdown.register_converter(XlsxConverterWithOCR(ocr_service=ocr_service), priority=-1.0)
```

要点:
- **`ocr_service is None` 时也能注册**——只是 OCR 阶段会被静默跳过。
- 优先级 `-1.0` 比内置 `0.0` 小,因此 `accepts()` 一旦命中就抢在前面。

## 3. `LLMVisionOCRService`

```python
class LLMVisionOCRService:
    def __init__(self, client, model, default_prompt=None):
        self.client = client
        self.model  = model
        self.default_prompt = default_prompt or (
            "Extract all text from this image. "
            "Return ONLY the extracted text, maintaining the original "
            "layout and order. Do not add any commentary or description."
        )

    def extract_text(self, image_stream, prompt=None, stream_info=None, **kwargs):
        # 1) 推断 content_type: stream_info.mimetype → PIL 探测 → "image/png"
        # 2) image_stream.read() → base64 → data URI
        # 3) 调用 client.chat.completions.create(...)
        # 4) 返回 OCRResult(text=..., backend_used="llm_vision")
        # 任何异常都被捕获并返回 OCRResult(text="", error=str(e))
```

要点:
- 用 `chat.completions.create(messages=[{role:user, content:[{type:text},{type:image_url, image_url:{url:data_uri}}]}])` 协议。
- 任何客户端只要实现这个调用形态 + 支持 vision 就能用。
- 异常**不会**抛到上层,而是被压成 `OCRResult(error=...)`。

## 4. 四个 with-OCR 转换器要点

### `_pdf_converter_with_ocr.py`
- 用 `page.images` / page XObjects 取嵌入图像,按**垂直位置**插回。
- 检测"无文本页"则**整页渲染 300 DPI 后整页送 LLM**——这是扫描件的处理路径。
- 失败时 fallback 到 PyMuPDF 整页渲染重试。

### `_docx_converter_with_ocr.py`
- OCR 在 "DOCX→HTML→Markdown" 流水线之前执行,确保 HTML→MD 阶段不会破坏流。
- 通过 `doc.part.rels` 取图片关系。

### `_pptx_converter_with_ocr.py`
- 按 `top, left` 排序处理图片、placeholder、组内图片。
- 若 LLM 返回"图像描述"则优先用描述;OCR 仅作 fallback。

### `_xlsx_converter_with_ocr.py`
- 从图像 anchor 推算 `A1`/`B3` 等列字母/行号。
- 每张工作表的图片**统一放在数据表后**(`### Images in this sheet:` 段),不与行交错。

## 5. 输出格式契约

```
*[Image OCR]
<extracted text>
[End OCR]*
```

这一对包裹标记是公开契约,所有四个 with-OCR 转换器都遵守。后处理可以靠它剥离/保留 OCR 块。

## 6. 二次开发 checklist

如果想 fork/修改:

1. 修改 `_plugin.py` 的 `register_converters` 优先级(数值越小越先)。
2. 修改 `_ocr_service.py::extract_text` 可换协议(比如 Anthropic / Gemini 原生 SDK)。
3. 修改各 `_xxx_converter_with_ocr.py` 时保持"输出契约"(`*[Image OCR]…[End OCR]*`)——否则后处理脚本全失效。
4. 加新格式(例如 `.rtf`)?实现 `DocumentConverter`,在 `register_converters` 中以负优先级注册。
5. 加测试:参考 `tests/test_*.py`,使用 `pytest tests/ -v`。