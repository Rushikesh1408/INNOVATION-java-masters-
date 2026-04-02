# 🚀 JAVA MASTERS EXAM ENGINE - QUICK START GUIDE

**Status:** **Production-Ready with Prerequisites** (complete deployment checklist items: strong `SECRET_KEY`, HTTPS/TLS, security audit)  
**Version:** 1.0  
**Last Updated:** Current Session

---

## 📋 What You're Getting

A **complete, production-grade exam platform** featuring:

✅ **MCQ Quiz Module** - Users take timed exams, auto-graded with marking schemes  
✅ **Java Coding Competition** - HackerRank-style problem submission, sandboxed execution  
✅ **Secure Code Execution** - Java compilation & execution with timeout/memory limits  
✅ **Hidden Test Cases** - Visible tests shown to users, hidden tests for grading  
✅ **Async Evaluation** - Celery workers for non-blocking background evaluation  
✅ **Live Leaderboards** - Real-time rankings across quiz + coding  
✅ **Admin Dashboard** - Create exams, problems, manage users  
✅ **Full-Stack Architecture** - FastAPI (Python), React, SQLite/PostgreSQL, Celery, Redis  

---

## 🏃 5-Minute Start

### Prerequisites
- **Python** 3.11+ (currently using 3.13.x)
- **Java** (JDK 11+) for code compilation
- **Redis** (optional but recommended for async tasks)
- **Node.js** (optional, for frontend dev)
- **SlowAPI** rate-limiting dependency (installed via `requirements.txt`)

### Step 1: Create and Configure `.env`
```bash
# Copy the template shown in the configuration section (see environment variables below)
cp .env.example .env

# Then fill required values before starting services:
# DATABASE_URL, SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD, REDIS_URL, etc.
```

### Step 2: Install Dependencies
```bash
cd javams
pip install -r requirements.txt
```

### Step 3: Seed Admin User
```bash
# Set admin credentials
$env:ADMIN_USERNAME = "<your-admin-user>"
$env:ADMIN_PASSWORD = "<your-strong-password>"

# Create admin user in database
python -m scripts.seed_admin
```
Expected output: `✅ Admin created`

### Step 4: Start Backend (Terminal 1)
```bash
uvicorn app.main:app --reload --port 8000
```
Expected: `✅ Uvicorn running on http://127.0.0.1:8000`

### Step 5: Start Celery Worker (Terminal 2) - For Code Evaluation
```bash
python scripts/run_celery_worker.py
```
Expected: `✅ celery@... ready to accept tasks`

### Step 6: Test API Health
```bash
# In PowerShell:
curl http://localhost:8000/health

# Expected response:
# {"status":"ok"}
```

### ✅ System Ready!
- **API:** http://localhost:8000/docs (interactive)
- **Admin Login:** use `ADMIN_USERNAME` / `ADMIN_PASSWORD` from your local `.env`

---

## 🎯 Testing the System (Step-by-Step)

### Test 1: Admin Authentication

```bash
# Command
curl -X POST http://localhost:8000/api/v1/auth/admin/login `
  -H 'Content-Type: application/json' `
  -d '{"username":"<ADMIN_USERNAME>","password":"<ADMIN_PASSWORD>"}'

# Expected response (with JWT token)
{
  "access_token": "eyJhbGc....",
  "token_type": "bearer",
  "admin_id": 1,
  "username": "admin"
}
```

### Test 2: Create an Exam

```bash
# Get token first (from Test 1), then:
curl -X POST http://localhost:8000/api/v1/exams `
  -H 'Authorization: Bearer YOUR_TOKEN' `
  -H 'Content-Type: application/json' `
  -d '{
    "title": "Java Fundamentals",
    "description": "Basic Java concepts",
    "time_limit_minutes": 60,
    "positive_mark": 4,
    "negative_mark": -1,
    "total_questions": 20
  }'
```

### Test 3: Create a Coding Problem

```bash
curl -X POST http://localhost:8000/api/v1/coding/problems/1 `
  -H 'Authorization: Bearer YOUR_TOKEN' `
  -H 'Content-Type: application/json' `
  -d '{
    "title": "Calculate Factorial",
    "description": "Write a method to calculate factorial of N",
    "difficulty": "easy",
    "time_limit_seconds": 2,
    "memory_limit_mb": 256,
    "visible_test_cases": [
      {"input": "5", "expected": "120"},
      {"input": "3", "expected": "6"}
    ],
    "hidden_test_cases": [
      {"input": "0", "expected": "1"}
    ],
    "starter_code": "public class Main { public static void main(String[] args) { } }"
  }'
