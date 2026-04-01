import psycopg2
import sys

passwords = ['postgres', 'admin', 'password', 'root', 'Rushikesh1408', 'Rushikesh@1408', '']
user = 'postgres'
host = 'localhost'
port = '5432'

for pwd in passwords:
    try:
        conn = psycopg2.connect(dbname='postgres', user=user, host=host, password=pwd, port=port)
        print(f"SUCCESS: {pwd}")
        conn.close()
        sys.exit(0)
    except Exception as e:
        print(f"FAILED: {pwd} - {e}")

sys.exit(1)
