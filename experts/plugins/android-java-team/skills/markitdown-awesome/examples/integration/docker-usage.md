# 集成:Docker 与 CI 用法

## Docker 一次性运行

```bash
# 构建(仓库根目录)
docker build -t markitdown:latest .

# stdin → stdout
docker run --rm -i markitdown:latest < ./input.pdf > ./output.md

# 挂载数据目录
docker run --rm \
  -v "$PWD/data":/data \
  markitdown:latest \
  markitdown /data/in.pdf -o /data/out.md
```

## 在 CI(GitHub Actions / GitLab CI)中跑

```yaml
- name: Convert reports to markdown
  run: |
    pip install 'markitdown[pdf,docx,pptx,xlsx]'
    mkdir -p out
    for f in reports/*; do
      markitdown "$f" -o "out/$(basename "${f%.*}").md"
    done
- name: Upload artifacts
  uses: actions/upload-artifact@v4
  with:
    name: markdown-reports
    path: out/
```

## 与 `make` 集成

```make
MARKITDOWN ?= markitdown
SRC := $(wildcard docs/*.pdf docs/*.docx)
OUT := $(patsubst docs/%,out/%,$(SRC:.pdf=.md))
OUT := $(OUT:.docx=.md)

out/%.md: docs/%
	@mkdir -p out
	$(MARKITDOWN) $< -o $@

.PHONY: all
all: $(OUT)
```