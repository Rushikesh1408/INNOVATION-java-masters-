# Java Masters Exam Engine

Scalable full-stack online examination platform with:

- FastAPI backend (modular layered architecture)
- React frontend (role-based UI)
- PostgreSQL data layer (normalized schema)
- Anti-cheating telemetry and server-side flagging

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
	api/
		router.py
		routes/
			auth.py
			exams.py
			contestants.py
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
		question.py
		session.py
		response.py
		result.py
	repositories/
		admin_repository.py
		exam_repository.py
		contestant_repository.py
	schemas/
		auth.py
		exam.py
		question.py
		contestant.py
		leaderboard.py
	services/
		auth_service.py
		exam_service.py
		contestant_service.py
	main.py
scripts/
	seed_admin.py
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

### Contestant

- Register with unique email.
- Start exam session with UUID tracking.
- Submit question responses with time-per-question.
- Finish exam and generate results.

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

### Security

- Admin JWT auth.
- Password hashing via bcrypt.
- CORS allowlist through environment config.
- Server-side validation using Pydantic.
- Request audit middleware.
- SlowAPI limiter integrated at app level.

## Database schema

Tables implemented:

- `admins(id, username, password_hash)`
- `users(id, name, email unique)`
- `exams(id, title, time_limit, rules, created_by)`
- `questions(id, exam_id, question_text, options, correct_option)`
- `sessions(id UUID, user_id, exam_id, start_time, end_time, ip_address, device_info, status, warning_count, flagged)`
- `responses(id, session_id, question_id, selected_option, time_taken)`
- `results(id, user_id, exam_id, score, accuracy, total_time, flagged)`

Indexes included for session lookup, response uniqueness per question, and leaderboard sort paths.

## Environment setup

### Backend

1. Create `.env` from `.env.example`.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Seed admin user:

```bash
python scripts/seed_admin.py
```

4. Run API:

```bash
uvicorn app.main:app --reload
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

## Notes

- This implementation is hackathon-ready and modular.
- For production, add refresh tokens, DB migrations with Alembic, Redis-backed distributed rate limiting, and WebSocket live monitoring channels.
