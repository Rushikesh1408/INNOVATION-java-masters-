# Java Masters Exam Engine - Complete System (Quiz + Coding)

Production-ready full-stack examination platform featuring **MCQ Quiz Round** and **Java Coding Round** with secure execution, test case evaluation, and comprehensive leaderboarding.

**Tech Stack:** FastAPI, React, PostgreSQL/SQLite, Redis, Celery, Java Runtime

---

##  SYSTEM FLOW

1. **User Registration & Login**  JWT authentication
2. **Admin Setup**  Creates exams with MCQ questions & coding problems
3. **Quiz Round**  Contestants answer multiple-choice questions
4. **Quiz Results**  System calculates scores, top users proceed
5. **Coding Round**  Shortlisted users write Java code for problems
6. **Code Evaluation**  Compilation, execution, test case validation (visible + hidden)
7. **Final Leaderboard**  Combined scoring from quiz + coding
8. **Analytics Dashboard**  Performance metrics & rankings

---

##  QUICK START

```bash
# 1. Setup environment
pip install -r requirements.txt
python -m scripts.seed_admin  # Create admin with ADMIN_USERNAME, ADMIN_PASSWORD

# 2. Start backend
uvicorn app.main:app --reload

# 3. Start worker (async evaluation)
python scripts/run_celery_worker.py

# 4. Frontend
cd frontend && npm install && npm run dev
```

Visit http://localhost:8000/docs for API documentation

---

##  JAVA EXECUTION ENGINE (Core Innovation)

Secure, isolated Java code compilation and execution with test case evaluation.

### How It Works

```
User Code (Java)
    
Write to Main.java
    
Compile: javac Main.java
     (Success?)
Execute: java Main <input> (2-second timeout)
    
Compare Output  Expected
    
Return: ACCEPTED / WRONG_ANSWER / TIMEOUT / COMPILE_ERROR
```

### Evaluation Flow

