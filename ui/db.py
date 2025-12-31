import os
import psycopg2

POSTGRES_DSN = {
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "dbname": os.getenv("POSTGRES_DB", "toxicity"),
    "user": os.getenv("POSTGRES_USER", "user"),
    "password": os.getenv("POSTGRES_PASSWORD", "password"),
}

def get_connection():
    conn = psycopg2.connect(**POSTGRES_DSN)
    conn.autocommit = True
    return conn