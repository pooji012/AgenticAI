$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:CREWAI_STORAGE_DIR = Join-Path $ProjectRoot ".crewai-storage"
$env:LOCALAPPDATA = Join-Path $ProjectRoot ".localappdata"
$env:TEMP = Join-Path $ProjectRoot ".tmp"
$env:TMP = Join-Path $ProjectRoot ".tmp"
$env:PIP_CACHE_DIR = Join-Path $ProjectRoot ".tmp"
$env:PYTHONIOENCODING = "utf-8"
$env:CREWAI_TRACING_ENABLED = "false"

New-Item -ItemType Directory -Path $env:CREWAI_STORAGE_DIR -Force | Out-Null
New-Item -ItemType Directory -Path $env:LOCALAPPDATA -Force | Out-Null
New-Item -ItemType Directory -Path $env:TEMP -Force | Out-Null

$VenvScripts = Join-Path $ProjectRoot ".venv\Scripts"
if (-not $env:_OLD_CONTENT_CREATION_PATH) {
    $env:_OLD_CONTENT_CREATION_PATH = $env:PATH
}

function global:deactivate {
    if ($env:_OLD_CONTENT_CREATION_PATH) {
        $env:PATH = $env:_OLD_CONTENT_CREATION_PATH
        Remove-Item Env:_OLD_CONTENT_CREATION_PATH -ErrorAction SilentlyContinue
    }
    Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue
    Remove-Item function:deactivate -ErrorAction SilentlyContinue
}

$env:VIRTUAL_ENV = Join-Path $ProjectRoot ".venv"
$env:PATH = "$VenvScripts;$env:PATH"

Write-Host "Activated contentCreationAgent virtual environment."
