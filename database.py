import sqlite3
import os
from config import DB_FILE

TABLES = [
    """
    CREATE TABLE IF NOT EXISTS cars(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporting_mark TEXT,
        number TEXT,
        car_type TEXT,
        length INTEGER,
        owner TEXT,
        status TEXT,
        location TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS industries(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        town TEXT,
        track TEXT,
        spots INTEGER,
        notes TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS locomotives(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        railroad TEXT,
        number TEXT,
        model TEXT,
        decoder TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS trains(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        description TEXT
    )
    """
]

def initialize_database():
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    for table in TABLES:
        cur.execute(table)

    conn.commit()
    conn.close()


def get_count(table_name):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cur.fetchone()[0]

    conn.close()
    return count