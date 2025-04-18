import os
import subprocess
import sys

# This handles both development and PyInstaller runtime paths
if hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS  # temp path where PyInstaller unpacks files
    INIT_SETUP_PATH = os.path.join(BASE_DIR, "init_setup.exe")
    DB_PATH = os.path.join(os.path.dirname(sys.executable), "roster.db")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    INIT_SETUP_PATH = os.path.join(BASE_DIR, "init_setup.exe")
    DB_PATH = os.path.join(BASE_DIR, "roster.db")

# Run init_setup if DB doesn't exist (or is corrupted)
def ensure_database():
    if not os.path.exists(DB_PATH):
        subprocess.run([INIT_SETUP_PATH], check=True)
    else:
        import sqlite3
        try:
            with sqlite3.connect(DB_PATH) as con:
                con.execute("SELECT COUNT(*) FROM managers")
        except:
            subprocess.run([INIT_SETUP_PATH], check=True)

ensure_database()

import login  # launch login GUI
