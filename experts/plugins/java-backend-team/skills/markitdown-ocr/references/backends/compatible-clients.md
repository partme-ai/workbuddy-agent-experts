# 兼容的 LLM 客户端矩阵

> `markitdown-ocr` 不绑定特定厂商——只要客户端实现了 OpenAI 的 `chat.completions.create(model, messages=[…])` 且支持 vision 就能用。这页是常见组合速查。

## 协议要求

```python
# 插件内部期望的最小协议
response = client.chat.completions.create(
    model="…",
    messages=[
        {"role": "user", "content": [
            {"type": "text", "text": "<prompt>"},
            {"type": "image_url", "image_url": {"url": "data:image/...;base64,..."}},
        ]},
    ],
)
text = response.choices[0].message.content
```

`image_url` 是 `data:` URI(Base64 内嵌);**不是**公网 URL。

## 客户端清单

| 客户端 | 构造 | 备注 |
|--------|------|------|
| `openai.OpenAI()` | `OpenAI()` | 默认读 `OPENAI_API_KEY` |
| `openai.AzureOpenAI(...)` | 显式传 `api_key` + `azure_endpoint` + `api_version` | 需 deployment 支持 vision |
| `openai.OpenAI(base_url=…)` | 任意 OpenAI 兼容端点 | vLLM / Ollama / Gemini / DeepSeek-VL |
| `httpx.Client(proxy=…)` → `OpenAI(http_client=…)` | 走 HTTP 代理 | 企业网环境 |

## 已知可用的视觉模型(2026-08)

- OpenAI:`gpt-4o`、`gpt-4o-mini`、`gpt-4-turbo`
- Azure OpenAI:同上(deployment 名映射)
- Google:`gemini-2.0-flash`、`gemini-1.5-pro-vision`
- 本地:`Qwen2-VL-7B-Instruct`、`llama3.2-vision`、`InternVL2`

## 选型速记

- **质量优先 + 中文场景** → `gpt-4o` 或 `Qwen2-VL-72B`
- **成本敏感 + 量大** → `gpt-4o-mini`
- **完全本地 / 离线** → vLLM + `Qwen2-VL-7B`
- **多语种混排** → Gemini 系

## 注意

- 视觉模型**单次能塞多少 token** 决定单张图的上限分辨率;超大会被客户端截断或报错。
- 部分本地模型对 `data:` URI 支持不稳;若失败,先在 OpenAI Playground 验证模型本身可用。