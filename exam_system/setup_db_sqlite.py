import sqlite3
import os
import sys

# Add parent dir to path to allow importing flask_bcrypt via the venv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_bcrypt import generate_password_hash

def setup_database():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exam_db.db')
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema_sqlite.sql')

    if not os.path.exists(schema_path):
        print(f"Error: schema file not found at {schema_path}")
        return False

    # Remove old DB to start fresh
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed old database: {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
        print("Schema applied.")

        # Seed Admin
        admin_user = 'admin'
        admin_pass = 'admin123'
        hashed_pass = generate_password_hash(admin_pass).decode('utf-8')
        conn.execute(
            "INSERT OR IGNORE INTO admins (username, password_hash) VALUES (?, ?)",
            (admin_user, hashed_pass)
        )

        # Seed Sample Test
        conn.execute(
            "INSERT OR IGNORE INTO tests (id, title, description, time_limit_minutes, is_active) VALUES (?, ?, ?, ?, ?)",
            (1, 'Python Fundamentals', 'A basic test on Python programming.', 30, 1)
        )

        # Seed Questions (using option_1..4)
        questions = [
            (1, 'What is the correct way to create a list in Python?', '[1, 2, 3]', '(1, 2, 3)', '{1, 2, 3}', '<1, 2, 3>', 1),
            (1, 'Which keyword is used to define a function?', 'func', 'def', 'function', 'lambda', 2),
            (1, 'What is the result of 2 ** 3?', '6', '8', '9', '5', 2),
            (1, 'How do you start a comment in Python?', '//', '/*', '#', '--', 3),
            (1, 'Which data type is immutable?', 'list', 'dict', 'set', 'tuple', 4),
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO questions (test_id, question_text, option_1, option_2, option_3, option_4, correct_option) VALUES (?,?,?,?,?,?,?)",
            questions
        )

        conn.commit()
        print("\n✅ Database setup complete!")
        print(f"   Path:           {db_path}")
        print(f"   Admin Username: {admin_user}")
        print(f"   Admin Password: {admin_pass}")
        print(f"   Sample test:    Python Fundamentals ({len(questions)} questions)")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    setup_database()
