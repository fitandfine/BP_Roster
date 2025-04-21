import sqlite3
import os
import sys

# Get install directory from argument or fallback
if len(sys.argv) > 1:
    BASE_DIR = sys.argv[1]
else:
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))

DB = os.path.join(BASE_DIR, "roster.db")
ROSTERSDIR = os.path.join(BASE_DIR, "Rosters")
os.makedirs(ROSTERSDIR, exist_ok=True)



def create_connection(db_file=DB):
    return sqlite3.connect(db_file)

def create_tables(conn):
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS managers (
            manager_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL UNIQUE,
            password   TEXT NOT NULL
        )
    ''')

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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roster (
            roster_id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date TEXT,
            end_date   TEXT,
            pdf_file   TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP       
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roster_duties (
            roster_id  INTEGER,
            duty_date  TEXT,
            employee   TEXT,
            start_time TEXT,
            end_time   TEXT,
            note       TEXT,
            FOREIGN KEY(roster_id) REFERENCES roster(roster_id) ON DELETE CASCADE
        )
    ''')

    conn.commit()

def seed_default_manager(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM managers")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute("INSERT INTO managers (username, password) VALUES (?, ?)", ('admin', 'admin'))
        print("[OK] Default manager inserted: username=admin, password=admin")
        conn.commit()

def ensure_rosters_folder():
    os.makedirs(ROSTERSDIR, exist_ok=True)

def initialize_database():
    conn = create_connection()
    create_tables(conn)
    seed_default_manager(conn)
    conn.close()
    ensure_rosters_folder()

if __name__ == '__main__':
    initialize_database()

    # Show popup only when running as a bundled .exe
    if getattr(sys, 'frozen', False):
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Setup Complete", "Roster database and folders initialized.\n\nLogin: admin / admin")
