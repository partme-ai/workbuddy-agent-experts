# 进阶:安全批量处理(企业场景)

## 目标

- 不依赖外网(避免 SSRF)
- 失败可恢复(只重跑失败文件)
- 输出结构稳定(便于下游 pipeline)

## 完整脚本

```bash
#!/usr/bin/env bash
set -euo pipefail

INBOX="${1:-./inbox}"
OUT="${2:-./out_md}"
mkdir -p "$OUT"

# 把 list 文件持久化,失败可续跑
LIST="$OUT/.list.txt"
> "$LIST"

find "$INBOX" -type f \( -iname "*.pdf" -o -iname "*.docx" -o -iname "*.pptx" -o -iname "*.xlsx" -o -iname "*.html" -o -iname "*.epub" \) -print0 \
  | sort -z \
  | while IFS= read -r -d '' f; do
      rel="${f#$INBOX/}"
      out="$OUT/${rel%.*}.md"
      mkdir -p "$(dirname "$out")"
      if markitdown "$f" -o "$out" 2>>"$OUT/.errors.log"; then
        echo "OK $f" >> "$LIST"
      else
        echo "FAIL $f" >> "$LIST"
      fi
    done

echo "done. see $OUT/.errors.log for failures"
```

## 关键点

1. `find … -print0` + `read -d ''` 防止文件名含空格/换行
2. `2>>` 把 stderr 收口到日志文件,不污染 stdout
3. `OUT/.list.txt` 持久化执行结果,可做幂等续跑
4. **不依赖** 任何 HTTP/SMTP/外网 — 避免 SSRF 与外部依赖