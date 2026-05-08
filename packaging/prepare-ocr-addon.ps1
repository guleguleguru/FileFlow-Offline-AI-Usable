param(
    [string]$Python = "python",
    [string]$OutputDir = "packaging\addons\ocr\python"
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$target = Join-Path $root $OutputDir

if (Test-Path $target) {
    Remove-Item -LiteralPath $target -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $target | Out-Null
& $Python -m pip install --default-timeout 180 --upgrade -r (Join-Path $root "requirements-ocr.txt") -t $target
if ($LASTEXITCODE -ne 0) {
    throw "Failed to prepare OCR Python runtime. pip exited with code $LASTEXITCODE."
}

Write-Host "OCR Python runtime prepared at $target"
Write-Host "Build the addon with: ISCC.exe packaging\inno\FileFlowOffline-OCR-Addon.iss"
