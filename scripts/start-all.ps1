# PowerShell script to start both backend and frontend
# Usage: .\scripts\start-all.ps1

Write-Host "🚀 Starting AiX Decision System..." -ForegroundColor Cyan
Write-Host ""

# Start backend in background
Write-Host "📡 Starting Backend..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot\..\backend
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & ".venv\Scripts\Activate.ps1"
    }
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Start frontend in background
Write-Host "🎨 Starting Frontend..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot\..\frontend
    npm run dev
}

Write-Host ""
Write-Host "✅ Both servers started!" -ForegroundColor Green
Write-Host "   Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop all servers" -ForegroundColor Yellow
Write-Host ""

# Wait for user interrupt
try {
    while ($true) {
        Start-Sleep -Seconds 1
        # Check if jobs are still running
        if ($backendJob.State -eq "Failed" -or $frontendJob.State -eq "Failed") {
            Write-Host "❌ One or more servers failed!" -ForegroundColor Red
            break
        }
    }
} finally {
    Write-Host "🛑 Stopping servers..." -ForegroundColor Yellow
    Stop-Job $backendJob, $frontendJob
    Remove-Job $backendJob, $frontendJob
    Write-Host "✅ Servers stopped." -ForegroundColor Green
}
