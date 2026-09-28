[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) { throw "Virtual environment Python not found at $python" }

Push-Location $projectRoot
try {
    & $python '.\scripts\archive_raildar_live_status.py' --rstgcn-top-five
    if ($LASTEXITCODE -ne 0) { throw "RailRadar archive failed with exit code $LASTEXITCODE" }
}
finally {
    Pop-Location
}
