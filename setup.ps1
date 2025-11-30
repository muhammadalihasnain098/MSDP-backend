# Quick Setup Script for MSDP Backend
# Run this after cloning the repository

Write-Host "MSDP Backend Setup Script" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Cyan
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "Python 3\.1[0-9]" -or $pythonVersion -match "Python 3\.[2-9][0-9]") {
    Write-Host "[OK] $pythonVersion detected" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Python 3.10+ required. Please install from python.org" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Cyan
if (Test-Path "venv") {
    Write-Host "[SKIP] Virtual environment already exists" -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies (this may take a few minutes)..." -ForegroundColor Cyan
pip install -r requirements.txt

# Create .env file
Write-Host ""
Write-Host "Setting up environment variables..." -ForegroundColor Cyan
if (Test-Path ".env") {
    Write-Host "[SKIP] .env file already exists" -ForegroundColor Yellow
} else {
    Copy-Item ".env.example" ".env"
    
    # Generate SECRET_KEY
    $secretKey = python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
    (Get-Content ".env") -replace "your-secret-key-here-change-in-production", $secretKey | Set-Content ".env"
    
    Write-Host "[OK] .env file created with generated SECRET_KEY" -ForegroundColor Green
    Write-Host "[WARNING] Please update DATABASE_URL and REDIS_URL in .env" -ForegroundColor Yellow
}

# Create storage directories
Write-Host ""
Write-Host "Creating storage directories..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "storage/model_registry" | Out-Null
New-Item -ItemType Directory -Force -Path "media" | Out-Null
Write-Host "[OK] Directories created" -ForegroundColor Green

# Run migrations
Write-Host ""
Write-Host "Running database migrations..." -ForegroundColor Cyan
python manage.py migrate

# Create superuser
Write-Host ""
Write-Host "Create a superuser account..." -ForegroundColor Cyan
Write-Host "This will be your admin account for Django admin panel" -ForegroundColor Gray
python manage.py createsuperuser

# Success message
Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Update .env file with your database and Redis URLs" -ForegroundColor White
Write-Host "2. Start Django: python manage.py runserver" -ForegroundColor White
Write-Host "3. Start Celery Worker: celery -A config worker -l info" -ForegroundColor White
Write-Host "4. Start Celery Beat: celery -A config beat -l info" -ForegroundColor White
Write-Host ""
Write-Host "Admin panel: http://localhost:8000/admin/" -ForegroundColor Cyan
Write-Host "API docs: See README.md" -ForegroundColor Cyan
Write-Host ""
