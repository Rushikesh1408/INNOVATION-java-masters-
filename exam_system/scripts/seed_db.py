import psycopg2
import os
from flask_bcrypt import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

def seed():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not set in .env")
        return

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    try:
        # Create Admin
        admin_user = 'admin'
        admin_pass = 'admin123'
        hashed_pass = generate_password_hash(admin_pass).decode('utf-8')
        
        cur.execute("INSERT INTO admins (username, password_hash) VALUES (%s, %s) ON CONFLICT (username) DO NOTHING", 
                    (admin_user, hashed_pass))
        
        # Create Sample Test
        cur.execute("""INSERT INTO tests (title, time_limit, rules_text) 
                    VALUES (%s, %s, %s) RETURNING id""", 
                    ('General Knowledge Quiz', 10, '1. Fullscreen is mandatory.\n2. No switching tabs.\n3. Each question carries 1 mark.'))
        test_id = cur.fetchone()[0]

        # Add Questions
        questions = [
            ('What is the capital of France?', 'Lyon', 'Marseille', 'Paris', 'Nice', 'C'),
            ('Which planet is known as the Red Planet?', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'B'),
            ('What is 5 + 7?', '10', '11', '12', '13', 'C')
        ]
        
        for q in questions:
            cur.execute("""INSERT INTO questions (test_id, question_text, option_a, option_b, option_c, option_d, correct_option) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)""", (test_id, *q))

        conn.commit()
        print("Database seeded successfully!")
        print(f"Admin Username: {admin_user}")
        print(f"Admin Password: {admin_pass}")

    except Exception as e:
        print(f"Error seeding: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed()