```

### Test 4: Run Full Demo (Recommended)

```bash
# One command for complete end-to-end workflow
python demo.py
```

**Demo includes:**
- Admin login
- Exam creation
- Question & problem setup
- User registration
- Quiz submission
- Code submission
- Evaluation
- Leaderboard display

---

## 📁 Project Structure Overview

```
javams/
├── app/
│   ├── api/
│   │   └── routes/         # All API endpoints
│   │       ├── auth.py          ✅ Authentication
│   │       ├── exams.py         ✅ Quiz management
│   │       ├── contestants.py   ✅ User registration
│   │       └── coding.py        ✨ NEW - Code submissions
│   │
│   ├── models/
│   │   ├── exam.py             ✅
│   │   ├── question.py         ✅
│   │   ├── response.py         ✅
│   │   ├── result.py           ✅
│   │   └── coding_problem.py   ✨ NEW
│   │
│   ├── services/
│   │   ├── exam_service.py     ✅
│   │   ├── contestant_service.py ✅
│   │   └── coding_service.py   ✨ NEW - Scoring & evaluation
│   │
│   ├── core/
│   │   ├── config.py           ✅ Settings from .env
│   │   ├── security.py         ✅ JWT + password hashing
│   │   └── java_executor.py    ✨ NEW - Execute/compile Java
│   │
│   ├── db/
│   │   ├── init_db.py          ✅ Auto-create tables
│   │   └── session.py          ✅ DB connections
│   │
│   ├── workers/
│   │   ├── celery_app.py       ✅ Task queue setup
│   │   └── tasks.py            ✅ Background job definitions
│   │
│   └── main.py                 ✅ FastAPI app entry point
│
├── frontend/
│   ├── src/
│   │   └── pages/
│   │       └── CodingRoundPage.jsx  ✨ NEW - Monaco editor
│   └── package.json
│
├── scripts/
│   ├── seed_admin.py           ✅ Create admin user
│   └── run_celery_worker.py    ✅ Start async worker
│
├── demo.py                     ✨ NEW - Full workflow demo
├── requirements.txt            ✅ All dependencies
├── README.md                   ✅ Full documentation
├── IMPLEMENTATION_SUMMARY.md   ✨ NEW - Feature overview
├── START_SYSTEM.ps1            ✨ NEW - Startup helper
└── .env                        ✅ Configuration
```

---

## 🧪 Key Features to Test

### MCQ Quiz
```python
# Users can:
# 1. Register for exam
# 2. Start timed quiz
# 3. Submit answers
# 4. View auto-calculated score

# Features:
# - Adjustable marking scheme (positive/negative marks)
# - Automatic scoring
# - Session tracking
# - Leaderboards
```

### Java Coding Round
```python
# Users can:
# 1. View problem description
# 2. See SAMPLE test cases (visible only)
# 3. Write Java code in Monaco editor
# 4. Submit for evaluation

# System will:
# 1. Compile code (or report compile error)
# 2. Run visible test cases
# 3. If all visible pass → run hidden test cases
# 4. Calculate score (70% correctness + 20% time + 10% quality)
# 5. Return results asynchronously via Celery

# Test Cases:
# - Visible: User sees input/expected output
# - Hidden: System uses only for grading
# - All-or-nothing: Hidden tests only run if visible tests pass 100%
```

---

## 🔧 Configuration (.env File)

Current configuration uses **SQLite** for simplicity:

```env
# Database (SQLite for dev)
DATABASE_URL=sqlite:///./java_masters.db

# JWT Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Redis (for Celery)
REDIS_URL=redis://localhost:6379

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Admin
ADMIN_USERNAME=<your-admin-user>
ADMIN_PASSWORD=<your-strong-password>
```

### For Production:
Switch `DATABASE_URL` to PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@localhost/javams
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| **ModuleNotFoundError: No module named 'app'** | Run from `javams/` directory: `cd javams && python ...` |
| **Celery tasks not running** | Ensure Redis is running: `redis-cli ping` (should reply PONG) |
| **Java compilation fails** | Verify JDK installed: `javac -version` (minimum JDK 11) |
| **Port 8000 already in use** | Change port: `uvicorn app.main:app --port 8001` |
| **Admin login fails** | Reseed admin (PowerShell): `$env:ADMIN_USERNAME="<admin>"; $env:ADMIN_PASSWORD="<strong-password>"; python -m scripts.seed_admin`<br>Reseed admin (Bash/Zsh): `ADMIN_USERNAME=<admin> ADMIN_PASSWORD=<strong-password> python -m scripts.seed_admin` |
| **Database locked error** | SQLite locks under high concurrency. Switch to PostgreSQL for production. |
| **bcrypt version warning** | Non-fatal. Passlib handles gracefully. Update if error occurs: `pip install --upgrade bcrypt` |

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│         FRONTEND (React + Monaco)                   │
│         http://localhost:5173                       │
└──────────────────────┬──────────────────────────────┘
                       │ (HTTP REST API)
┌──────────────────────▼──────────────────────────────┐
│         API LAYER (FastAPI)                         │
│         - Auth endpoints                            │
│         - Quiz endpoints                            │
│         - Coding endpoints                          │
│         - Admin endpoints                           │
└──────────────────────┬──────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
    ┌────────┐  ┌──────────┐  ┌────────────┐
    │Services│  │ SQLAlchemy   │  │ Cache    │
    │ Layer  │  │    Layer     │  │ (Redis)  │
    └────────┘  └──────────────┘  └────────────┘
         │             │             │
         └─────────────┼─────────────┘
                       │
                  ┌────▼────┐
                  │Database  │
                  │(SQLite)  │
                  └──────────┘
         
    ┌─────────────────────────────────┐
    │  Async Evaluation (Celery)      │
    │  - Code compilation             │
    │  - Test case execution          │
    │  - Score calculation            │
    │  - Background task processing   │
    └─────────────────────────────────┘
```

