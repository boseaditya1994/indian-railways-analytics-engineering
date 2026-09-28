<#!
.SYNOPSIS
Finds extracted RSTGCN CSV files and runs the no-Snowflake validation preflight.
#>
[CmdletBinding()]
param()

$projectRoot = Split-Path -Parent $PSScriptRoot
$dataRoot = Join-Path $projectRoot 'data\raw\rstgcn_sep2024'
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$provenance = Join-Path $projectRoot 'data\provenance\rstgcn_sep2024.json'
$quarantineReport = Join-Path $projectRoot 'artifacts\quality\rstgcn_sep2024_quarantine.json'

if (-not (Test-Path -LiteralPath $python)) { throw "Project Python environment not found: $python" }
if (-not (Test-Path -LiteralPath $provenance)) { throw "Provenance manifest not found: $provenance" }

$delay = Get-ChildItem -LiteralPath $dataRoot -Recurse -File -Filter 'train_routes_delays_Sep2024.csv' | Select-Object -First 1
$route = Get-ChildItem -LiteralPath $dataRoot -Recurse -File -Filter 'train_routes_Sep2024.csv' | Select-Object -First 1
if ($null -eq $delay -or $null -eq $route) {
    throw "Could not locate both documented RSTGCN CSV files under $dataRoot"
}

& $python -m railway_pipeline --mode backfill --start-date 2024-09-01 `
    --rstgcn-delay-path $delay.FullName `
    --rstgcn-route-path $route.FullName `
    --provenance-path $provenance `
    --quarantine-report-path $quarantineReport
if ($LASTEXITCODE -ne 0) { throw "RSTGCN preflight failed with exit code $LASTEXITCODE" }
