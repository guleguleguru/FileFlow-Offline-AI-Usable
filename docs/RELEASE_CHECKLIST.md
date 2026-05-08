# FileFlow Offline Release Checklist

Use this checklist before publishing a public GitHub Release.

## Build Artifacts

- Build `FileFlowOffline-Core-Setup.exe` from `packaging/offline-converter-core.spec`.
- Run `packaging/prepare-ocr-addon.ps1`, then build `FileFlowOffline-OCR-Addon.exe`.
- Build `FileFlowOffline-LibreOffice-Addon.exe`.
- Confirm large artifacts are uploaded as Release assets only and are not tracked in git.

## Clean Windows Install

- Install Core on a clean Windows machine.
- Confirm desktop/start-menu shortcuts open the GUI.
- Run `offline-converter-agent.exe check-dependencies --json`; OCR may be missing before OCR Addon.
- Install OCR Addon and confirm OCR status changes to available.
- Install LibreOffice Addon and confirm LibreOffice status changes to available for Word-to-PDF.
- Uninstall from Windows “应用和功能” and confirm the application directory is removed or contains only expected user-created files.

## Conversion Validation

- Run `python -m pytest`.
- Set `FILEFLOW_REAL_SAMPLE_DIR` to a local folder with sanitized PDFs and run `python -m pytest tests\test_real_pdf_samples.py`.
- Validate at least one text PDF, scanned Chinese PDF, table/form PDF, mixed PDF, and multi-page PDF.
- For PDF-to-Word, check both `visual` and `editable` expectations: visual embeds page images for appearance; editable prioritizes editable text.

## Release Notes

- State that the release is `v0.2.0-alpha` unless clean-machine validation and real-sample coverage have been completed.
- Describe Core, OCR Addon, and LibreOffice Addon installation order.
- State that documents are processed locally and not uploaded.
- State that complex PDF tables/forms are not guaranteed to become native editable Word tables.
- Attach or link `THIRD_PARTY_NOTICES.md`.
