<#!
.SYNOPSIS
Downloads the author-approved RSTGCN dataset locally, extracts it, hashes the archive,
and writes a local provenance manifest. Raw data remains excluded from Git.
#>
[CmdletBinding()]
param()

$projectRoot = Split-Path -Parent $PSScriptRoot
$destination = Join-Path $projectRoot 'data\raw\rstgcn_sep2024'
$archivePath = Join-Path $destination 'Indian-Railway-Network-and-Delays.zip'
$manifestPath = Join-Path $projectRoot 'data\provenance\rstgcn_sep2024.json'
$datasetUrl = 'https://raw.githubusercontent.com/KoyenaChowdhury/RSTGCN/main/Indian-Railway-Network-and-Delays.zip'

if (Test-Path -LiteralPath $destination) {
    $existingItems = @(Get-ChildItem -LiteralPath $destination -Force)
    if ($existingItems.Count -gt 0) {
        throw "Destination is not empty: $destination. Review its contents before running again."
    }
}

New-Item -ItemType Directory -Force -Path $destination | Out-Null
try {
    Invoke-WebRequest -Uri $datasetUrl -OutFile $archivePath -ErrorAction Stop
    $hash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    Expand-Archive -LiteralPath $archivePath -DestinationPath $destination -ErrorAction Stop
    $manifest = [ordered]@{
        source_name = 'rstgcn_sep2024'
        source_url = 'https://github.com/KoyenaChowdhury/RSTGCN'
        license_name = 'Written author permission; citation required'
        retrieved_at = (Get-Date).ToUniversalTime().ToString('o')
        coverage_description = 'Train-level observed arrival/departure delays and routes for September 2024 from the RSTGCN authors.'
        local_processing_permitted = $true
        automated_access_permitted = $false
        raw_redistribution_permitted = $false
        archive_sha256 = $hash
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $manifestPath) | Out-Null
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding utf8
    Write-Output "Acquired RSTGCN locally. SHA-256: $hash"
    Write-Output "Provenance manifest: $manifestPath"
}
catch {
    if (Test-Path -LiteralPath $destination) {
        Write-Warning "Acquisition did not complete. Review and remove only $destination if you want a clean retry."
    }
    throw
}