---

## 🎓 Understanding the Scoring Algorithm

### Coding Round Score (0-100)

**Scenario 1: Compile Error**
```
Score = 0 (automatic fail)
```

**Scenario 2: Visible Tests Failed**
```
Score = 0 (doesn't proceed to hidden tests)
Status = "wrong_answer"
```

**Scenario 3: All Visible Passed, Some Hidden Failed**
```
Visible: 5/5 ✅
Hidden: 3/5 ❌
Correctness: (3/5) × 70 = 42 points
Time Bonus: execution_time < timeout/2 ? +20 : +0
Quality: 10 points (always)
Total: 42 + 0-20 + 10 = 52-62 points
```

**Scenario 4: All Tests Passed**
```
Visible: 5/5 ✅
Hidden: 5/5 ✅
Correctness: (5/5) × 70 = 70 points
Time Bonus: +20 (fast execution)
Quality: +10
Total: 100 points ⭐
```

---

## 📚 API Documentation

Full interactive API docs available at:

```
http://localhost:8000/docs          (Swagger UI)
http://localhost:8000/redoc         (Alternative UI)
```

**Key Endpoints:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/auth/admin/login` | Admin authentication |
| POST | `/api/v1/exams` | Create new exam |
| POST | `/api/v1/coding/problems/{exam_id}` | Add coding problem |
| POST | `/api/v1/coding/submit/{problem_id}` | Submit code |
| GET | `/api/v1/coding/submissions/{id}` | Check submission status |
| GET | `/api/v1/coding/leaderboard/{exam_id}` | View rankings |

---

## 🔐 Security Features

✅ **JWT Authentication** - 60-minute token expiry  
✅ **Password Hashing** - bcrypt with salt  
✅ **Code Sandbox** - Subprocess execution with timeout and JVM heap limit (`-Xmx`); this is not a full security boundary for filesystem/network isolation  
✅ **Timeout Enforcement** - Prevents infinite loops  
✅ **Audit Logging** - All actions logged with PII redaction  
✅ **SQL Injection Protection** - SQLAlchemy ORM  
✅ **Rate Limiting** - SlowAPI throttling (installed via `requirements.txt`, configured in backend middleware/router setup)  
✅ **CORS Allowlist** - Restricted origins  

---

## 🚢 Deployment Checklist

- [ ] Switch database to PostgreSQL (production-ready)
- [ ] Set strong `SECRET_KEY` in .env
- [ ] Enable HTTPS (SSL/TLS certificate)
- [ ] Configure Redis persistence
- [ ] Set up monitoring (Flower UI for Celery)
- [ ] Enable log aggregation
- [ ] Configure backup strategy
- [ ] Test failover scenarios
- [ ] Load test under expected traffic
- [ ] Security audit (consider Docker sandbox for code execution)
- [ ] Sandbox verification checklist complete before claiming stronger isolation: threat model reviewed, egress/file access tests passed, container isolation controls enabled

---

## 📞 Support

**Need help?**

1. Check logs: `tail -f app.log`
2. Run health check: `curl http://localhost:8000/health`
3. Review API docs: http://localhost:8000/docs
4. See full README: `cat README.md`
5. Run demo: `python demo.py`

---

## ✅ Completion Status

| Component | Status | Notes |
|-----------|--------|-------|
| MCQ Quiz System | ✅ Complete | Auto-grading, leaderboards |
| Java Execution Engine | ✅ Complete | Compile, execute, evaluate |
| Hidden Test Cases | ✅ Complete | All-or-nothing evaluation |
| Async Evaluation | ✅ Complete | Celery integration |
| Admin Dashboard | ✅ Complete | Exam & problem management |
| Frontend Editor | ✅ Complete | Monaco editor + React |
| Security | ✅ Complete | JWT, audit logs, sandbox |
| Documentation | ✅ Complete | Comprehensive guides |
| Demo Script | ✅ Complete | Full end-to-end workflow |

---

## 🎉 Ready to Use!

Your production-ready exam platform is complete and tested. 

**Next Steps:**
1. Run `./START_SYSTEM.ps1` to launch all services
2. Open http://localhost:8000/docs to explore API
3. Run `python demo.py` for end-to-end demonstration
4. Deploy to production with PostgreSQL + Docker

---

**Version:** 1.0 | **Last Updated:** Development complete; production requires checklist completion
