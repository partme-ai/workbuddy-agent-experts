# CLI ↔ Azure 后端 ↔ Python API 对照表

> 在 CLI、Python API、Azure Portal 之间快速切换时,这张表能减少查文档的次数。

| 用户意图 | CLI | Python API |
|---------|-----|-----------|
| 走 DI(高质量 PDF/扫描) | `markitdown f.pdf -d -e "$ENDPOINT"` | `MarkItDown(docintel_endpoint="…")` |
| 走 CU(自动选 analyzer) | `markitdown f.pdf --use-cu --cu-endpoint "$ENDPOINT"` | `MarkItDown(cu_endpoint="…")` |
| 走 CU + 自定义 analyzer | 加 `--cu-analyzer my-analyzer` | `MarkItDown(cu_endpoint="…", cu_analyzer_id="my-analyzer")` |
| 走 CU 限制类型 | `--cu-file-types pdf,jpeg` | `MarkItDown(cu_endpoint="…", cu_file_types=[ContentUnderstandingFileType.PDF, …])` |
| 自带 DI 凭据 | (CLI 不暴露,只能靠默认链) | `MarkItDown(docintel_endpoint="…", docintel_credential=AzureKeyCredential("…"))` |
| 自带 CU 凭据 | (CLI 不暴露) | `MarkItDown(cu_endpoint="…", cu_credential=AzureKeyCredential("…"))` |

## 服务端点长什么样

```
Document Intelligence:  https://<res>.cognitiveservices.azure.com/
Content Understanding:  https://<cu>.services.ai.azure.com/
```

`res` / `cu` 是你在 Azure Portal 创建的资源名。

## CLI 没有暴露的 Python API 字段

CLI 故意做得精简。下列功能**只能通过 Python API**:

- `docintel_credential` / `cu_credential`(注入显式凭据)
- `docintel_api_version`
- `llm_client` / `llm_model` / `llm_prompt`(需要 `markitdown-ocr` 插件 → `markitdown-ocr` skill)
- `style_map`(自定义 mammoth 样式映射)
- `exiftool_path`

如果用户的需求命中以上字段,直接转用 Python API 或跳到兄弟 Skill。