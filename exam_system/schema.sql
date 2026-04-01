-- Database Schema for Online Examination System

-- Admin Table
CREATE TABLE IF NOT EXISTS admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

-- Contestant Table
CREATE TABLE IF NOT EXISTS contestants (
    email VARCHAR(255) PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tests Table
CREATE TABLE IF NOT EXISTS tests (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    time_limit INTEGER NOT NULL, -- minutes
    rules_text TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Questions Table
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    test_id INTEGER REFERENCES tests(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_option CHAR(1) CHECK (correct_option IN ('A', 'B', 'C', 'D'))
);

-- Attempts Table
CREATE TABLE IF NOT EXISTS attempts (
    id SERIAL PRIMARY KEY,
    test_id INTEGER REFERENCES tests(id) ON DELETE CASCADE,
    contestant_email VARCHAR(255) REFERENCES contestants(email) ON DELETE CASCADE,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    total_time_taken INTEGER, -- seconds
    score INTEGER DEFAULT 0,
    submitted BOOLEAN DEFAULT FALSE,
    UNIQUE(test_id, contestant_email)
);

-- Responses Table
CREATE TABLE IF NOT EXISTS responses (
    id SERIAL PRIMARY KEY,
    attempt_id INTEGER REFERENCES attempts(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    selected_option CHAR(1) CHECK (selected_option IN ('A', 'B', 'C', 'D')),
    time_taken INTEGER -- seconds per question
);
