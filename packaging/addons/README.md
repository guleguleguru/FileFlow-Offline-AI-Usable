# Addon staging

This folder is for local release staging only. Do not commit large OCR or LibreOffice runtime payloads.

Prepare the OCR runtime before compiling `FileFlowOffline-OCR-Addon.iss`:

```powershell
.\packaging\prepare-ocr-addon.ps1
```

The script installs PaddleOCR/PaddlePaddle into `packaging\addons\ocr\python`, which the installer places at `plugins\ocr\python`.
