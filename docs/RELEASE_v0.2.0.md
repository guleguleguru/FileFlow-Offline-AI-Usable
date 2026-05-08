# FileFlow Offline v0.2.0-alpha

## 下载

- `FileFlowOffline-Core-Setup.exe`：主程序、图形界面、agent CLI、基础转换能力。
- `FileFlowOffline-OCR-Addon.exe`：扫描件 PDF 转 Word 所需中文 OCR 组件。
- `FileFlowOffline-LibreOffice-Addon.exe`：Word 转 PDF 所需 LibreOffice 组件。
- `FileFlowOffline-Full.zip`：可选完整离线包，适合不能分多次下载的场景；如果没有提供该附件，请安装 Core + 所需 Addon。

## 安装

1. 先安装 Core。
2. 需要扫描件 OCR 时安装 OCR Addon。
3. 需要 Word 转 PDF 时安装 LibreOffice Addon；PDF 转 Word 原版式优先不再依赖 LibreOffice。
4. 打开 FileFlow Offline，或用 `offline-converter-agent.exe check-dependencies --json` 检查组件状态。
5. 卸载时使用 Windows“应用和功能”里的 FileFlow Offline 卸载入口；Addon 文件会随安装目录清理。

## 发布构建说明

发布者编译 OCR Addon 前需要先运行 `.\packaging\prepare-ocr-addon.ps1`，把 PaddleOCR/PaddlePaddle 运行时放入 `packaging\addons\ocr\python`。大型运行组件只作为 Release 附件发布，不进入源码仓库。

发布前建议运行：

```powershell
python -m pytest
$env:FILEFLOW_REAL_SAMPLE_DIR="D:\fileflow-real-samples"
python -m pytest tests\test_real_pdf_samples.py
```

真实样本目录应只放脱敏 PDF，不提交到 git。

## Agent CLI

```powershell
offline-converter-agent.exe convert --kind pdf-to-word --pdf-word-mode visual --input "file.pdf" --output-dir "agent-output" --json
offline-converter-agent.exe diagnose --json
offline-converter-agent.exe export-logs --output logs.zip --json
```

## 能力边界

- 全部转换在本机离线完成，不上传文件。
- `pdf-to-word --pdf-word-mode visual` 会把每页 PDF 渲染图嵌入 DOCX；它优先接近原 PDF 外观，但不优先保证文字可编辑，也不承诺每个表格单元格都像原生 Word 表格一样编辑。
- `pdf-to-word --pdf-word-mode editable` 优先生成可编辑文字，复杂版式还原能力有限。
- 扫描件 OCR 质量取决于原件清晰度、方向和图片噪声。

## 已知限制

- Core 安装器不内置 OCR 和 LibreOffice；扫描件 OCR 需要 OCR Addon，Word 转 PDF 需要 LibreOffice Addon。
- 首次 OCR 可能较慢。
- 极复杂 PDF 的表格、印章、手写内容不能保证完全还原。

## 隐私和第三方许可证

文件不会上传。Release 包可能包含 LibreOffice、PaddleOCR、PaddlePaddle、PySide6、PyMuPDF、Pillow、python-docx 等第三方组件，各组件遵循其各自第三方许可证。发布 Release 时应同时附带 `THIRD_PARTY_NOTICES.md`，并在 Release 说明中提醒用户大型 Addon 只作为二进制附件分发，不进入源码仓库。
