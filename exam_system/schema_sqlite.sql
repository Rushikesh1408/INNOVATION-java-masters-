-- SQLite Schema for Online Examination System

-- Admins Table
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

-- Contestants Table
CREATE TABLE IF NOT EXISTS contestants (
    email VARCHAR(100) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tests Table
CREATE TABLE IF NOT EXISTS tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    time_limit_minutes INTEGER NOT NULL DEFAULT 30,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Questions Table (uses option_1..4 to match seeding)
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    option_1 TEXT NOT NULL,
    option_2 TEXT NOT NULL,
    option_3 TEXT NOT NULL,
    option_4 TEXT NOT NULL,
    correct_option INTEGER NOT NULL CHECK (correct_option BETWEEN 1 AND 4),
    FOREIGN KEY (test_id) REFERENCES tests (id) ON DELETE CASCADE
);

-- Attempts Table
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contestant_email VARCHAR(100) NOT NULL,
    test_id INTEGER NOT NULL,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    score INTEGER DEFAULT 0,
    total_time_taken INTEGER DEFAULT 0,
    submitted INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'IN_PROGRESS',
    anti_cheat_flags TEXT DEFAULT '[]',
    UNIQUE (contestant_email, test_id),
    FOREIGN KEY (contestant_email) REFERENCES contestants (email),
    FOREIGN KEY (test_id) REFERENCES tests (id)
);

-- Responses Table
CREATE TABLE IF NOT EXISTS responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    selected_option INTEGER NOT NULL,
    time_taken_seconds INTEGER,
    is_correct INTEGER,
    UNIQUE (attempt_id, question_id),
    FOREIGN KEY (attempt_id) REFERENCES attempts (id),
    FOREIGN KEY (question_id) REFERENCES questions (id)
);
