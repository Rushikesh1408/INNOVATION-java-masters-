import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

def create_database():
    # Credentials from docker-compose.yml and local environment
    user = 'postgres'
    password = 'Rushikesh1408'
    host = 'localhost'
    port = '5432'
    dbname = 'exam_db'

    try:
        # Connect to default postgres db
        con = psycopg2.connect(dbname='postgres', user=user, host=host, password=password, port=port)
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        
        # Check if db exists
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{dbname}'")
        exists = cur.fetchone()
        
        if not exists:
            cur.execute(f"CREATE DATABASE {dbname}")
            print(f"Database {dbname} created.")
        else:
            print(f"Database {dbname} already exists.")
            
        cur.close()
        con.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    create_database()
