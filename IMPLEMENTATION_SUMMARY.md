# Java Masters Exam Engine - Implementation Summary

Project: Full-stack exam platform with MCQ and Java coding rounds.

Status: Production-ready with caveats.

Before production go-live, complete these items:
- Validate PostgreSQL backup/restore and credential rotation.
- Replace weak/default credential examples and enforce strong password policy.
- Enable TLS/HTTPS and secure transport defaults.
- Run a formal security audit and penetration test.

## Scope Delivered
- Quiz round (MCQ) with scoring and leaderboard.
- Java coding round with visible/hidden test cases.
- Async evaluation with Celery.
- Admin APIs and reporting.
- Frontend coding page with Monaco editor.

## Setup Steps
1. Environment setup
   - `pip install -r requirements.txt`

2. PostgreSQL setup
  - Install PostgreSQL 14 or newer.
  - Create the application database.
  - Set `DATABASE_URL` in `.env` or export it in your shell.
  - Run migrations with `alembic upgrade head`.

3. Initialize database and admin
   - `python -m scripts.seed_admin`

4. Start services
   - API: `uvicorn app.main:app --reload --port 8000`
   - Worker: `python scripts/run_celery_worker.py`
   - Frontend (optional): `cd frontend && npm install && npm run dev`

## Quick Start
```bash
# from repository root
pip install -r requirements.txt

# install and initialize PostgreSQL 14+
# create the database, set DATABASE_URL, then run migrations
alembic upgrade head

# set credentials in your shell or .env first
python -m scripts.seed_admin

# run services
uvicorn app.main:app --reload
python scripts/run_celery_worker.py
```

## Database Operations

### Backup
```bash
pg_dump "$DATABASE_URL" > backup.sql
```

### Restore
```bash
psql "$DATABASE_URL" < backup.sql
```

### Credential Rotation
1. Generate a new password.
2. Run `ALTER USER <db_user> WITH PASSWORD '<new_password>';` in PostgreSQL.
3. Update `DATABASE_URL` in `.env` or your secret manager.
4. Restart the API and worker services.

Admin login check (replace placeholders):
```bash
curl -X POST http://localhost:8000/api/v1/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"<ADMIN_USERNAME>","password":"<ADMIN_PASSWORD>"}'
```

## Security Notes
- Current implementation uses subprocess execution with timeout and JVM heap limit (`-Xmx`) as baseline controls.
- Subprocess execution is not a complete security boundary by itself.
- For production isolation, use container sandboxing and OS-level controls:
  - Container isolation (Docker/gVisor/Firecracker)
  - Network namespace isolation / egress restrictions
  - Read-only filesystem mounts and restricted writable paths
  - seccomp/AppArmor/SELinux policies
  - cgroups for CPU/memory/process limits

## Testing
- Use `demo.py` for end-to-end flow checks.
- Validate coding task worker path by submitting code and polling submission status.
- Verify leaderboard behavior with multiple submissions per user/problem.

## Compatibility
- Minimum Python: 3.11+
- Tested runtime documentation target: Python 3.13.x
- Java: JDK 11+
- PostgreSQL: 14+
