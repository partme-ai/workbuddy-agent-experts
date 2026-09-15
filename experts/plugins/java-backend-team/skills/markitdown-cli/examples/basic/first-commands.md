# 基础:30 秒上手

## 装包

```bash
pip install 'markitdown[pdf,docx,pptx,xlsx]'
```

## 转一个 PDF 到 Markdown

```bash
markitdown report.pdf -o report.md
```

## 转 YouTube 视频(需要 youtube-transcription extras)

```bash
pip install 'markitdown[youtube-transcription]'
markitdown "https://www.youtube.com/watch?v=XXXX" -o transcript.md
```

## 列已装插件

```bash
markitdown --list-plugins
```

完成。

## 完整参数表

跑 `markitdown --help` 即可看到所有 CLI 参数;离线对照见 [cli/cheatsheet.md](../references/cli/cheatsheet.md)。