<#!
.SYNOPSIS
Starts the dashboard API with a hidden, process-only Snowflake password.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ProjectRoot ".env"
$UvicornExe = Join-Path $ProjectRoot ".venv\Scripts\uvicorn.exe"
if (-not (Test-Path -LiteralPath $EnvFile)) { throw "Missing .env file at $EnvFile" }
if (-not (Test-Path -LiteralPath $UvicornExe)) { throw "uvicorn is not installed in .venv. Run: .\.venv\Scripts\python.exe -m pip install -e '.[dashboard,warehouse]'" }

Get-Content -LiteralPath $EnvFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
        $name, $value = $line.Split("=", 2)
        [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim().Trim('"'), "Process")
    }
}
$SecurePassword = Read-Host "Snowflake password (not saved)" -AsSecureString
$Bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword)
try {
    $env:SNOWFLAKE_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Bstr)
    & $UvicornExe railway_pipeline.dashboard.api:app --host 127.0.0.1 --port 8000
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Bstr)
    Remove-Item Env:SNOWFLAKE_PASSWORD -ErrorAction SilentlyContinue
}
