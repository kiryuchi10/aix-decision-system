# PowerShell script to start backend server
# Usage: .\scripts\start-backend.ps1

Write-Host "🚀 Starting AiX Backend Server..." -ForegroundColor Cyan

$backendDir = Join-Path $PSScriptRoot "..\backend"

if (-not (Test-Path $backendDir)) {
    Write-Host "❌ Backend directory not found: $backendDir" -ForegroundColor Red
    exit 1
}

Set-Location $backendDir

# Check if virtual environment exists
$venvPath = Join-Path $backendDir ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "⚠️  Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
& "$venvPath\Scripts\Activate.ps1"

# Check if requirements are installed
Write-Host "🔍 Checking dependencies..." -ForegroundColor Yellow
pip show fastapi | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from template..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Created .env file. Please update with your configuration." -ForegroundColor Green
    } else {
        Write-Host "⚠️  .env.example not found. Creating basic .env..." -ForegroundColor Yellow
        @"
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/aix_system
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=development
"@ | Out-File -FilePath ".env" -Encoding utf8
    }
}

# Start server
Write-Host "🌐 Starting FastAPI server..." -ForegroundColor Green
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
