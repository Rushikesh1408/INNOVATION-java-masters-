# Java Masters Exam Engine

Secure online examination platform built with FastAPI, React, PostgreSQL, Redis, and Celery-ready worker scaffolding.

## Quickstart (5 Commands)

```bash
pip install -r requirements.txt
docker compose up -d postgres redis
python scripts/seed_admin.py
uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

## Architecture

```text
Frontend (React + Tailwind)
  -> Load Balancer / CDN
  -> FastAPI API instances (stateless)
  -> Redis (cache + session state)
  -> PostgreSQL (source of truth)
  -> Celery workers (async/long-running jobs)
```

## Technology Stack

- Backend: FastAPI, SQLAlchemy, Pydantic, SlowAPI
- Frontend: React, React Router, Axios, Tailwind CSS, Vite
- Database: PostgreSQL
- Cache/State: Redis
- Worker: Celery (Redis broker/result backend)

## Current Backend Structure

```text
app/
  api/
    router.py
    routes/
      admin_reports.py
      auth.py
      contestants.py
      exams.py
      monitoring.py
  core/
    config.py
    deps.py
    logging_middleware.py
    redis_client.py
    security.py
  db/
    base.py
    init_db.py
    session.py
  models/
    admin.py
    exam.py
    log.py
    question.py
    response.py
    result.py
    session.py
    user.py
  repositories/
    admin_repository.py
    contestant_repository.py
    exam_repository.py
    log_repository.py
  schemas/
    auth.py
    contestant.py
    exam.py
    leaderboard.py
    log.py
    monitoring.py
    question.py
  services/
    auth_service.py
    contestant_service.py
    exam_service.py
    log_service.py
    monitoring_service.py
  workers/
    celery_app.py
    tasks.py
  database.py
  main.py
scripts/
  run_celery_worker.py
  seed_admin.py
docker-compose.yml
```

## Current Frontend Structure

```text
frontend/
  src/
    api/client.js
    hooks/useAntiCheat.js
    pages/
      AdminDashboardPage.jsx
      AdminLoginPage.jsx
      ContestantFormPage.jsx
      ExamPage.jsx
      HomePage.jsx
      NotFoundPage.jsx
      ResultPage.jsx
      RulesPage.jsx
    App.jsx
    main.jsx
    styles.css
```

## Implemented Features

### Admin

- JWT-based login
- Exam creation with marking scheme
  - `positive_mark`
  - `negative_mark`
- Question management (4-option MCQ)
- Monitoring dashboard API + WebSocket stream
- Leaderboard and CSV export
- Audit logs API

### Contestant

- Registration with unique email
- Exam start with UUID session
- Auto-save answer submissions
- Resume active session state from Redis
- Finish exam and view results/leaderboard

### Anti-Cheating and Integrity

- Tab switch/fullscreen exit telemetry
- Warning threshold and auto-submit
- Suspicious fast-answer flagging
- IP and device info capture
- Single active session enforcement

### Security and Reliability

- Bcrypt password hashing
- JWT expiry handling
- CORS allowlist
- Request audit middleware
- Rate limiting via SlowAPI
- Redis leaderboard caching
- Axios retry interceptor (frontend)

## Database Schema (Logical)

- `admins(id, username, password_hash)`
- `users(id, name, email unique)`
- `exams(id, title, time_limit, rules, positive_mark, negative_mark, created_by)`
- `questions(id, exam_id, question_text, option_1, option_2, option_3, option_4, correct_option)`
- `sessions(id UUID, user_id, exam_id, start_time, end_time, ip_address, device_info, status, warning_count, flagged)`
- `responses(id, session_id, question_id, selected_option, time_taken)`
- `results(id, user_id, exam_id, score, accuracy, total_time, flagged)`
- `logs(id, user_id nullable, action, context, timestamp)`

## Setup

### 1) Environment

Create `.env` from `.env.example`.

### 2) Install backend dependencies

```bash
pip install -r requirements.txt
```

### 3) Start infrastructure (PostgreSQL + Redis)

```bash
docker compose up -d postgres redis
```

### 4) Seed admin

```bash
set ADMIN_USERNAME=admin
set ADMIN_PASSWORD=replace-with-secure-password
python scripts/seed_admin.py
```

### 5) Run API

```bash
uvicorn app.main:app --reload
```

### 6) Run worker (optional)

```bash
python scripts/run_celery_worker.py
```

### 7) Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Overview

### Auth/Admin

- `POST /api/v1/auth/admin/login`
- `GET /api/v1/auth/admin/me`
- `GET /api/v1/admin/audit-logs?limit=100`
- `GET /api/v1/admin/results/{exam_id}/export`
- `GET /api/v1/admin/monitoring/active`
- `WS /api/v1/admin/monitoring/ws?token=<admin_jwt>`

### Exams

- `POST /api/v1/exams`
- `GET /api/v1/exams`
- `GET /api/v1/exams/{exam_id}`
- `POST /api/v1/exams/{exam_id}/questions`
- `GET /api/v1/exams/{exam_id}/questions`
- `PUT /api/v1/exams/{exam_id}/questions/{question_id}`
- `DELETE /api/v1/exams/{exam_id}/questions/{question_id}`

### Contestants

- `POST /api/v1/contestants/register`
- `POST /api/v1/contestants/start-exam`
- `POST /api/v1/contestants/resume`
- `POST /api/v1/contestants/submit-answer`
- `POST /api/v1/contestants/monitoring-event`
- `POST /api/v1/contestants/finish/{session_id}`
- `GET /api/v1/contestants/leaderboard/{exam_id}`

## Deployment Targets

- Backend: Render or Railway
- Frontend: Vercel or Netlify
- PostgreSQL: Supabase or Neon
- Redis: Managed Redis (or cloud provider addon)

## Production Notes

- Keep FastAPI instances stateless for horizontal scaling.
- Restrict `ALLOWED_ORIGINS` to exact frontend domains.
- Use HTTPS everywhere and secure secrets in platform env vars.
- Add Alembic migrations before production schema rollout.
- Configure scheduled backups (`pg_dump` or managed snapshots).
