# 可选安装特性(Extras)完整清单

> 引用自 [`packages/markitdown/pyproject.toml`](https://github.com/microsoft/markitdown/blob/main/packages/markitdown/pyproject.toml)。
> 任何变更以官方 pyproject 为准。

| 特性键 | 安装命令片段 | 启用场景 | 依赖预览 |
|--------|------------|---------|---------|
| `[all]` | `pip install 'markitdown[all]'` | 一把梭,几乎所有可选依赖都装 | 上述全部 |
| `[pptx]` | `pip install 'markitdown[pptx]'` | PowerPoint 文件 | python-pptx |
| `[docx]` | `pip install 'markitdown[docx]'` | Word 文件 | mammoth、python-docx |
| `[xlsx]` | `pip install 'markitdown[xlsx]'` | 现代 Excel | openpyxl、pandas |
| `[xls]` | `pip install 'markitdown[xls]'` | 老版 Excel | xlrd |
| `[pdf]` | `pip install 'markitdown[pdf]'` | PDF(内置转换器,无需云服务) | pdfminer.six、pdfplumber、PyMuPDF |
| `[outlook]` | `pip install 'markitdown[outlook]'` | Outlook `.msg` 邮件 | extract-msg |
| `[az-doc-intel]` | `pip install 'markitdown[az-doc-intel]'` | Azure Document Intelligence 后端 | azure-ai-documentintelligence |
| `[az-content-understanding]` | `pip install 'markitdown[az-content-understanding]'` | Azure Content Understanding 后端 | azure-ai-contentunderstanding |
| `[audio-transcription]` | `pip install 'markitdown[audio-transcription]'` | 音频 wav/mp3 转写 | whisper 等 |
| `[youtube-transcription]` | `pip install 'markitdown[youtube-transcription]'` | YouTube 视频转写 | yt-dlp 等 |

## 常见组合

```bash
# 最小可用(Office + PDF,本地即可)
pip install 'markitdown[pdf,docx,pptx,xlsx]'

# 全部内置 + Azure Document Intelligence
pip install 'markitdown[all]' 'markitdown[az-doc-intel]'
# 注意:有些键合并装会报错,若遇冲突改用单次安装
pip install 'markitdown[pdf,docx,pptx,xlsx,az-doc-intel]'

# LLM Vision OCR(走 markitdown-ocr 插件)
pip install markitdown-ocr
pip install openai   # 或 azure-openai / 任何 OpenAI 兼容客户端
```

## 依赖缺失时的行为

某个特性未安装但碰到了对应文件,会抛 `MissingDependencyException`(`_exceptions.py` 中定义)。`__main__.py` 会把异常透传到 stderr。**最佳实践**:在脚本里捕获后给用户友好提示,例如:

```python
from markitdown import MarkItDown
from markitdown._exceptions import MissingDependencyException

try:
    md = MarkItDown()
    print(md.convert("slides.pptx").markdown)
except MissingDependencyException as e:
    print("需要先安装 pptx 依赖:\n  pip install 'markitdown[pptx]'")
```