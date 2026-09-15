# DocumentConverter 生命周期

> 给"想写自定义转换器"的读者。基于 [`_base_converter.py`](https://github.com/microsoft/markitdown/blob/main/packages/markitdown/src/markitdown/_base_converter.py)。

## 两个核心抽象

```python
class DocumentConverter:
    def accepts(self, file_stream, stream_info, **kwargs) -> bool: ...
    def convert(self, file_stream, stream_info, **kwargs) -> DocumentConverterResult: ...

@dataclass
class DocumentConverterResult:
    markdown: str       # 主输出
    text_content: str   # 部分内置转换器会同步填
    # 任何额外字段都可以通过 kwargs 透传
```

## 注册与优先级

```python
from markitdown import MarkItDown, PRIORITY_SPECIFIC_FILE_FORMAT
md = MarkItDown(enable_builtins=False)
md.register_converter(MyConverter(), priority=PRIORITY_SPECIFIC_FILE_FORMAT)
```

优先级数字越小越先试用。内置转换器用 `0.0` 和 `10.0`;插件(例如 markitdown-ocr)用 `-1.0` 抢在前面。

## `accepts()` 的最佳实践

1. **优先看 `stream_info.extension`**(最便宜),其次 `stream_info.mimetype`,最后才读 `file_stream` 做 magic-byte 检测。
2. **不要在 `accepts()` 里读整个流**——MarkItDown 会把流 seek 回起点再交给 `convert()`,但读太多会拖慢判断。
3. **不要抛异常**:用 `return False` 表示"这不是我的格式",让其它转换器继续。

## `convert()` 注意事项

- `file_stream` 是 `BinaryIO`,调用方可能 seek 过;确保 `convert()` 自己 `seek(0)` 或读完整。
- 返回 `DocumentConverterResult(markdown="…")`;`text_content` 留空也没事,主消费方读 `markdown`。
- 若你想"先 OCR 再结构化",OCR 阶段用第三方插件思路:在 `convert()` 内部调用 LLM 后再产出 Markdown。

## 调试

```python
import logging
logging.getLogger("markitdown").setLevel(logging.DEBUG)
```

MarkItDown 没有结构化 logger,但 `warn()` 会把插件加载错误打到 stderr,适合排查。