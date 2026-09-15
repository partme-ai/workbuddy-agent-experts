# Python API 速查

> 来源:[`packages/markitdown/src/markitdown/_markitdown.py`](https://github.com/microsoft/markitdown/blob/main/packages/markitdown/src/markitdown/_markitdown.py) 与 [`__init__.py`](https://github.com/microsoft/markitdown/blob/main/packages/markitdown/src/markitdown/__init__.py)。

## 顶层导出

```python
from markitdown import (
    MarkItDown,
    DocumentConverter,
    DocumentConverterResult,
    MarkItDownException,
    MissingDependencyException,
    UnsupportedFormatException,
    FileConversionException,
    FailedConversionAttempt,
    StreamInfo,
    PRIORITY_SPECIFIC_FILE_FORMAT,   # = 0.0
    PRIORITY_GENERIC_FILE_FORMAT,    # = 10.0
)
```

## `MarkItDown(…)` 构造参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `enable_builtins` | bool \| None | True | 是否注册内置转换器 |
| `enable_plugins` | bool \| None | False | 是否加载 `markitdown.plugin` 入口点声明的第三方插件 |
| `requests_session` | requests.Session \| None | 自动创建 | 用于 `http(s):` URI;`Accept` 头会优先 `text/markdown` |
| `llm_client` | OpenAI-兼容客户端 \| None | None | 图像转换时的图注 client(也供 markitdown-ocr 使用) |
| `llm_model` | str \| None | None | 配合 `llm_client` |
| `llm_prompt` | str \| None | None | 自定义图注/OCR 提示词 |
| `exiftool_path` | str \| None | `$EXIFTOOL_PATH` → 自动探测 | 图像 EXIF 抽取 |
| `style_map` | str \| None | None | 自定义 mammoth HTML→Markdown 样式映射 |
| `docintel_endpoint` | str \| None | None | 启用 Azure Document Intelligence 后端 |
| `docintel_credential` | object \| None | None | DI 凭据(留 None 时用默认凭据链) |
| `docintel_file_types` | list \| None | None | DI 接管的文件类型白名单 |
| `docintel_api_version` | str \| None | None | DI API 版本 |
| `cu_endpoint` / `cu_credential` / `cu_analyzer_id` / `cu_file_types` | … | None | Azure Content Understanding 后端 |

`docintel_*` 与 `cu_*` 互斥(参考 `__main__.py` 的 `argparse` mutually_exclusive_group)。

## `convert()` / `convert_*()` 路由表

`MarkItDown.convert(source)` 根据 `source` 类型自动分派:

```
source 是 str → 检查前缀
  ├─ http:// https:// file:// data://   → convert_uri(source)
  └─ 其它(当作本地路径)              → convert_local(source)

source 是 pathlib.Path          → convert_local(source)
source 是 requests.Response     → convert_response(source)
source 是 BinaryIO              → convert_stream(source)
其它 → TypeError
```

`stream_info: StreamInfo` 是**贯穿全链路**的元数据,涵盖 `mimetype`、`extension`、`charset`、`filename`、`local_path`、`url`。`StreamInfo.copy_and_update(...)` 用于在不修改原对象的前提下合并线索。

## 返回值 `DocumentConverterResult`

`packages/markitdown/src/markitdown/_base_converter.py` 中定义。常用字段:

- `markdown: str` — 最终 Markdown 字符串(主输出)
- `text_content: str` — 部分内置转换器会同步填此字段(插件可只填它)

## 插件加载机制

通过 Python 入口点 `markitdown.plugin` 自动发现:

```toml
[project.entry-points."markitdown.plugin"]
ocr = "markitdown_ocr"
```

`MarkItDown(enable_plugins=True)` 会:
1. 调用 `importlib.metadata.entry_points(group="markitdown.plugin")`
2. 依次 `entry.load()` 拿到模块对象
3. 调用模块的 `register_converters(markitdown_instance, **kwargs)`

失败会被 `warn(...)` 捕获,**不会**让整个 MarkItDown 崩溃。

## 自定义转换器最小骨架

```python
from markitdown import DocumentConverter, DocumentConverterResult, StreamInfo
from markitdown._base_converter import PRIORITY_SPECIFIC_FILE_FORMAT

class MyTxtConverter(DocumentConverter):
    def accepts(self, file_stream, stream_info: StreamInfo, **kwargs) -> bool:
        return (stream_info.extension or "").lower() == ".mytxt"

    def convert(self, file_stream, stream_info: StreamInfo, **kwargs) -> DocumentConverterResult:
        text = file_stream.read().decode("utf-8", errors="replace")
        return DocumentConverterResult(markdown=f"# Custom Output\n\n{text}")

# 使用
from markitdown import MarkItDown
md = MarkItDown(enable_builtins=False)  # 只跑自定义
md.register_converter(MyTxtConverter(), priority=PRIORITY_SPECIFIC_FILE_FORMAT)
print(md.convert("hello.mytxt").markdown)
```

> 完整插件范例见 `packages/markitdown-sample-plugin`(官方仓库)。