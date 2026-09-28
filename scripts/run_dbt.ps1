<#!
.SYNOPSIS
Runs dbt with project-local credentials loaded from .env and a hidden password prompt.

.EXAMPLE
.\scripts\run_dbt.ps1 debug
.\scripts\run_dbt.ps1 build
#>
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$DbtArguments
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ProjectRoot ".env"
$DbtExe = Join-Path $ProjectRoot ".venv\Scripts\dbt.exe"

if (-not (Test-Path -LiteralPath $EnvFile)) { throw "Missing .env file at $EnvFile" }
$DbtCommand = $null
if (Test-Path -LiteralPath $DbtExe) {
    $DbtCommand = $DbtExe
}
else {
    $PathDbt = Get-Command dbt -ErrorAction SilentlyContinue
    if ($PathDbt) { $DbtCommand = $PathDbt.Source }
}
if (-not $DbtCommand) { throw "dbt was not found in .venv or on PATH. Install a dbt CLI, then retry." }

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
    & $DbtCommand @DbtArguments --project-dir (Join-Path $ProjectRoot "dbt_railway") --profiles-dir (Join-Path $ProjectRoot "dbt_railway")
    exit $LASTEXITCODE
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Bstr)
    Remove-Item Env:SNOWFLAKE_PASSWORD -ErrorAction SilentlyContinue
}
