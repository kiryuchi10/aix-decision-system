@echo off
REM CMD script to start backend server
REM Usage: scripts\start-backend.cmd

echo 🚀 Starting AiX Backend Server...

cd /d "%~dp0..\backend"

if not exist ".venv" (
    echo ⚠️  Virtual environment not found. Creating...
    python -m venv .venv
)

echo 📦 Activating virtual environment...
call .venv\Scripts\activate.bat

echo 🔍 Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo 📥 Installing dependencies...
    pip install -r requirements.txt
)

if not exist ".env" (
    echo ⚠️  .env file not found. Creating...
    (
        echo DATABASE_URL=mysql+pymysql://root:password@localhost:3306/aix_system
        echo SECRET_KEY=your-secret-key-change-in-production
        echo ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo ENVIRONMENT=development
    ) > .env
)

echo 🌐 Starting FastAPI server...
echo    API Docs: http://localhost:8000/docs
echo    Press Ctrl+C to stop
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
