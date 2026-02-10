# Run MySQL init for .env (aix_decision_db, aix_user, aix_pass)
# From backend folder: .\scripts\run_mysql_init_env.ps1
# Requires: mysql client in PATH. You will be prompted for root password.

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Split-Path -Parent $scriptDir
$sqlFile = Join-Path $scriptDir "mysql_init_env.sql"

if (-not (Test-Path $sqlFile)) {
    Write-Error "Not found: $sqlFile"
    exit 1
}

Write-Host "Running MySQL init (aix_decision_db / aix_user) from $sqlFile"
Write-Host "You will be prompted for MySQL root password."
Get-Content $sqlFile -Raw | mysql -u root -p
if ($LASTEXITCODE -eq 0) {
    Write-Host "Done. Backend .env DATABASE_URL=mysql+pymysql://aix_user:aix_pass@localhost:3306/aix_decision_db should work."
} else {
    Write-Host "MySQL command failed. Check root password and that mysql is in PATH."
    exit 1
}
