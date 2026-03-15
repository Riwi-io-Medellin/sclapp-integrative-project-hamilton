"""
Database connection layer.

Provides PostgreSQL connection and query execution. Reads DB_* from environment.
All queries commit so INSERT/UPDATE persist; errors are re-raised, not silenced.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """
    Establishes a connection to the PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', '127.0.0.1'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'sclapp'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '0421')
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_db_info():
    """
    Returns host, port and database from env (for debugging: confirm which DB the backend uses).
    """
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": os.getenv("DB_NAME", "sclapp"),
    }


def execute_query(query, params=None, fetch=True):
    """
    Executes a SQL query. Always commits after execute so INSERT/UPDATE persist.
    If fetch=True, returns cur.fetchall(); if fetch=False, returns True.
    On error: prints the error, rolls back and re-raises the exception (does not silence).
    """
    conn = get_db_connection()
    if conn is None:
        raise RuntimeError("Could not connect to the database (get_db_connection returned None).")

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            conn.commit()
            if fetch:
                result = cur.fetchall()
            else:
                result = True
            return result
    except Exception as e:
        print(f"Error ejecutando consulta: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
