# 后端实战:Azure OpenAI / 本地 vLLM / Ollama

## 1. Azure OpenAI(企业合规场景)

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
md.convert("confidential.pdf").markdown
```

> 注意:`azure_endpoint` 不要带尾部 `/`;`api_version` 必须是 deployment 已启用的版本。

## 2. 本地 vLLM(私有化)

```bash
# 启动 vLLM,暴露 OpenAI 兼容协议
vllm serve Qwen2-VL-7B-Instruct --port 8000
```

```python
import openai
from markitdown import MarkItDown

client = openai.OpenAI(base_url="http://localhost:8000/v1")  # 本地 vLLM 通常不校验 key
md = MarkItDown(
    enable_plugins=True,
    llm_client=client,
    llm_model="Qwen2-VL-7B-Instruct",
)
md.convert("doc.pdf").markdown
```

## 3. Ollama(本地小模型)

```bash
ollama serve
ollama pull llama3.2-vision
```

```python
import openai
from markitdown import MarkItDown

client = openai.OpenAI(base_url="http://localhost:11434/v1")  # 本地 Ollama 通常不校验 key
md = MarkItDown(
    enable_plugins=True,
    llm_client=client,
    llm_model="llama3.2-vision",
)
md.convert("doc.pdf").markdown
```

## 4. Google Gemini(走 OpenAI 兼容端点)

```python
import openai
from markitdown import MarkItDown

client = openai.OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.environ["GOOGLE_API_KEY"],
)
md = MarkItDown(enable_plugins=True, llm_client=client, llm_model="gemini-2.0-flash")
md.convert("doc.pdf").markdown
```

## 5. 走 HTTP 代理

```python
import httpx
from openai import OpenAI

http_client = httpx.Client(proxy="http://proxy.local:3128", timeout=60)
client = OpenAI(http_client=http_client)
md = MarkItDown(enable_plugins=True, llm_client=client, llm_model="gpt-4o")
```

## 选哪个?

| 后端 | 适合 | 成本 | 隐私 |
|------|------|------|------|
| OpenAI `gpt-4o` | 通用,质量稳 | 中 | 云端 |
| OpenAI `gpt-4o-mini` | 大批量、粗 OCR | 低 | 云端 |
| Azure OpenAI | 企业合规 | 中 | Azure 私有云 |
| vLLM 本地 | 完全私有化 | GPU 折旧 | 完全本地 |
| Ollama | 笔记本/小模型 | 0 | 完全本地 |
| Gemini | 多语种、价格低 | 低 | Google 云 |