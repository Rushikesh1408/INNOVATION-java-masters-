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

2. Configure secrets and environment
   - Copy template to `.env` and fill required values.
   - Generate a strong password and keep it out of source control.
   - Example generation:
     - `openssl rand -base64 32`
   - Set shell variables before seeding:
     - `ADMIN_USERNAME=<your-admin-user>`
     - `ADMIN_PASSWORD=<GENERATED_STRONG_PASSWORD>`
   - Never commit `.env`.

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

# set credentials in your shell or .env first
python -m scripts.seed_admin

# run services
uvicorn app.main:app --reload
python scripts/run_celery_worker.py
```

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
