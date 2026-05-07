# GitHub Copilot Instructions

Use `AGENTS.md` for this repository.

For file conversion requests, use FileFlow Offline through `offline-converter-agent.exe`:

```powershell
python skills/fileflow-offline-ai/scripts/resolve_fileflow.py
& "PATH\offline-converter-agent.exe" convert --kind pdf-to-word --input "file.pdf" --output-dir "agent-output" --json
```

Validate JSON output and generated files before claiming success.