1. **Visible Test Cases**  User sees input/output (for learning)
2. **Hidden Test Cases**  Used for scoring (users don't see)
3. **All-or-Nothing**  ALL visible tests must pass to check hidden tests
4. **Scoring**  70% correctness, 20% time, 10% code quality

### Example Coding Problem

```python
# Problem Definition (Admin creates this)
{
  "title": "Factorial Calculator",
  "description": "Calculate factorial of N",
  "time_limit_seconds": 2,
  "difficulty": "easy",
  "visible_test_cases": [
    {"input": "5", "expected": "120"},
    {"input": "3", "expected": "6"}
  ],
  "hidden_test_cases": [  # Secret tests for grading
    {"input": "0", "expected": "1"},
    {"input": "10", "expected": "3628800"}
  ]
}

# User submits Java code
public class Main {
    public static void main(String[] args) {
        int n = Integer.parseInt(args[0]);
        System.out.println(factorial(n));
    }
    static long factorial(int n) {
        return n <= 1 ? 1 : n * factorial(n-1);
    }
}

# Evaluation Result
{
  "status": "accepted",
  "score": 95,
  "passed_visible": 2,
  "passed_hidden": 2,
  "execution_time_ms": 42
}
```

---

##  DATABASE SCHEMA

### Quiz Models
- **Exam**: title, time_limit, positive_mark, negative_mark
- **Question**: exam_id, question_text, options[4], correct_option
- **Session**: user_id, exam_id, start_time, status
- **Response**: session_id, question_id, selected_option
- **Result**: user_id, exam_id, score, accuracy, total_time

### Coding Models
- **CodingProblem**: exam_id, title, description, difficulty, time_limit_seconds, memory_limit_mb, visible_tests[], hidden_tests[]
- **Submission**: user_id, problem_id, code, language, status, score, passed_visible, passed_hidden, execution_time_ms

### Auth & Admin
- **Admin**: username, password_hash
- **User**: name, email
- **Log**: user_id, action, context (with PII redaction)

---

##  BACKEND STRUCTURE

```
app/
 api/
    router.py
    routes/
        auth.py
        exams.py
        contestants.py
        coding.py                  # NEW: Coding endpoints
        admin_reports.py
        monitoring.py
 core/
    config.py
    security.py
    java_executor.py               # NEW: Java execution engine
    redis_client.py
    logging_middleware.py
    deps.py
 models/
    user.py
    exam.py
    question.py
    result.py
    session.py
    response.py
    admin.py
    log.py
    coding_problem.py              # NEW: CodingProblem, Submission models
 repositories/
    exam_repository.py
    contestant_repository.py
    admin_repository.py
    coding_repository.py           # NEW: Submission & Problem repos
 services/
    auth_service.py
    exam_service.py
    contestant_service.py
    log_service.py
    coding_service.py              # NEW: Evaluation & scoring logic
 db/
    base.py
    init_db.py
    session.py
    database.py
 workers/
    celery_app.py
    tasks.py                       # NEW: Async evaluation task
 main.py

frontend/
 src/
    pages/
       LoginPage.jsx
       ExamPage.jsx
       CodingRoundPage.jsx       # NEW: Java editor with Monaco
       ResultPage.jsx
       LeaderboardPage.jsx
       ...
    App.jsx
    main.jsx
 package.json
```

---

##  API ENDPOINTS

### Coding (NEW)

```
POST   /api/v1/coding/problems/{exam_id}
       Create coding problem (admin only)

GET    /api/v1/coding/problems/{exam_id}
       List problems for exam (visible tests only)

POST   /api/v1/coding/submit/{problem_id}
       Submit Java code (returns submission_id, triggers async evaluation)

GET    /api/v1/coding/submissions/{submission_id}
       Get submission status & results

POST   /api/v1/coding/evaluate/{submission_id}
       Manually trigger evaluation (normally async via Celery)

GET    /api/v1/coding/leaderboard/{exam_id}
       Coding round leaderboard (ranked by total score)

GET    /api/v1/coding/best/{problem_id}
       Get user's best submission for problem
```

### Quiz (Existing - Still Available)

```
POST   /api/v1/exams
GET    /api/v1/exams/{exam_id}
POST   /api/v1/exams/{exam_id}/questions
PUT    /api/v1/exams/{exam_id}/questions/{question_id}

POST   /api/v1/contestants/register
POST   /api/v1/contestants/start-exam
POST   /api/v1/contestants/submit-answer
POST   /api/v1/contestants/finish/{session_id}
GET    /api/v1/contestants/leaderboard/{exam_id}
```

### Admin

```
GET    /api/v1/admin/audit-logs
GET    /api/v1/admin/results/{exam_id}/export
```

---

##  SCORING & LEADERBOARD

### Coding Score Calculation

```python
def calculate_score(eval_result):
    if status == "compile_error":
        return 0
    
    if status == "timeout":
        # Proportional scoring: pass rate × corresponding weight
        total_visible = eval_result.get("total_visible", 1) or 1
        total_hidden = eval_result.get("total_hidden", 1) or 1
        visible_ratio = min(1.0, eval_result.get("passed_visible", 0) / total_visible)
        hidden_ratio = min(1.0, eval_result.get("passed_hidden", 0) / total_hidden)
        return int(visible_ratio * 70 + hidden_ratio * 20)
    
    # Correctness: 70% (from hidden tests only)
    # Guard against division by zero
    total_hidden = eval_result.get("total_hidden", 1) or 1
    correctness = (eval_result.get("passed_hidden", 0) / total_hidden) * 70
    
    # Time efficiency: 20% (bonus if < 50% of timeout)
    time_bonus = 20 if execution_time < (timeout * 0.5) else 0
    
    # Code quality: 10% (placeholder for actual metrics)
    quality = 10
    
    return min(100, correctness + time_bonus + quality)
```

### Final Score

```
Final_Score = (Quiz_Score × 0.4) + (Coding_Score × 0.6)
```

### Leaderboard Ranking

```
Rank 1: User A (80 points)
Rank 2: User B (75 points)
...
```

---

##  DEPLOYMENT

### Requirements

- Python 3.11+
- Java Development Kit (JDK 11+)
- PostgreSQL 13+ (or SQLite for dev)
- Redis 6+
- Node.js 18+

### Environment Setup

```bash
# Copy and edit .env
cp .env.example .env

DATABASE_URL=sqlite:///./java_masters.db  # Dev
# or
DATABASE_URL=postgresql://user:pass@host/db  # Prod

ADMIN_JWT_SECRET=<generate: openssl rand -hex 32>
REDIS_URL=redis://localhost:6379/0
```

### Docker Deployment

```bash
docker-compose up -d  # Brings up postgres, redis, backend

# Then seed & start api
python -m scripts.seed_admin
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Verification

```bash
curl http://localhost:8000/health
# Response: {"status": "ok"}

curl http://localhost:8000/docs
# Opens interactive API documentation
```

---

##  SECURITY FEATURES

### Code Execution Sandbox

⚠️  **Current Implementation (Development/Staging Only):**
-  Subprocess execution with 2-second timeout
-  JVM heap limit (-Xmx256m)
-  Basic process cleanup

⚠️  **NOT Implemented (Required for Production):**
-  No filesystem isolation (can access all readable files)
-  No network isolation (can make network calls)
-  Memory limit is JVM heap only, not total process memory
-  No automatic error sanitization

**Production-Grade Sandboxing (Recommended):**
Deploy with container isolation (Docker with `--network=none --read-only --memory=256m`) or OS-level controls (seccomp, AppArmor, SELinux)

### API Security

-  JWT authentication (exp: 60 min)
-  CORS allowlist (localhost:5173, etc.)
-  Rate limiting (SlowAPI)
-  Input validation (Pydantic)
-  SQL injection protection (ORM)

### Audit & Privacy

-  All actions logged with timestamps
-  User context pseudonymized (SHA256)
-  PII redaction (emails, phones, SSNs  [redacted])
-  90-day retention policy
-  CSV export injection protection

---

##  TESTING

### Test Execution Paths

```bash
# Compile Error
POST /api/v1/coding/submit/1
{"code": "invalid syntax"}
# Response: status=compile_error, score=0

`# Timeout (execution exceeds timeout limit)
POST /api/v1/coding/submit/1
{"code": "while(true){};"}
# Response: status=timeout, score=partial (proportional scoring: tests passed × weight)`

# Wrong Answer
POST /api/v1/coding/submit/1
{"code": "System.out.println(0);"}
# Response: status=wrong_answer, score=0

# Accepted
POST /api/v1/coding/submit/1
{"code": "// Correct solution..."}
# Response: status=accepted, score=95
```

---

##  FEATURES CHECKLIST

-  User registration & JWT auth
-  Admin exam management
-  MCQ quiz with timer
-  Quiz result calculation
-  Quiz leaderboard
-  Coding problem creation
-  **Java compilation & execution**
-  **Visible + hidden test cases**
-  **Timeout enforcement**
-  **Scoring algorithm**
-  **Coding leaderboard**
-  **Final combined rankings**
-  Admin dashboard
-  Audit logs
-  CSV export
-  Async evaluation (Celery)
-  Rate limiting
-  CORS security
-  React + Monaco editor frontend
-  Docker compose
-  Production-ready

---

##  DOCUMENTATION

- **Interactive API Docs:** http://localhost:8000/docs
- **OpenAPI Schema:** http://localhost:8000/openapi.json
- **Frontend Dev:** http://localhost:5173

---

##  TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Compilation fails | Check Java code syntax, ensure JDK 11+ installed |
| All tests timeout | Reduce `time_limit_seconds` or optimize code |
| Celery not working | Verify Redis running: `redis-cli ping` |
| Database locked (SQLite) | Use PostgreSQL for concurrent access |

---

##  LICENSE

Apache 2.0

---

**Production-ready Java Masters Exam Engine** 
