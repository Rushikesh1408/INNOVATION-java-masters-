import os
from contextlib import contextmanager
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import RealDictCursor


def _get_db_url():
    """Get the PostgreSQL DATABASE_URL env var."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise RuntimeError('DATABASE_URL is required and must point to PostgreSQL.')
    return db_url


def _connect(db_url: str):
    parsed = urlparse(db_url)
    if parsed.scheme.startswith('postgres'):
        return psycopg2.connect(db_url)
    raise RuntimeError('Unsupported DATABASE_URL. Only PostgreSQL URLs are supported.')

class Database:
    @classmethod
    @contextmanager
    def get_connection(cls):
        db_url = _get_db_url()
        conn = _connect(db_url)
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
        return query

    @classmethod
    def execute_query(cls, query, params=None, fetch=None):
        query = cls._fix_query(query)
        with cls.get_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, params or ())
            if fetch == 'one':
                row = cur.fetchone()
                if row is None:
                    return None
                return tuple(row.values())
            elif fetch == 'all':
                rows = cur.fetchall()
                return [tuple(r.values()) for r in rows]
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
