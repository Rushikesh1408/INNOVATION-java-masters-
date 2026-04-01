import sqlite3
import os
from contextlib import contextmanager

def _get_db_path():
    """Get the SQLite database path from DATABASE_URL env var."""
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///exam_db.db')
    if db_url.startswith('sqlite:///'):
        path = db_url[len('sqlite:///'):]
        # If relative, resolve relative to exam_system root (where wsgi.py lives)
        if not os.path.isabs(path):
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(base, path)
        return path
    return 'exam_db.db'

class Database:
    @classmethod
    @contextmanager
    def get_connection(cls):
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @classmethod
    def _fix_query(cls, query):
        """Convert %s placeholders to ? for SQLite."""
        return query.replace('%s', '?')

    @classmethod
    def execute_query(cls, query, params=None, fetch=None):
        query = cls._fix_query(query)
        with cls.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params or ())
            if fetch == 'one':
                row = cur.fetchone()
                return tuple(row) if row else None
            elif fetch == 'all':
                rows = cur.fetchall()
                return [tuple(r) for r in rows]
            return None

    @classmethod
    def execute_insert(cls, query, params=None):
        """Execute an INSERT and return the last inserted row id."""
        query = cls._fix_query(query)
        with cls.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params or ())
            return cur.lastrowid

    @classmethod
    def execute_many(cls, query, params_list):
        query = cls._fix_query(query)
        with cls.get_connection() as conn:
            cur = conn.cursor()
            cur.executemany(query, params_list)
