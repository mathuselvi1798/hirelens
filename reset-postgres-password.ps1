# ---------------------------------------------------------------------------
# One-time fix: reset the forgotten `postgres` superuser password and create
# the `hirelens` database, for Hirelens Phase 4.
#
# What this does, in order:
#   1. Stops the PostgreSQL Windows service
#   2. Backs up pg_hba.conf and temporarily allows trusted local connections
#   3. Starts PostgreSQL again (now password-free for local connections)
#   4. Sets a new, known password for the postgres user
#   5. Creates the `hirelens` database (skips if it already exists)
#   6. Restores the original, secure pg_hba.conf
#   7. Restarts PostgreSQL with normal password authentication restored
#
# MUST be run as Administrator (stopping/starting a Windows service requires
# it). Right-click this file's .bat wrapper and choose "Run as administrator".
# ---------------------------------------------------------------------------

$ErrorActionPreference = "Stop"

$PgBin      = "C:\Program Files\PostgreSQL\18\bin"
$PgData     = "C:\Program Files\PostgreSQL\18\data"
$HbaFile    = Join-Path $PgData "pg_hba.conf"
$HbaBackup  = Join-Path $PgData "pg_hba.conf.bak"
$ServiceName = "postgresql-x64-18"
$NewPassword = "HirelensDev2026"
$DbName      = "hirelens"

function Write-Step($msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

Write-Step "Stopping PostgreSQL service ($ServiceName)..."
Stop-Service -Name $ServiceName -Force
Start-Sleep -Seconds 2

Write-Step "Backing up pg_hba.conf..."
Copy-Item $HbaFile $HbaBackup -Force

Write-Step "Temporarily allowing trusted local connections..."
(Get-Content $HbaFile) -replace 'scram-sha-256', 'trust' | Set-Content $HbaFile

Write-Step "Starting PostgreSQL service..."
Start-Service -Name $ServiceName
Start-Sleep -Seconds 3

Write-Step "Setting a new password for the postgres user..."
$env:PGPASSWORD = ""
& "$PgBin\psql.exe" -U postgres -h 127.0.0.1 -p 5432 -c "ALTER USER postgres WITH PASSWORD '$NewPassword';"

Write-Step "Creating the '$DbName' database (skipping if it already exists)..."
try {
    & "$PgBin\psql.exe" -U postgres -h 127.0.0.1 -p 5432 -c "CREATE DATABASE $DbName;" 2>$null
} catch {
    Write-Host "   ($DbName already exists - fine, continuing)"
}

Write-Step "Restoring the original, secure pg_hba.conf..."
Copy-Item $HbaBackup $HbaFile -Force
Remove-Item $HbaBackup

Write-Step "Restarting PostgreSQL with normal password authentication..."
Restart-Service -Name $ServiceName
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " Done."
Write-Host " postgres password is now: $NewPassword"
Write-Host " Database '$DbName' is ready on localhost:5432"
Write-Host "============================================================" -ForegroundColor Green
