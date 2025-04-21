import os
import subprocess
import time
import sqlite3
import sys

from utils import resource_path

INSTALL_DIR = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
DB_PATH = os.path.join(INSTALL_DIR, "roster.db")
INIT_SETUP_PATH = os.path.join(INSTALL_DIR, "init_setup", "init_setup.exe")

def db_valid(path):
    try:
        with sqlite3.connect(path) as con:
            con.execute("SELECT COUNT(*) FROM managers")
        return True
    except:
        return False

# Run init_setup if DB is missing or corrupt
if not os.path.exists(DB_PATH) or not db_valid(DB_PATH):
    try:
        subprocess.run([INIT_SETUP_PATH, INSTALL_DIR], check=True)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize database.\nError: {e}")

    for _ in range(50):
        if db_valid(DB_PATH):
            break
        time.sleep(0.1)

    if not db_valid(DB_PATH):
        raise RuntimeError("Database initialization failed. Exiting.")

import login
