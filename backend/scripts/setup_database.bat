@echo off
REM AiX Decision System Database Setup Script (Windows)
REM Run this from the backend directory

echo 🗄️  Setting up AiX Decision System Database...

set DB_NAME=aix_system
set DB_USER=root
set DB_PASS=password
set DB_HOST=localhost
set DB_PORT=3306

set SEED_DIR=app\data\seed
set SCHEMA_FILE=schema.sql

REM Step 1: Create database
echo.
echo Step 1: Creating database...
mysql -h %DB_HOST% -P %DB_PORT% -u %DB_USER% -p%DB_PASS% -e "CREATE DATABASE IF NOT EXISTS %DB_NAME% CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>nul
if errorlevel 1 (
    echo Please enter MySQL root password:
    mysql -h %DB_HOST% -P %DB_PORT% -u %DB_USER% -p -e "CREATE DATABASE IF NOT EXISTS %DB_NAME% CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
)
echo ✅ Database '%DB_NAME%' created

REM Step 2: Run schema.sql
if exist "%SCHEMA_FILE%" (
    echo.
    echo Step 2: Running schema.sql...
    mysql -h %DB_HOST% -P %DB_PORT% -u %DB_USER% -p%DB_PASS% %DB_NAME% < "%SCHEMA_FILE%" 2>nul
    if errorlevel 1 (
        echo Please enter MySQL root password:
        mysql -h %DB_HOST% -P %DB_PORT% -u %DB_USER% -p %DB_NAME% < "%SCHEMA_FILE%"
    )
    echo ✅ Schema applied
) else (
    echo ⚠️  Schema file not found: %SCHEMA_FILE%
)

REM Step 3: Import seed CSV files
if exist "%SEED_DIR%" (
    echo.
    echo Step 3: Importing seed CSV files...
    python scripts\import_seed_data.py
    if errorlevel 1 (
        echo ⚠️  Seed import failed. Check Python and dependencies.
    ) else (
        echo ✅ Seed files imported
    )
) else (
    echo ⚠️  Seed directory not found: %SEED_DIR%
)

echo.
echo ✅ Database setup complete!
echo.
echo 📊 Database: %DB_NAME%
echo 👤 User: %DB_USER%
echo 🌐 Host: %DB_HOST%:%DB_PORT%
echo.
echo You can now start the backend server with:
echo   uvicorn app.main:app --reload
pause
