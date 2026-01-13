@echo off
REM CMD script to start frontend server
REM Usage: scripts\start-frontend.cmd

echo 🎨 Starting AiX Frontend Server...

cd /d "%~dp0..\frontend"

if not exist "node_modules" (
    echo 📥 Installing dependencies...
    call npm install
)

if not exist ".env" (
    echo ⚠️  .env file not found. Creating...
    echo VITE_API_BASE_URL=http://localhost:8000 > .env
)

echo 🌐 Starting Vite dev server...
echo    Frontend: http://localhost:5173
echo    Press Ctrl+C to stop
echo.

call npm run dev

pause
