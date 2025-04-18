import sqlite3
import os

DB_FILE = 'roster.db'
ROSTERS_DIR = 'Rosters'


def create_connection(db_file=DB_FILE):
    """Create and return a SQLite connection."""
    return sqlite3.connect(db_file)


def create_tables(conn):
    """Create necessary tables if they do not exist."""
    cursor = conn.cursor()

    # Table for manager credentials
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS managers (
            manager_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL UNIQUE,
            password   TEXT NOT NULL
        )
    ''')

    # Table for employee/staff details
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            staff_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            email           TEXT NOT NULL,
            phone_number    TEXT,
            max_hours       TEXT,
            days_unavailable TEXT
        )
    ''')

    # Table for roster summary
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roster (
            roster_id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date TEXT,
            end_date   TEXT,
            pdf_file   TEXT,  -- Path to the generated PDF file (inside Rosters/)
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP       
        )
    ''')

    # Table for duty details (including special note)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roster_duties (
            roster_id  INTEGER,
            duty_date  TEXT,   -- YYYY-MM-DD
            employee   TEXT,
            start_time TEXT,   -- HH:MM
            end_time   TEXT,   -- HH:MM
            note       TEXT,   -- Optional daily note for the duty day
            FOREIGN KEY(roster_id) REFERENCES roster(roster_id) ON DELETE CASCADE
        )
    ''')

    conn.commit()


def seed_default_manager(conn):
    """Insert default admin manager if no managers exist."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM managers")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute(
            "INSERT INTO managers (username, password) VALUES (?, ?)",
            ('admin', 'admin')
        )
        print("[✔] Default manager inserted: username=admin, password=admin")
        conn.commit()


def ensure_rosters_folder():
    """Ensure the folder for storing roster PDFs exists."""
    os.makedirs(ROSTERS_DIR, exist_ok=True)


def initialize_database():
    """Run all setup tasks: tables, manager seed, PDF folder."""
    conn = create_connection()
    create_tables(conn)
    seed_default_manager(conn)
    conn.close()
    ensure_rosters_folder()


if __name__ == '__main__':
    initialize_database()
    print("[✔] Database initialized and ready.")
