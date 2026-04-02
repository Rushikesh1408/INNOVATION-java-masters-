#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Java Masters Exam Engine - System Startup Script (Windows PowerShell)

.DESCRIPTION
    Starts all required services for the complete exam platform:
    - FastAPI backend (port 8000)
    - Celery worker for async evaluation
    - Redis (if available)  
    - Optional: Frontend dev server
    - Optional: Celery Flower monitoring UI

.EXAMPLE
    .\START_SYSTEM.ps1
    .\START_SYSTEM.ps1 -IncludeFrontend
    .\START_SYSTEM.ps1 -IncludeFlower

.NOTES
    Requirements:
    - Python 3.11+
    - Redis server (optional, required for Celery)
    - Node.js (optional, for frontend)
#>

param(
    [switch]$IncludeFrontend = $false,
    [switch]$IncludeFlower = $false,
    [ValidateRange(1, 65535)]
    [int]$ApiPort = 8000,
    [ValidateRange(1, 65535)]
    [int]$FrontendPort = 5173
)

# Color helpers
function Write-Success { Write-Host @args -ForegroundColor Green }
function Write-Info { Write-Host @args -ForegroundColor Cyan }
function Write-WarnMsg { Write-Host @args -ForegroundColor Yellow }
function Write-ErrorMessage { Write-Host @args -ForegroundColor Red }

Write-Info "
╔════════════════════════════════════════════════════════════════╗
║     JAVA MASTERS EXAM ENGINE - SYSTEM STARTUP                  ║
║     Production-Ready Full-Stack Exam Platform                  ║
╚════════════════════════════════════════════════════════════════╝
"

# Discover Python command
$pythonCmd = $null
$pythonPrefixArgs = @()

$pythonCandidate = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCandidate) {
    $pythonCandidate = Get-Command python3 -ErrorAction SilentlyContinue
}

if ($pythonCandidate) {
    $pythonCmd = $pythonCandidate.Source
} elseif ($env:PYTHON_HOME -and (Test-Path (Join-Path $env:PYTHON_HOME "python.exe"))) {
    $pythonCmd = Join-Path $env:PYTHON_HOME "python.exe"
} else {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        $pythonCmd = $pyLauncher.Source
        $pythonPrefixArgs = @("-3")
    }
}

# Verify Python
Write-Info "[1/5] Verifying Python installation..."
try {
    if (-not $pythonCmd) {
        throw "Python interpreter not found"
    }
    $version = & $pythonCmd @pythonPrefixArgs --version 2>&1
    Write-Success "  ✅ $version"
} catch {
    Write-ErrorMessage "  ❌ Python not found in PATH, PYTHON_HOME, or py launcher"
    exit 1
}

# Check key dependencies
Write-Info "[2/5] Verifying dependencies..."
$deps = @("fastapi", "sqlalchemy", "celery", "redis")
$missing = @()
foreach ($dep in $deps) {
    $check = & $pythonCmd @pythonPrefixArgs -c "import $dep; print('ok')" 2>&1
    if ($check -eq "ok") {
        Write-Success "  ✅ $dep"
    } else {
        Write-WarnMsg "  ⚠️  $dep (optional)"
        if ($dep -in @("fastapi", "sqlalchemy")) {
            $missing += $dep
        }
    }
}

if ($missing.Count -gt 0) {
    Write-ErrorMessage "  ❌ Missing required packages: $($missing -join ', ')"
    Write-Info "  Run: pip install -r requirements.txt"
    exit 1
}

# Optional: Check Redis
Write-Info "[3/5] Checking Redis (optional)..."
try {
    $redis_check = & redis-cli ping 2>&1
    if ($redis_check -eq "PONG") {
        Write-Success "  ✅ Redis running on localhost:6379"
        $hasRedis = $true
    } else {
        Write-WarnMsg "  ⚠️  Redis not accessible (Celery will fail without it)"
        $hasRedis = $false
    }
} catch {
    Write-WarnMsg "  ⚠️  Redis not found (install redis-server or use WSL)"
    $hasRedis = $false
}

# Check database
Write-Info "[4/5] Checking database..."
try {
    $pgReady = Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue
    if ($pgReady.TcpTestSucceeded) {
        Write-Success "  ✅ PostgreSQL reachable on localhost:5432"
    } else {
        Write-WarnMsg "  ⚠️  PostgreSQL not reachable on localhost:5432"
    }
} catch {
    Write-WarnMsg "  ⚠️  Unable to verify PostgreSQL connectivity"
}

# Create startup commands
Write-Info "[5/5] Preparing startup services..."
Write-Success "  ✅ Services configured"

# Display startup info
Write-Info "
╔════════════════════════════════════════════════════════════════╗
║                    STARTUP INSTRUCTIONS                        ║
╚════════════════════════════════════════════════════════════════╝

Open 3-4 Terminal Windows and run these commands:

TERMINAL 1 - FastAPI Backend (Required)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
uvicorn app.main:app --reload --port $ApiPort

TERMINAL 2 - Celery Worker (Required for code evaluation)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
python scripts/run_celery_worker.py

╔════════════════════════════════════════════════════════════════╗
║                      ACCESS POINTS                             ║
╚════════════════════════════════════════════════════════════════╝

API Documentation:     http://localhost:$ApiPort/docs
Interactive API:       http://localhost:$ApiPort/redoc
Frontend (React):      http://localhost:$FrontendPort (if started)
Celery Flower UI:      http://localhost:5555 (if started)
Health Check:          http://localhost:$ApiPort/health

╔════════════════════════════════════════════════════════════════╗
║                    QUICK TEST COMMANDS                         ║
╚════════════════════════════════════════════════════════════════╝

Test Admin Login:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Development-only example. Do not use shared/default credentials in production.
Set `$env:ADMIN_USERNAME` and `$env:ADMIN_PASSWORD` before running this command.

@'
curl -X POST http://localhost:8000/api/v1/auth/admin/login `
  -H 'Content-Type: application/json' `
  -d "{\"username\":\"<ADMIN_USERNAME>\",\"password\":\"<ADMIN_PASSWORD>\"}"
'@ | Write-Host

Run Demo (End-to-End Workflow):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
python demo.py

Get API Health:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
curl http://localhost:$ApiPort/health
"

if ($IncludeFrontend) {
    Write-Info "
TERMINAL 3 - Frontend Development Server (Optional)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
cd frontend
npm install
npm run dev
"
} else {
    Write-Info "`nFrontend instructions hidden. Use -IncludeFrontend to display them."
}

if ($IncludeFlower) {
    Write-Info "
TERMINAL 4 - Celery Flower UI (Optional - monitoring)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
celery -A app.workers.celery_app flower --port 5555
"
} else {
    Write-Info "Flower instructions hidden. Use -IncludeFlower to display them."
}

# Auto-startup option
$startNow = Read-Host "Would you like to start the API server now? (y/n)"
if ($startNow -eq "y" -or $startNow -eq "Y") {
    Write-Info "`nStarting FastAPI server..."
    & $pythonCmd @pythonPrefixArgs -m uvicorn app.main:app --reload --port $ApiPort
} else {
    Write-Info "`n✅ System check complete. Ready to start services manually."
    Write-Info "Copy commands from instructions above into separate terminal windows."
}
