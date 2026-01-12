# AiX Decision System Database Setup Script (PowerShell)
# Run this from the backend directory: .\scripts\setup_database.ps1

Write-Host "🗄️  Setting up AiX Decision System Database..." -ForegroundColor Cyan

$DB_NAME = if ($env:MYSQL_DATABASE) { $env:MYSQL_DATABASE } else { "aix_system" }
$DB_USER = if ($env:MYSQL_USER) { $env:MYSQL_USER } else { "root" }
$DB_PASS = if ($env:MYSQL_PASSWORD) { $env:MYSQL_PASSWORD } else { "password" }
$DB_HOST = if ($env:MYSQL_HOST) { $env:MYSQL_HOST } else { "localhost" }
$DB_PORT = if ($env:MYSQL_PORT) { $env:MYSQL_PORT } else { "3306" }

$SEED_DIR = "app\data\seed"
$SCHEMA_FILE = "schema.sql"

# Check if MySQL is available
$mysqlCmd = Get-Command mysql -ErrorAction SilentlyContinue
if (-not $mysqlCmd) {
    Write-Host "❌ MySQL client not found. Please install MySQL first." -ForegroundColor Red
    exit 1
}

# Check if Python is available
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $pythonCmd) {
    Write-Host "❌ Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# Step 1: Create database
Write-Host ""
Write-Host "Step 1: Creating database..." -ForegroundColor Yellow
$createDbCmd = "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
try {
    $result = & mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASS -e $createDbCmd 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Please enter MySQL root password:" -ForegroundColor Yellow
        & mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p -e $createDbCmd
    }
    Write-Host "✅ Database '$DB_NAME' created" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Database creation may have failed. Continuing..." -ForegroundColor Yellow
}

# Step 2: Run schema.sql
if (Test-Path $SCHEMA_FILE) {
    Write-Host ""
    Write-Host "Step 2: Running schema.sql..." -ForegroundColor Yellow
    try {
        # Use Get-Content and pipe to mysql (PowerShell way)
        $schemaContent = Get-Content $SCHEMA_FILE -Raw
        $schemaContent | & mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASS $DB_NAME 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Please enter MySQL root password:" -ForegroundColor Yellow
            $schemaContent | & mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p $DB_NAME
        }
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Schema applied" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Schema application may have failed. Check manually." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Schema application error: $_" -ForegroundColor Yellow
        Write-Host "💡 Try running manually: Get-Content schema.sql | mysql -u root -p aix_system" -ForegroundColor Cyan
    }
} else {
    Write-Host "⚠️  Schema file not found: $SCHEMA_FILE" -ForegroundColor Yellow
}

# Step 3: Import seed CSV files
if (Test-Path $SEED_DIR) {
    Write-Host ""
    Write-Host "Step 3: Importing seed CSV files..." -ForegroundColor Yellow
    try {
        & python scripts\import_seed_data.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Seed files imported" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Seed import may have failed. Check the output above." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Failed to run import script: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Seed directory not found: $SEED_DIR" -ForegroundColor Yellow
}

# Step 4: Run Alembic migrations (if available)
if (Test-Path "alembic") {
    Write-Host ""
    Write-Host "Step 4: Running Alembic migrations..." -ForegroundColor Yellow
    $alembicCmd = Get-Command alembic -ErrorAction SilentlyContinue
    if ($alembicCmd) {
        & alembic upgrade head
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Migrations applied" -ForegroundColor Green
        }
    } else {
        Write-Host "⚠️  Alembic not found. Skipping migrations." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✅ Database setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Database: $DB_NAME" -ForegroundColor Cyan
Write-Host "👤 User: $DB_USER" -ForegroundColor Cyan
Write-Host "🌐 Host: $DB_HOST`:$DB_PORT" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now start the backend server with:" -ForegroundColor Yellow
Write-Host "  uvicorn app.main:app --reload" -ForegroundColor White
