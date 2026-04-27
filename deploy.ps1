# ITAM Windows Server Deployment Script
# Run this script as Administrator in PowerShell

param(
    [string]$InstallPath = "C:\inetpub\itam",
    [string]$SiteName = "ITAM",
    [int]$Port = 80
)

$ErrorActionPreference = "Stop"

Write-Host "ITAM Deployment Script for Windows Server" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Please run this script as Administrator" -ForegroundColor Red
    exit 1
}

# Step 1: Install IIS
Write-Host "`n[1/8] Installing IIS..." -ForegroundColor Yellow
Install-WindowsFeature Web-Server -IncludeManagementTools

# Step 2: Install URL Rewrite
Write-Host "[2/8] Installing URL Rewrite..." -ForegroundColor Yellow
$rewritePath = "$env:TEMP\rewrite_amd64_en-US.msi"
if (-not (Test-Path "C:\Windows\System32\inetsrv\urlrewrite.dll")) {
    Invoke-WebRequest -Uri "https://aka.ms/urlrewrite" -OutFile $rewritePath
    Start-Process msiexec.exe -ArgumentList "/i $rewritePath /quiet /norestart" -Wait
    Remove-Item $rewritePath -Force
}

# Step 3: Create directory
Write-Host "[3/8] Creating directory..." -ForegroundColor Yellow
if (-not (Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force
}

# Step 4: Copy files
Write-Host "[4/8] Copying application files..." -ForegroundColor Yellow
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($scriptDir -ne $InstallPath) {
    Copy-Item -Path "$scriptDir\*" -Destination $InstallPath -Recurse -Force -Exclude ".venv"
}

# Step 5: Setup virtual environment
Write-Host "[5/8] Setting up virtual environment..." -ForegroundColor Yellow
Set-Location $InstallPath
python -m venv .venv
& "$InstallPath\.venv\Scripts\Activate.ps1"

# Step 6: Install dependencies
Write-Host "[6/8] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
pip install wfastcgi
wfastcgi-enable

# Step 7: Configure environment
Write-Host "[7/8] Configuring environment..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    $secretKey = python -c "import secrets; print(secrets.token_hex(50))"
    (Get-Content ".env") -replace "your-secure-secret-key-here", $secretKey | Set-Content ".env"
}

# Step 8: Setup database
Write-Host "[8/8] Setting up database..." -ForegroundColor Yellow
python manage.py migrate
python manage.py collectstatic --noinput

# Create superuser if needed
Write-Host "`nCreating superuser account..." -ForegroundColor Yellow
$exists = python -c "import django; django.setup(); from accounts.models import User; print(User.objects.filter(username='admin').exists())"
if ($exists -eq "False") {
    python manage.py shell -c "from accounts.models import User; User.objects.create_superuser('admin', 'admin@itam.local', 'admin123')"
}

# Restart IIS
Write-Host "`nRestarting IIS..." -ForegroundColor Yellow
Restart-Service W3SVC -Force

Write-Host "`nDeployment complete!" -ForegroundColor Green
Write-Host "Site URL: http://localhost:$Port" -ForegroundColor Cyan
Write-Host "Admin URL: http://localhost:$Port/admin" -ForegroundColor Cyan
Write-Host "Credentials: admin / admin123" -ForegroundColor Yellow