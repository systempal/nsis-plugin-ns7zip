<#
.SYNOPSIS
    Rebuilds the 7zip-19.00 directory from original sources.

.DESCRIPTION
    This script downloads 7-Zip 19.00 source code from 7-zip.org and merges it
    with the Nsis7z plugin files from the local archive to recreate the complete
    7zip-19.00 directory structure.

.NOTES
    Author: Simone
    Date: 2025-12-08
    
    Sources:
    - 7-Zip 19.00 source: https://7-zip.org/a/7z1900-src.7z
    - Nsis7z plugin: docs\plugins\original\ns7zip\Nsis7z_19.00.7z
#>

param(
    [switch]$Force,
    [string]$OutputPath = "$PSScriptRoot\7zip-19.00"
)

$ErrorActionPreference = "Stop"

# Paths
$ScriptDir = $PSScriptRoot
$TempDir = Join-Path $env:TEMP "nsis7z_rebuild_$(Get-Random)"
$SevenZipSrcUrl = "https://7-zip.org/a/7z1900-src.7z"
$Nsis7zArchive = Join-Path $ScriptDir "..\docs\plugins\original\ns7zip\Nsis7z_19.00.7z"

# Check if output already exists
if (Test-Path $OutputPath) {
    if ($Force) {
        Write-Host "Removing existing directory: $OutputPath" -ForegroundColor Yellow
        Remove-Item -Path $OutputPath -Recurse -Force
    } else {
        Write-Error "Output directory already exists: $OutputPath. Use -Force to overwrite."
        exit 1
    }
}

# Check if Nsis7z archive exists
if (-not (Test-Path $Nsis7zArchive)) {
    Write-Error "Nsis7z plugin archive not found: $Nsis7zArchive"
    exit 1
}

# Create temp directory
Write-Host "Creating temp directory: $TempDir" -ForegroundColor Cyan
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

try {
    # Download 7-Zip source
    $SevenZipSrcFile = Join-Path $TempDir "7z1900-src.7z"
    Write-Host "Downloading 7-Zip 19.00 source from $SevenZipSrcUrl..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $SevenZipSrcUrl -OutFile $SevenZipSrcFile -UseBasicParsing
    
    if (-not (Test-Path $SevenZipSrcFile)) {
        Write-Error "Failed to download 7-Zip source"
        exit 1
    }
    
    Write-Host "Download complete: $((Get-Item $SevenZipSrcFile).Length / 1KB) KB" -ForegroundColor Green

    # Extract 7-Zip source
    Write-Host "Extracting 7-Zip source..." -ForegroundColor Cyan
    $ExtractDir = Join-Path $TempDir "extracted"
    & 7z x $SevenZipSrcFile -o"$ExtractDir" -y | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to extract 7-Zip source"
        exit 1
    }

    # Extract Nsis7z plugin
    Write-Host "Extracting Nsis7z plugin..." -ForegroundColor Cyan
    $PluginDir = Join-Path $TempDir "plugin"
    & 7z x $Nsis7zArchive -o"$PluginDir" -y | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to extract Nsis7z plugin"
        exit 1
    }

    # Merge: Copy plugin files into 7-Zip source tree
    Write-Host "Merging plugin files into 7-Zip source tree..." -ForegroundColor Cyan
    $PluginContrib = Join-Path $PluginDir "Contrib\nsis7z"
    Copy-Item -Path "$PluginContrib\*" -Destination $ExtractDir -Recurse -Force

    # Move to final destination
    Write-Host "Moving to output directory: $OutputPath" -ForegroundColor Cyan
    Move-Item -Path $ExtractDir -Destination $OutputPath

    # Verify
    $FileCount = (Get-ChildItem -Path $OutputPath -Recurse -File).Count
    Write-Host "`nSuccess! Rebuilt nsis7z1900-src with $FileCount files." -ForegroundColor Green
    Write-Host "Output: $OutputPath" -ForegroundColor Green

} finally {
    # Cleanup temp directory
    if (Test-Path $TempDir) {
        Write-Host "`nCleaning up temp files..." -ForegroundColor Cyan
        Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
