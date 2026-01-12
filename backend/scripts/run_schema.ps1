# PowerShell script to run schema.sql
# Usage: .\scripts\run_schema.ps1

param(
    [string]$DBName = "aix_system",
    [string]$DBUser = "root",
    [string]$DBPass = "",
    [string]$DBHost = "localhost",
    [int]$DBPort = 3306
)

$SCHEMA_FILE = "schema.sql"

if (-not (Test-Path $SCHEMA_FILE)) {
    Write-Host "❌ Schema file not found: $SCHEMA_FILE" -ForegroundColor Red
    exit 1
}

Write-Host "📄 Running schema.sql..." -ForegroundColor Yellow

if ($DBPass) {
    # With password
    Get-Content $SCHEMA_FILE -Raw | & mysql -h $DBHost -P $DBPort -u $DBUser -p$DBPass $DBName
} else {
    # Prompt for password
    Write-Host "Enter MySQL password for user '$DBUser':" -ForegroundColor Yellow
    Get-Content $SCHEMA_FILE -Raw | & mysql -h $DBHost -P $DBPort -u $DBUser -p $DBName
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Schema applied successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Schema application failed!" -ForegroundColor Red
    exit 1
}
