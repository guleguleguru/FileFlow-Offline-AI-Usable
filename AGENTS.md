# Agent Instructions

Use FileFlow Offline as a local-only Windows file converter. Do not upload user documents.

## Preferred Workflow

1. Locate the executables:

   ```powershell
   python skills/fileflow-offline-ai/scripts/resolve_fileflow.py
   ```

2. Use the first candidate where `agent_exists` is `true`.
3. Check dependencies before conversion:

   ```powershell
   & "PATH\offline-converter-agent.exe" check-dependencies --json
   ```

4. Convert with JSON output:

   ```powershell
   & "PATH\offline-converter-agent.exe" convert --kind pdf-to-word --input "file.pdf" --output-dir "agent-output" --json
   ```

5. Validate `ok: true`, confirm every path in `tasks[].outputs` exists, and report the output paths.

## Conversion Kinds

- `pdf-to-word`: PDF to editable DOCX. Prioritizes editable text, not perfect table/form layout.
- `image-to-pdf`: One or more images to a combined PDF.
- `pdf-to-images`: PDF pages to PNG/JPG. Supports `--pages "1,3-5"` and `--image-format png|jpg`.
- `word-to-pdf`: DOC/DOCX to PDF through bundled or local LibreOffice.

## Safety

- Keep `vendor/`, `dist-*`, `release-components*`, `build/`, release zips, local PDFs, DOCX files, and conversion outputs out of source commits.
- Put large Windows packages in GitHub Releases, not in git.
- When validating PDF-to-Word quality, inspect DOCX text with `python-docx` if accuracy matters.
