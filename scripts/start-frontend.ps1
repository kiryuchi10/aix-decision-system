# PowerShell script to start frontend server
# Usage: .\scripts\start-frontend.ps1

Write-Host "🎨 Starting AiX Frontend Server..." -ForegroundColor Cyan

$frontendDir = Join-Path $PSScriptRoot "..\frontend"

if (-not (Test-Path $frontendDir)) {
    Write-Host "❌ Frontend directory not found: $frontendDir" -ForegroundColor Red
    exit 1
}

Set-Location $frontendDir

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
    npm install
}

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating..." -ForegroundColor Yellow
    @"
VITE_API_BASE_URL=http://localhost:8000
"@ | Out-File -FilePath ".env" -Encoding utf8
    Write-Host "✅ Created .env file." -ForegroundColor Green
}

# Start dev server
Write-Host "🌐 Starting Vite dev server..." -ForegroundColor Green
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

npm run dev
