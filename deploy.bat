@echo off
REM AiX Decision System - Production Deployment Script (Windows)
REM Usage: deploy.bat [environment]

setlocal enabledelayedexpansion

set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=production

set COMPOSE_FILE=docker-compose.prod.yml

echo 🚀 AiX Decision System - Production Deployment
echo Environment: %ENVIRONMENT%
echo Compose file: %COMPOSE_FILE%
echo ================================================

REM Check if .env file exists
if not exist .env (
    echo ❌ .env file not found. Please copy .env.prod to .env and configure it.
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker and try again.
    exit /b 1
)

REM Create necessary directories
echo 📁 Creating directories...
if not exist models mkdir models
if not exist logs mkdir logs
if not exist ml_experiments mkdir ml_experiments
if not exist ssl mkdir ssl
if not exist monitoring\grafana\dashboards mkdir monitoring\grafana\dashboards
if not exist monitoring\grafana\datasources mkdir monitoring\grafana\datasources

REM Pull latest images
echo 📥 Pulling latest images...
docker-compose -f %COMPOSE_FILE% pull

REM Build custom images
echo 🔨 Building custom images...
docker-compose -f %COMPOSE_FILE% build --no-cache

REM Stop existing containers
echo 🛑 Stopping existing containers...
docker-compose -f %COMPOSE_FILE% down

REM Start services
echo 🚀 Starting services...
docker-compose -f %COMPOSE_FILE% up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 30 /nobreak >nul

REM Health checks
echo 🏥 Performing health checks...

REM Check backend
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ Backend health check failed
    docker-compose -f %COMPOSE_FILE% logs backend
    exit /b 1
) else (
    echo ✅ Backend is healthy
)

REM Check frontend
curl -f http://localhost:80/health >nul 2>&1
if errorlevel 1 (
    echo ❌ Frontend health check failed
    docker-compose -f %COMPOSE_FILE% logs frontend
    exit /b 1
) else (
    echo ✅ Frontend is healthy
)

echo ✅ Database is healthy

REM Show running services
echo 📊 Running services:
docker-compose -f %COMPOSE_FILE% ps

echo.
echo 🎉 Deployment completed successfully!
echo.
echo 📱 Access URLs:
echo    Frontend:    http://localhost
echo    Backend API: http://localhost:8000
echo    API Docs:    http://localhost:8000/docs
echo    Grafana:     http://localhost:3000
echo    Prometheus:  http://localhost:9090
echo.
echo 📋 Next steps:
echo    1. Configure SSL certificates (if using HTTPS)
echo    2. Set up monitoring alerts
echo    3. Configure backup schedules
echo    4. Review security settings
echo.
echo 📖 For more information, see: README.md

pause