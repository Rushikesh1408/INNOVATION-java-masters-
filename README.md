# Masters Exam Engine

"Java" in this project name refers to exam content/domain, not the implementation language.

Production-ready full-stack online examination platform with:

- FastAPI backend (modular layered architecture)
- React frontend (role-based UI)
- PostgreSQL data layer (normalized schema)
- Redis cache/session state
- Celery worker scaffolding for heavy/async tasks
- Anti-cheating telemetry and server-side flagging

## Production Architecture

```text
Frontend (React)
	-> Load Balancer / CDN
	-> FastAPI API instances (stateless)
	-> Redis (cache/session state)
	-> PostgreSQL (system of record)
	-> Celery workers (async/long-running jobs)
```

## Implemented Architecture

### High-level flow

1. React frontend calls FastAPI REST APIs.
2. Contestant runtime sends anti-cheat events (tab switch/fullscreen exits).
3. FastAPI services enforce exam/session policies.
4. SQLAlchemy repositories persist data in PostgreSQL.
5. Leaderboard is computed from results sorted by accuracy desc, time asc.

### Layer responsibilities

- API Layer: request/response contracts and access control.
- Service Layer: business logic and anti-cheat rules.
- Repository Layer: persistence and query isolation.
- Database Layer: relational constraints, indexing, and data integrity.

## Backend structure

```text
app/
	database.py
	api/
		router.py
		routes/
			admin_reports.py
			auth.py
			exams.py
			contestants.py
			monitoring.py
	routes/
		exam_routes.py
	core/
		config.py
		deps.py
		logging_middleware.py
		security.py
	db/
		base.py
		init_db.py
		session.py
	models/
		admin.py
		user.py
		exam.py
		log.py
		question.py
		session.py
		response.py
		result.py
	repositories/
		admin_repository.py
		exam_repository.py
		contestant_repository.py
		log_repository.py
	schemas/
		auth.py
		exam.py
		question.py
		contestant.py
		leaderboard.py
		log.py
		monitoring.py
	services/
		auth_service.py
		exam_service.py
		contestant_service.py
		log_service.py
		monitoring_service.py
	workers/
		celery_app.py
		tasks.py
	utils/
		settings.py
	main.py
scripts/
	seed_admin.py
	run_celery_worker.py
	docker-compose.yml
```

## Frontend structure

```text
frontend/
	src/
		api/client.js
		hooks/useAntiCheat.js
		pages/
			RoleSelectionPage.jsx
			AdminDashboardPage.jsx
			ContestantExamPage.jsx
		App.jsx
		main.jsx
		styles.css
```

## Core Features Implemented

### Admin

- JWT admin login endpoint.
- Create exams.
- Add/list MCQ questions with 4 options.
- View exams and leaderboard.
- Export results CSV (`/api/v1/admin/results/{exam_id}/export`).
- View audit logs (`/api/v1/admin/audit-logs`).
- Live monitoring snapshots + WebSocket stream (`/api/v1/admin/monitoring/*`).

### Contestant

- Register with unique email.
- Start exam session with UUID tracking.
- Submit question responses with time-per-question.
- Finish exam and generate results.
- Resume-friendly session state persisted in Redis cache.

### Anti-cheating

- Frontend:
	- Fullscreen attempt on exam start.
	- Page visibility tracking for tab switching.
	- Fullscreen exit tracking.
	- Basic context menu and clipboard shortcut blocking.
- Backend:
	- Session warning counter.
	- Auto-submit when warning threshold is reached.
	- Suspicious fast-response flagging.
	- IP address and device info capture.
	- Single active session per user+exam enforced.
	- Audit log entries for start, answer submit, monitoring events, and submission.

### Security

- Admin JWT auth.
- Password hashing via bcrypt.
- CORS allowlist through environment config.
- Server-side validation using Pydantic.
- Request audit middleware.
- SlowAPI limiter integrated at app level.
- Redis-backed leaderboard caching.

## Database schema

Tables implemented:

- `admins(id, username, password_hash)`
- `users(id, name, email unique)`
- `exams(id, title, time_limit, rules, created_by)`
- `questions(id, exam_id, question_text, option_1, option_2, option_3, option_4, correct_option)`
- `sessions(id UUID, user_id, exam_id, start_time, end_time, ip_address, device_info, status, warning_count, flagged)`
- `responses(id, session_id, question_id, selected_option, time_taken)`
- `results(id, user_id, exam_id, score, accuracy, total_time, flagged)`
- `logs(id, user_id nullable, action, context, timestamp)`

Indexes included for session lookup, response uniqueness per question, and leaderboard sort paths.

## Environment setup

### Backend

1. Create `.env` from `.env.example`.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start infrastructure (PostgreSQL + Redis) with Docker:

```bash
docker compose up -d postgres redis
```

4. Seed admin user:

```bash
set ADMIN_USERNAME=admin
set ADMIN_PASSWORD=replace-with-secure-password
python scripts/seed_admin.py
```

5. Run API with uvicorn:

```bash
uvicorn app.main:app --reload
```

6. Run Celery worker (optional async workloads):

```bash
python scripts/run_celery_worker.py
```

### Frontend

1. Create `frontend/.env` from `frontend/.env.example`.
2. Install dependencies:

```bash
cd frontend
npm install
```

3. Start dev server:

```bash
npm run dev
```

## Deployment model

- Frontend: Vercel or Netlify.
- Backend: Render or Railway.
- PostgreSQL: Supabase or Neon.
- Configure CORS allowlist and environment secrets per platform.

## API endpoints (starter)

- `POST /api/v1/auth/admin/login`
- `POST /api/v1/exams` (admin)
- `GET /api/v1/exams`
- `POST /api/v1/exams/{exam_id}/questions` (admin)
- `GET /api/v1/exams/{exam_id}/questions`
- `POST /api/v1/contestants/register`
- `POST /api/v1/contestants/start-exam`
- `POST /api/v1/contestants/submit-answer`
- `POST /api/v1/contestants/monitoring-event`
- `POST /api/v1/contestants/finish/{session_id}`
- `GET /api/v1/contestants/leaderboard/{exam_id}`
- `GET /api/v1/admin/audit-logs?limit=100`
- `GET /api/v1/admin/results/{exam_id}/export`
- `GET /api/v1/admin/monitoring/active`
- `WS  /api/v1/admin/monitoring/ws?token=<admin_jwt>`

## Deployment Steps

1. Backend deploy (Render/Railway): set env vars from `.env.example`, enable HTTPS, attach managed PostgreSQL + Redis.
2. Frontend deploy (Vercel/Netlify): set `VITE_API_BASE_URL` to your HTTPS backend URL.
3. Configure `ALLOWED_ORIGINS` to exact frontend domains.
4. Run migrations/create tables and seed admin.
5. Configure worker process for Celery if using async tasks.
6. Configure daily DB backups (provider snapshot + `pg_dump` cron task).

## Fault Tolerance and Scaling Notes

- FastAPI instances remain stateless and horizontally scalable.
- Redis caches leaderboards and stores session state snapshots.
- Monitoring supports WebSocket with polling fallback on frontend.
- API supports auto-save and anti-cheat telemetry ingestion.
