# Certificate Generation Script for AFIRGen (PowerShell)
# Supports self-signed certificates for development

param(
    [string]$Domain = "localhost",
    [string]$Country = "US",
    [string]$State = "State",
    [string]$City = "City",
    [string]$Organization = "AFIRGen",
    [int]$ValidityDays = 365
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "AFIRGen TLS Certificate Generator" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$SslDir = Join-Path $ProjectRoot "nginx\ssl"

# Create SSL directory if it doesn't exist
if (-not (Test-Path $SslDir)) {
    New-Item -ItemType Directory -Path $SslDir -Force | Out-Null
}

Write-Host "Generating self-signed certificate..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Domain: $Domain"
Write-Host "Country: $Country"
Write-Host "State: $State"
Write-Host "City: $City"
Write-Host "Organization: $Organization"
Write-Host "Validity: $ValidityDays days"
Write-Host ""

# Check if OpenSSL is available
$opensslPath = Get-Command openssl -ErrorAction SilentlyContinue

if (-not $opensslPath) {
    Write-Host "Error: OpenSSL is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install OpenSSL:" -ForegroundColor Yellow
    Write-Host "  1. Download from: https://slproweb.com/products/Win32OpenSSL.html"
    Write-Host "  2. Or install via Chocolatey: choco install openssl"
    Write-Host "  3. Or use Git Bash which includes OpenSSL"
    Write-Host ""
    exit 1
}

# Generate certificate using OpenSSL
$certPath = Join-Path $SslDir "cert.pem"
$keyPath = Join-Path $SslDir "key.pem"
$subject = "/C=$Country/ST=$State/L=$City/O=$Organization/CN=$Domain"

$opensslArgs = @(
    "req", "-x509", "-nodes",
    "-days", $ValidityDays,
    "-newkey", "rsa:2048",
    "-keyout", $keyPath,
    "-out", $certPath,
    "-subj", $subject
)

try {
    & openssl $opensslArgs
    
    if ($LASTEXITCODE -ne 0) {
        throw "OpenSSL command failed with exit code $LASTEXITCODE"
    }
    
    Write-Host ""
    Write-Host "✓ Self-signed certificate generated successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Certificate location: $certPath"
    Write-Host "Private key location: $keyPath"
    Write-Host ""
    Write-Host "WARNING: Self-signed certificates are for development only!" -ForegroundColor Yellow
    Write-Host "Browsers will show security warnings. For production, use Let's Encrypt."
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Certificate setup complete!" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "1. Update docker-compose.yaml to use the nginx reverse proxy"
    Write-Host "2. Update frontend config.js to use HTTPS URLs"
    Write-Host "3. Start the services: docker-compose up -d"
    Write-Host ""
}
catch {
    Write-Host ""
    Write-Host "Error generating certificate: $_" -ForegroundColor Red
    exit 1
}
