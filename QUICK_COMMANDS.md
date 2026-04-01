# Java Masters Exam Engine - Quick Commands

This file is documentation. It is not an executable script.

## Setup Variables (PowerShell)
```powershell
$JAVAMS_ROOT = (Resolve-Path .).Path
$env:ADMIN_USERNAME = $env:ADMIN_USERNAME
$env:ADMIN_PASSWORD = $env:ADMIN_PASSWORD
```

Note: create a local `.env` file from the template and set real credentials before running commands. Never commit `.env`.

## Start Commands (PowerShell)
```powershell
Set-Location $JAVAMS_ROOT
pip install -r requirements.txt

if (-not $env:ADMIN_USERNAME -or -not $env:ADMIN_PASSWORD) {
  throw "Set ADMIN_USERNAME and ADMIN_PASSWORD in your shell or .env before seeding."
}
python -m scripts.seed_admin

python -m uvicorn app.main:app --reload --port 8000
```

In a second terminal:
```powershell
Set-Location $JAVAMS_ROOT
python scripts/run_celery_worker.py
```

Optional frontend terminal:
```powershell
Set-Location (Join-Path $JAVAMS_ROOT "frontend")
npm install
npm run dev
```

## Health and Login Checks
```powershell
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/auth/admin/login `
  -H 'Content-Type: application/json' `
  -d "{\"username\":\"$env:ADMIN_USERNAME\",\"password\":\"$env:ADMIN_PASSWORD\"}"
```

## Cross-Platform Seeding
PowerShell:
```powershell
$env:ADMIN_USERNAME="<your-admin-user>"
$env:ADMIN_PASSWORD="<your-strong-password>"
python -m scripts.seed_admin
```

Bash/Zsh:
```bash
export ADMIN_USERNAME="<your-admin-user>"
export ADMIN_PASSWORD="<your-strong-password>"
python -m scripts.seed_admin
```

## Python Version
Use Python 3.11+ (tested with Python 3.13.x).

## Paths
Run commands from repository root. Prefer `python` from PATH instead of hardcoded user-specific interpreter paths.
