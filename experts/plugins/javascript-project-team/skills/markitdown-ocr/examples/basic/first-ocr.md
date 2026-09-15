# 第一次 OCR(Hello-World 级)

## 1. 装包

```bash
pip install markitdown-ocr openai
export OPENAI_API_KEY=sk-...
```

## 2. 准备一个含图的 PDF

任意一份 PPT/Word/PDF 都行——本示例假设 `demo.pdf` 含嵌入图片。

## 3. Python 一行

```python
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(
    enable_plugins=True,
    llm_client=OpenAI(),
    llm_model="gpt-4o",
)
print(md.convert("demo.pdf").markdown)
```

## 4. 看到 `*[Image OCR]…[End OCR]*` 块?

说明 OCR 跑通了。若一个都没出现:

```bash
markitdown --list-plugins | grep ocr
# 期望: ocr   (package: markitdown_ocr)
```

若没有输出,确认 `pip install markitdown-ocr` 成功,再确认 `enable_plugins=True`。

完成。