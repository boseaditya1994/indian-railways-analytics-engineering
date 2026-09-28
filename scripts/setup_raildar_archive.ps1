[CmdletBinding()]
param(
    [switch]$SkipTask
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$runner = Join-Path $PSScriptRoot 'run_raildar_archive.ps1'
$taskName = 'IndianRailwaysRailRadarArchive'

if (-not (Test-Path -LiteralPath $python)) { throw "Virtual environment Python not found at $python" }

$securePassword = Read-Host 'Snowflake password for the dedicated local archive connection' -AsSecureString
$credential = [System.Management.Automation.PSCredential]::new('archive', $securePassword)
$env:RAILWAY_ARCHIVE_SNOWFLAKE_PASSWORD = $credential.GetNetworkCredential().Password
try {
    Push-Location $projectRoot
    & $python '.\scripts\store_raildar_archive_password.py'
    if ($LASTEXITCODE -ne 0) { throw "Could not store the Snowflake archive credential" }
}
finally {
    Remove-Item Env:RAILWAY_ARCHIVE_SNOWFLAKE_PASSWORD -ErrorAction SilentlyContinue
    Pop-Location
}

if (-not $SkipTask) {
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$runner`""
    $triggers = @(
        (New-ScheduledTaskTrigger -Daily -At 8:00AM),
        (New-ScheduledTaskTrigger -Daily -At 8:00PM)
    )
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Principal $principal -Description 'Archives the RSTGCN-derived five-train RailRadar watchlist twice daily.' -Force | Out-Null
    Write-Host "Scheduled task '$taskName' created for 8:00 AM and 8:00 PM while you are logged in."
}

Write-Host 'Secure RailRadar archive setup complete.'
