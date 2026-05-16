$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:CREWAI_STORAGE_DIR = Join-Path $ProjectRoot ".crewai-storage"
$env:LOCALAPPDATA = Join-Path $ProjectRoot ".localappdata"
$env:PYTHONIOENCODING = "utf-8"
$env:CREWAI_TRACING_ENABLED = "false"

New-Item -ItemType Directory -Path $env:CREWAI_STORAGE_DIR -Force | Out-Null
New-Item -ItemType Directory -Path $env:LOCALAPPDATA -Force | Out-Null

& (Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1")
