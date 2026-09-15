# Azure 后端实战

## 1. Azure Document Intelligence(DI)

适合:高质量 PDF/扫描件、表格抽取。

```bash
export AZURE_DOCINTEL_ENDPOINT="https://<res>.cognitiveservices.azure.com/"
# CLI 用 -d -e
markitdown scan.pdf -d -e "$AZURE_DOCINTEL_ENDPOINT" -o scan.md
```

Python 等价:
```python
import os
from markitdown import MarkItDown
md = MarkItDown(docintel_endpoint=os.environ["AZURE_DOCINTEL_ENDPOINT"])
print(md.convert_local("scan.pdf").markdown)
```

## 2. Azure Content Understanding(CU)

适合:多模态(文档/图像/音频/视频)、结构化字段。

```bash
export AZURE_CU_ENDPOINT="https://<cu>.services.ai.azure.com/"

# 2.1 自动选 analyzer(按文件类型)
markitdown report.pdf --use-cu --cu-endpoint "$AZURE_CU_ENDPOINT" -o out.md

# 2.2 自定义 analyzer(例:自定义发票分析器)
markitdown invoice.pdf --use-cu \
  --cu-endpoint "$AZURE_CU_ENDPOINT" \
  --cu-analyzer "my-invoice-analyzer" \
  -o invoice.md

# 2.3 只对部分类型启用 CU(其它走本地)
markitdown mixed/* --use-cu \
  --cu-endpoint "$AZURE_CU_ENDPOINT" \
  --cu-file-types pdf,jpeg,mp4 \
  -o mixed.md
```

Python 等价:
```python
from markitdown import MarkItDown, converters
md = MarkItDown(
    cu_endpoint="https://<cu>.services.ai.azure.com/",
    cu_analyzer_id="my-invoice-analyzer",
    cu_file_types=[converters.ContentUnderstandingFileType.PDF],
)
print(md.convert_local("invoice.pdf").markdown)
```

## 3. 互斥规则

- `-d` 与 `--use-cu` **不可同时出现**(argparse mutually_exclusive_group)
- 同时传时,以 argparse 抛错为准,后者不生效
- 推荐:**先 DI 跑不动再 CU**,或者按"扫描件 vs 普通"分流,不要一刀切

## 4. 凭据链

DI / CU 默认走 `azure-identity` 的默认凭据链:

- 本地:`az login`
- CI:Service Principal / Managed Identity / 环境变量

详见 [`azure-identity` 文档](https://learn.microsoft.com/python/api/overview/azure/identity-readme)。