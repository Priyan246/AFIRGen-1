# Frontend Configuration Deployment Script (PowerShell)
# Usage: .\deploy-config.ps1 -Environment production
# Example: .\deploy-config.ps1 -Environment production -ApiBaseUrl "https://api.afirgen.com"

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('production', 'staging', 'development')]
    [string]$Environment = 'development',
    
    [Parameter(Mandatory=$false)]
    [string]$ApiBaseUrl = '',
    
    [Parameter(Mandatory=$false)]
    [string]$ConfigFile = 'config.js'
)

Write-Host "Configuring frontend for environment: $Environment" -ForegroundColor Cyan

# Set defaults based on environment
switch ($Environment) {
    'production' {
        if ([string]::IsNullOrEmpty($ApiBaseUrl)) {
            $ApiBaseUrl = $env:API_BASE_URL
            if ([string]::IsNullOrEmpty($ApiBaseUrl)) {
                $ApiBaseUrl = 'https://api.afirgen.com'
            }
        }
        $Debug = 'false'
    }
    'staging' {
        if ([string]::IsNullOrEmpty($ApiBaseUrl)) {
            $ApiBaseUrl = $env:API_BASE_URL
            if ([string]::IsNullOrEmpty($ApiBaseUrl)) {
                $ApiBaseUrl = 'https://staging-api.afirgen.com'
            }
        }
        $Debug = 'false'
    }
    'development' {
        if ([string]::IsNullOrEmpty($ApiBaseUrl)) {
            $ApiBaseUrl = $env:API_BASE_URL
            if ([string]::IsNullOrEmpty($ApiBaseUrl)) {
                $ApiBaseUrl = 'http://localhost:8000'
            }
        }
        $Debug = 'true'
    }
}

Write-Host "API Base URL: $ApiBaseUrl" -ForegroundColor Green
Write-Host "Debug Mode: $Debug" -ForegroundColor Green

# Backup original config
$BackupFile = "$ConfigFile.backup"
if (-not (Test-Path $BackupFile)) {
    Copy-Item $ConfigFile $BackupFile
    Write-Host "Created backup: $BackupFile" -ForegroundColor Yellow
}

# Read config file
$content = Get-Content $ConfigFile -Raw

# Update configuration values
$content = $content -replace "API_BASE_URL: '[^']*'", "API_BASE_URL: '$ApiBaseUrl'"
$content = $content -replace "ENVIRONMENT: '[^']*'", "ENVIRONMENT: '$Environment'"
$content = $content -replace "ENABLE_DEBUG: [^,]*,", "ENABLE_DEBUG: $Debug,"

# Write updated config
Set-Content -Path $ConfigFile -Value $content -NoNewline

Write-Host "`n✓ Frontend configuration updated successfully" -ForegroundColor Green
Write-Host "`nVerify configuration:" -ForegroundColor Cyan
Write-Host "  Get-Content $ConfigFile | Select-String 'API_BASE_URL'" -ForegroundColor Gray
