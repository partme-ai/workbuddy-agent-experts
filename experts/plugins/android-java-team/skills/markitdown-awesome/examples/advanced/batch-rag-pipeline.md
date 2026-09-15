# 高级:RAG 流水线批量入库

> 把整个文档目录结构化抽取 → 切片 → 写向量库。展示 MarkItDown 在生产 RAG 里的典型用法。

```python
import pathlib, hashlib
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=False)  # 显式禁用插件,可复现性更好

def file_hash(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]

for f in pathlib.Path("knowledge_base").rglob("*"):
    if not f.is_file(): continue
    if f.suffix.lower() not in {".pdf",".docx",".pptx",".xlsx",".md",".html"}: continue
    try:
        result = md.convert_local(str(f))
    except Exception as e:
        print(f"[SKIP] {f}: {e}")
        continue
    chunks = [c.strip() for c in result.markdown.split("\n\n") if c.strip()]
    for i, c in enumerate(chunks):
        # rag.index({
        #   "id": f"{file_hash(f)}_{i}",
        #   "text": c,
        #   "source": str(f),
        #   "chunk_index": i,
        # })
        pass
print("done")
```

要点:
- 用 `convert_local` 避免任何网络请求触发。
- 失败要记录 `file_hash` 以便重跑 / 排查。
- 按段落切块只是简单方案,生产可叠加 sentence-splitter。