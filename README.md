# 离线文件转换器

Windows 桌面软件，用于本机离线转换 PDF、Word 和图片文件。文件不会上传到网络。

## 功能

- 图片转 PDF：支持 JPG、PNG、WebP、BMP、TIFF，多图合并为一个 PDF。
- PDF 转图片：支持 PNG/JPG，支持页码范围。
- Word 转 PDF：通过本机或随包附带的 LibreOffice headless 转换。
- PDF 转 Word：文字型 PDF 直接提取为可编辑 DOCX；扫描件 PDF 可通过 PaddleOCR 中文模型做 OCR。

## 图形界面使用

```powershell
cd C:\工作\offline-file-converter
python -m pip install -e ".[dev]"
python -m offline_converter
```

打开后按 3 步使用：选择转换方式，添加或拖入文件，点击“开始转换”。

## AI agent / 命令行使用

命令行入口不会打开图形界面，适合本地 agent、脚本和自动化调用。

本项目还附带 Codex Skill：`skills/fileflow-offline-ai`。安装到 `~/.codex/skills/fileflow-offline-ai` 后，用户可以直接让 agent “用 FileFlow Offline 转换这个文件”，agent 会按 skill 自动定位 `offline-converter-agent.exe`、输出 JSON 并复核结果。

检查依赖：

```powershell
python -m offline_converter check-dependencies --json
```

PDF 转 Word：

```powershell
python -m offline_converter convert `
  --kind pdf-to-word `
  --input "C:\工作\offline-file-converter\附件材料.pdf" `
  --output-dir "C:\工作\offline-file-converter\agent-output" `
  --json
```

图片转 PDF：

```powershell
python -m offline_converter convert `
  --kind image-to-pdf `
  --input "1.jpg" "2.png" `
  --output-dir "C:\工作\offline-file-converter\agent-output" `
  --json
```

PDF 转图片：

```powershell
python -m offline_converter convert `
  --kind pdf-to-images `
  --input "file.pdf" `
  --output-dir "C:\工作\offline-file-converter\agent-output" `
  --pages "1,3-5" `
  --image-format png `
  --json
```

Word 转 PDF：

```powershell
python -m offline_converter convert `
  --kind word-to-pdf `
  --input "file.docx" `
  --output-dir "C:\工作\offline-file-converter\agent-output" `
  --json
```

JSON 输出包含 `ok`、每个任务的 `status`、`inputs`、`outputs`、`page_count` 和 `error`，agent 可以直接读取 `outputs` 继续处理。

打包后的离线包里也会包含 agent 专用入口：

```powershell
.\offline-converter-agent.exe convert --kind pdf-to-word --input "file.pdf" --output-dir "agent-output" --json
```

双击使用仍然打开 `离线文件转换器.exe` 图形界面；脚本和 agent 使用 `offline-converter-agent.exe`。

## 测试

```powershell
cd C:\工作\offline-file-converter
python -m pytest
```

## 打包

安装 PyInstaller：

```powershell
python -m pip install pyinstaller
```

构建：

```powershell
pyinstaller packaging/offline-converter.spec --noconfirm --clean --distpath dist-full
```

发布包需要包含 `vendor/LibreOffice` 和 `vendor/paddleocr/whl`，PyInstaller 会随包带上这些本地组件。
