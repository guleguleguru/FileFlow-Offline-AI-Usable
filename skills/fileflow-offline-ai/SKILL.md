---
name: fileflow-offline-ai
description: Use FileFlow Offline for local Windows file conversion. Trigger when the user wants to convert PDF, Word, or image files; use the GUI for manual workflows and the agent CLI for automation, JSON output, dependency checks, or AI-agent-readable conversion results.
---

# FileFlow Offline AI

Use this skill to operate the FileFlow Offline Windows converter without making the user read the README.

## Quick Decision

- For a person using the desktop app, open `离线文件转换器.exe` or `启动图形界面.bat`.
- For an AI agent, script, test, or repeatable workflow, use `offline-converter-agent.exe`.
- Do not upload user documents. This tool is designed for local offline conversion.
- Do not commit or upload conversion inputs, outputs, bundled runtimes, OCR models, or release zips unless the user explicitly asks for a Release upload.

## Locate The Tool

Prefer these paths in order:

1. Current workspace release: `release-components-agent/离线文件转换器/offline-converter-agent.exe`
2. Current workspace dist: `dist-agent/离线文件转换器/offline-converter-agent.exe`
3. Default project path: `C:/工作/offline-file-converter/release-components-agent/离线文件转换器/offline-converter-agent.exe`
4. Default dist path: `C:/工作/offline-file-converter/dist-agent/离线文件转换器/offline-converter-agent.exe`

Run `scripts/resolve_fileflow.py` from this skill to print discovered GUI and agent executables as JSON.

## Agent Commands

Check dependencies:

```powershell
& "PATH\offline-converter-agent.exe" check-dependencies --json
```

PDF to Word:

```powershell
& "PATH\offline-converter-agent.exe" convert --kind pdf-to-word --input "file.pdf" --output-dir "agent-output" --json
```

Image(s) to PDF:

```powershell
& "PATH\offline-converter-agent.exe" convert --kind image-to-pdf --input "1.jpg" "2.png" --output-dir "agent-output" --json
```

PDF to images:

```powershell
& "PATH\offline-converter-agent.exe" convert --kind pdf-to-images --input "file.pdf" --output-dir "agent-output" --pages "1,3-5" --image-format png --json
```

Word to PDF:

```powershell
& "PATH\offline-converter-agent.exe" convert --kind word-to-pdf --input "file.docx" --output-dir "agent-output" --json
```

The JSON result contains `ok`, `tasks`, `status`, `inputs`, `outputs`, `page_count`, and `error`. Use `outputs` for follow-up validation or user reporting.

## Validation Workflow

After a conversion:

1. Confirm the command exit code is `0` and JSON `ok` is `true`.
2. Confirm every path in `outputs` exists.
3. For PDF to Word, inspect the generated DOCX text with `python-docx` when accuracy matters.
4. For PDF to images, compare exported image count with requested pages.
5. For Word to PDF, confirm the output PDF exists and has nonzero size.

For PDF to Word, set expectations clearly: FileFlow prioritizes editable text. It does not promise perfect reconstruction of complex table or form layout.

## Repository Hygiene

When preparing GitHub uploads:

- Commit source files, tests, README, packaging spec, icons, `.gitignore`, and license notices.
- Keep `vendor/`, `dist-*`, `release-components*`, `build/`, generated zips, local documents, and conversion outputs out of git.
- Put large Windows release zips in GitHub Releases, not in the source repository.
