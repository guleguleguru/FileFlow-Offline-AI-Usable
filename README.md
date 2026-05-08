# FileFlow Offline AI-Usable

离线 Windows 文件转换器，支持 PDF、Word、图片互转、中文 OCR，并提供图形界面和 AI agent 可调用的 JSON CLI。当前版本定位为 `v0.2.0-alpha`：功能已可试用，但复杂 PDF 版式还原和安装器兼容性仍需要更多真实机器验证。

## 功能

- 图片转 PDF：支持 JPG、PNG、WebP、BMP、TIFF，多图合并为一个 PDF。
- PDF 转图片：支持 PNG/JPG 和页码范围。
- Word 转 PDF：通过 LibreOffice Addon 或本机 LibreOffice 转换。
- PDF 转 Word：
  - `visual` 原版式优先：每页 PDF 渲染图直接嵌入 DOCX，适合表格和表单外观保真。
- `editable` 文字可编辑优先：提取文字生成 DOCX，适合轻量编辑。
- 扫描件 PDF 可通过 OCR Addon 使用 PaddleOCR 中文模型识别。

## 图形界面

```powershell
python -m offline_converter
```

打开后选择转换方式，添加或拖入文件，确认保存目录，点击“开始转换”。PDF 转 Word 可选择“原版式优先”或“文字可编辑优先”。

## AI agent / 命令行

检查依赖：

```powershell
python -m offline_converter check-dependencies --json
```

PDF 转 Word 原版式优先：

```powershell
python -m offline_converter convert `
  --kind pdf-to-word `
  --pdf-word-mode visual `
  --input "file.pdf" `
  --output-dir "agent-output" `
  --json
```

PDF 转 Word 文字可编辑优先：

```powershell
python -m offline_converter convert `
  --kind pdf-to-word `
  --pdf-word-mode editable `
  --input "file.pdf" `
  --output-dir "agent-output" `
  --json
```

诊断和日志：

```powershell
python -m offline_converter diagnose --json
python -m offline_converter export-logs --output logs.zip --json
```

打包后的离线包里使用：

```powershell
.\offline-converter-agent.exe convert --kind pdf-to-word --pdf-word-mode visual --input "file.pdf" --output-dir "agent-output" --json
```

本项目附带多 agent 指令：`AGENTS.md`、`CLAUDE.md`、`GEMINI.md`、`.cursor/rules/fileflow-offline-ai.mdc`、`.windsurfrules`、`.github/copilot-instructions.md`，以及 Codex Skill：`skills/fileflow-offline-ai`。

## 可选组件

- Core：GUI、agent CLI、基础 PDF/图片/文字型 PDF 转换。
- OCR Addon：扫描件 PDF 转 Word 的中文 OCR。
- LibreOffice Addon：Word 转 PDF。

大型运行组件不进入源码仓库，只通过 GitHub Releases 发布。

## 安装包

Release 建议提供 3 个安装包：

- `FileFlowOffline-Core-Setup.exe`：主程序、GUI、agent CLI 和基础转换。
- `FileFlowOffline-OCR-Addon.exe`：扫描件 PDF 转 Word 的中文 OCR。
- `FileFlowOffline-LibreOffice-Addon.exe`：Word 转 PDF。

卸载使用 Windows“应用和功能”中的 FileFlow Offline 入口。公开发布前应在干净 Windows 机器上验证 Core、Addon、快捷方式、卸载和 `check-dependencies --json`。

## 本地开发

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

需要 OCR 开发依赖时：

```powershell
python -m pip install -e ".[dev,ocr]"
```

真实 PDF 样本回归测试不提交敏感文件。把脱敏 PDF 放到本机目录后运行：

```powershell
$env:FILEFLOW_REAL_SAMPLE_DIR="D:\fileflow-real-samples"
python -m pytest tests\test_real_pdf_samples.py
```

## 打包

Core 绿色包：

```powershell
pyinstaller packaging/offline-converter-core.spec --noconfirm --clean --distpath dist-core
```

完整包：

```powershell
pyinstaller packaging/offline-converter.spec --noconfirm --clean --distpath dist-full
```

安装器使用 Inno Setup：

```powershell
iscc packaging/inno/FileFlowOffline-Core.iss
.\packaging\prepare-ocr-addon.ps1
iscc packaging/inno/FileFlowOffline-OCR-Addon.iss
iscc packaging/inno/FileFlowOffline-LibreOffice-Addon.iss
```

## 能力边界

文件全部本地离线处理，不上传。`visual` 模式把每页 PDF 作为图片嵌入 Word，优先保证外观接近；它不承诺复杂 PDF 表格能变成原生 Word 表格，也不优先保证文字可编辑。`editable` 模式优先可编辑文字，不承诺复杂版式还原。Release 包可能包含 LibreOffice、PaddleOCR、PaddlePaddle、PySide6、PyMuPDF、Pillow、python-docx 等第三方组件，分发时应附带 `THIRD_PARTY_NOTICES.md` 并遵守各自许可证。
