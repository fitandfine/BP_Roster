"""
This module handles the database connection, schema creation, and migrations.
We use SQLite as our database.
"""

import sqlite3

def create_connection(db_file='roster.db'):
    """Create and return a SQLite connection."""
    conn = sqlite3.connect(db_file)
    return conn

def create_tables(conn):
    """Create necessary tables if they do not exist."""
    cursor = conn.cursor()
    # Create managers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS managers (
            manager_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    # Create staff table with basic fields.
    # Note: The columns max_hours and days_unavailable may be added later via migration.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone_number TEXT,
            available_dates TEXT,  -- Format: "from,to|unavailable_dates"
            available_hours TEXT   -- Format: "from,to|unavailable_hours"
        )
    ''')
    # Create roster table to store finalized roster PDF details.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roster (
            roster_id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date TEXT,
            end_date TEXT,
            pdf_file TEXT  -- Path to the generated PDF file
        )
    ''')
    conn.commit()

def migrate_staff_table(conn):
    """
    Perform a simple migration on the 'staff' table.
    If the columns max_hours and days_unavailable do not exist, add them.
    """
    cursor = conn.cursor()
    # Get current columns in staff table.
    cursor.execute("PRAGMA table_info(staff)")
    columns = [row[1] for row in cursor.fetchall()]
    # Add max_hours column if it doesn't exist.
    if "max_hours" not in columns:
        cursor.execute("ALTER TABLE staff ADD COLUMN max_hours TEXT")
    # Add days_unavailable column if it doesn't exist.
    if "days_unavailable" not in columns:
        cursor.execute("ALTER TABLE staff ADD COLUMN days_unavailable TEXT")
    conn.commit()

def initialize_database():
    """Initialize the database, create tables, and perform migrations if necessary."""
    conn = create_connection()
    create_tables(conn)
    migrate_staff_table(conn)
    conn.close()

if __name__ == '__main__':
    # Initialize database when this module is run directly.
    initialize_database()
    print("Database and tables created/migrated successfully.")
