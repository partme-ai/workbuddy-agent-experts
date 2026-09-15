# 第一次转换(Hello-World 级)

> 这份"开箱即用"的最小示例,适合用户第一次接触 MarkItDown 时复制即用。

## 1. 装包

```bash
pip install 'markitdown[all]'
```

## 2. 转一个 PDF 到 stdout

```bash
markitdown hello.pdf
```

## 3. 转一个 PDF 到文件

```bash
markitdown hello.pdf -o hello.md
```

## 4. Python 一行

```python
from markitdown import MarkItDown
print(MarkItDown().convert("hello.pdf").markdown)
```

## 5. 列出已装插件

```bash
markitdown --list-plugins
```

完成以上五步就具备了"任何 Office → Markdown"的最短路径。