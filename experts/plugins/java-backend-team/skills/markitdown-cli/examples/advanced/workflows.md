# 实战工作流示例

> 这是一组"可复制即用"的 bash 片段,覆盖 CLI 最常见的真实场景。

## 1. 把一整个目录的 Office 文件全部转 Markdown

```bash
#!/usr/bin/env bash
set -euo pipefail

INBOX="${1:-./inbox}"
OUT="${2:-./out_md}"
mkdir -p "$OUT"

shopt -s nullglob
for f in "$INBOX"/*; do
  ext="${f##*.}"
  case "$ext" in
    pdf|docx|pptx|xlsx|html|htm|epub|csv|json|xml|ipynb|md|txt)
      base="$(basename "$f")"
      out="$OUT/${base%.*}.md"
      echo "→ $f  →  $out"
      markitdown "$f" -o "$out"
      ;;
    *)
      echo "…skip $f (unsupported ext: $ext)"
      ;;
  esac
done
```

## 2. 远程 URL 抓取并转(简单 RSS→MD 工作流)

```bash
URL="https://example.com/blog/post.html"
curl -sL "$URL" | markitdown -m text/html -o post.md
```

## 3. 批量扫描件走 Azure Document Intelligence

```bash
ENDPOINT="https://<res>.cognitiveservices.azure.com/"
mkdir -p md_di
for pdf in scans/*.pdf; do
  markitdown "$pdf" -d -e "$ENDPOINT" -o "md_di/$(basename "${pdf%.pdf}").md"
done
```

## 4. 混合策略:扫描件走 DI、普通 PDF 走本地

```bash
ENDPOINT="https://<res>.cognitiveservices.azure.com/"
for pdf in inbox/*.pdf; do
  # 简易判别:文件名前缀 scan_ 走 DI
  if [[ "$(basename "$pdf")" == scan_* ]]; then
    markitdown "$pdf" -d -e "$ENDPOINT" -o "out/$(basename "${pdf%.pdf}").md"
  else
    markitdown "$pdf" -o "out/$(basename "${pdf%.pdf}").md"
  fi
done
```

## 5. 把输出再次用 `grep` 抽出章节

```bash
markitdown big_report.pdf | awk '
  /^# /  {print "\n# " substr($0,3); next}
  /^## / {print "\n## " substr($0,4); next}
  {print}
' > outline.md
```

## 6. Docker 中处理本地文件

```bash
# 一次性:文件用 stdin/stdout 流式传
docker run --rm -i markitdown:latest < ./local.pdf > ./local.md

# 多次:挂卷
docker run --rm \
  -v "$PWD/data":/data \
  markitdown:latest \
  markitdown /data/in.pdf -o /data/out.md
```

## 7. 在 CI 里跑(失败要明确退出码)

`__main__.py` 用 `sys.exit(1)` 报告配置错误,但**转换异常是否非零退出**取决于异常类型。建议:

```bash
set -e
if ! markitdown "$f" -o out.md; then
  echo "❌ markitdown failed on $f" >&2
  exit 1
fi
```

或在 Python 里捕获并显式 `sys.exit(2)`(见 `markitdown-awesome` 的"异常处理"示例)。

## 8. 配合 `entr` 实现"文件变了我就重转"

```bash
ls inbox/*.pdf | entr -c markitdown inbox/*.pdf -o out/all.md
```

> 注:`entr` 一次只接受一组文件,大批量建议写一个 `Makefile` 或用 `find … -exec`。

## 9. 让 `markitdown` 走 Azure Content Understanding 并路由多模态

```bash
CU="https://<cu>.services.ai.azure.com/"
# 让 PDF/JPEG/MP4 都走 CU,其它本地处理
markitdown media/* \
  --use-cu \
  --cu-endpoint "$CU" \
  --cu-file-types pdf,jpeg,mp4 \
  -o out_cu.md
```

## 10. 与 `tee` 配合:既看输出又留档

```bash
markitdown report.pdf | tee report.md | grep -E '^#+ ' > headings.md
```