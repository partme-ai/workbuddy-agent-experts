# CLI Cheat Sheet(打印贴墙版)

## 最常用 10 条

```bash
# 1. PDF 转 Markdown 写到文件
markitdown report.pdf -o report.md

# 2. 转 stdout 再 pipe
markitdown report.pdf | wc -l

# 3. 从 stdin 读
cat report.pdf | markitdown

# 4. 提示扩展名(MIME)
cat blob | markitdown -x pdf
cat blob | markitdown -m application/pdf

# 5. 启用插件
markitdown scanned.pdf -p

# 6. 列已装插件
markitdown --list-plugins

# 7. 走 Azure Document Intelligence
markitdown scan.pdf -d -e "https://<res>.cognitiveservices.azure.com/"

# 8. 走 Azure Content Understanding
markitdown doc.pdf --use-cu --cu-endpoint "https://<cu>.services.ai.azure.com/"

# 9. Content Understanding 限制文件类型
markitdown folder/* --use-cu --cu-endpoint "..." --cu-file-types pdf,jpeg

# 10. 保留 data URI(避免图片被截)
markitdown report.pdf --keep-data-uris -o report.md
```

## 参数速记

```
-v / --version          版本号
-o / --output FILE      写到文件
-x / --extension EXT    扩展名提示
-m / --mime-type MIME   MIME 提示
-c / --charset CSET     字符集提示
-d / --use-docintel     Azure Document Intelligence
-e / --endpoint URL     Document Intelligence endpoint
   / --use-cu           Azure Content Understanding
   / --cu-endpoint URL  CU endpoint
   / --cu-analyzer ID   CU 自定义 analyzer
   / --cu-file-types …  CU 限制类型
-p / --use-plugins      启用第三方插件
   / --list-plugins     列已装插件
   / --keep-data-uris   保留 data URI
```

## 互斥/组合速记

- `-d` 与 `--use-cu` **互斥**
- `-d` 必须同时给 `-e`
- `--use-cu` 必须同时给 `--cu-endpoint`
- `--list-plugins` 触发后立即退出,与"转文件"不可组合

## 环境变量(配合 Azure / OpenAI 客户端)

| 变量 | 作用 |
|------|------|
| `OPENAI_API_KEY` | OpenAI 客户端默认读 |
| `AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_ENDPOINT` / `OPENAI_API_VERSION` | Azure OpenAI SDK 默认读 |
| `EXIFTOOL_PATH` | MarkItDown 探测 exiftool 的备选路径 |
| `DOCINTEL_ENDPOINT` | (Python API 用)DI endpoint |
| `DOCINTEL_API_VERSION` | DI API 版本 |

> CLI 自身不直接读这些变量,变量由 Python API 构造的客户端读取。