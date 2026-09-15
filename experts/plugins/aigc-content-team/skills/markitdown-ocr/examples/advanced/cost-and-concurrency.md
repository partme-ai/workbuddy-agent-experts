# 进阶:成本控制与并发

## 为什么需要控制

OCR 插件每次遇到图片(或扫描页)就发一次 LLM 调用。100 张图 = 100 次 vision 调用,token 成本线性增长。**生产部署必须控制并发与失败回退**。

## 1. 串行(默认、最稳)

```python
from markitdown import MarkItDown
from openai import OpenAI
import pathlib

md = MarkItDown(enable_plugins=True, llm_client=OpenAI(), llm_model="gpt-4o")
for f in pathlib.Path("scans").glob("*.pdf"):
    out = pathlib.Path("out") / (f.stem + ".md")
    out.parent.mkdir(exist_ok=True)
    out.write_text(md.convert(str(f)).markdown, encoding="utf-8")
```

## 2. 并发(有上限的线程池)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from markitdown import MarkItDown
from openai import OpenAI
import pathlib, time

md = MarkItDown(enable_plugins=True, llm_client=OpenAI(), llm_model="gpt-4o")
files = list(pathlib.Path("scans").glob("*.pdf"))

def convert_one(f):
    t0 = time.time()
    text = md.convert(str(f)).markdown
    return f, text, time.time() - t0

with ThreadPoolExecutor(max_workers=4) as ex:
    for fut in as_completed(ex.submit(convert_one, f) for f in files):
        f, text, secs = fut.result()
        print(f"{f.name}: {secs:.1f}s, {len(text)} chars")
```

⚠️ 并发数不要超过 OpenAI RPM/TPM 限制;429 会被 `_ocr_service.py` 静默吞掉,表现为"图片没 OCR 出来"。

## 3. 失败重试 + 监控

```python
import logging, time
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ocr")

def with_retry(fn, attempts=3):
    for i in range(attempts):
        try: return fn()
        except Exception as e:
            if i == attempts - 1: raise
            log.warning("retry %d after %s", i, e)
            time.sleep(2 ** i)
```

## 4. 替换更便宜的模型做粗 OCR

`gpt-4o-mini` 支持 vision,成本约为 `gpt-4o` 的 1/30。质量看场景:

- 印刷清晰 + 简单排版 → `gpt-4o-mini`
- 扫描 + 表格 + 多语种 → `gpt-4o` 或 Claude/Gemini

```python
md = MarkItDown(enable_plugins=True, llm_client=OpenAI(), llm_model="gpt-4o-mini")
```