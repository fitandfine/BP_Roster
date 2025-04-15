# login.py
"""
This module implements the manager login screen using Tkinter.
On successful login, it launches the manager dashboard.
"""

import tkinter as tk
from tkinter import messagebox
import sqlite3
import dashboard  # This module will open the main dashboard after login

def verify_login(username, password):
    """Verify manager credentials against the database."""
    conn = sqlite3.connect('roster.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM managers WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()
    conn.close()
    return result

def login():
    """Process login from the GUI."""
    username = username_entry.get()
    password = password_entry.get()
    if verify_login(username, password):
        # On successful login, destroy the login window and open the dashboard.
        root.destroy()
        dashboard.launch_dashboard(username)  # Passing the manager username if needed
    else:
        messagebox.showerror("Login Failed", "Incorrect username or password. Please try again.")

# Create the login window
root = tk.Tk()
root.title("Manager Login")

# Username label and entry with placeholder
tk.Label(root, text="Username:").grid(row=0, column=0, padx=10, pady=10)
username_entry = tk.Entry(root)
username_entry.grid(row=0, column=1, padx=10, pady=10)
username_entry.insert(0,"")

# Password label and entry with placeholder (using '*' for password entry)
tk.Label(root, text="Password:").grid(row=1, column=0, padx=10, pady=10)
password_entry = tk.Entry(root, show="*")
password_entry.grid(row=1, column=1, padx=10, pady=10)
password_entry.insert(0,"")

# Login button that triggers the login function
login_button = tk.Button(root, text="Login", command=login)
login_button.grid(row=2, column=0, columnspan=2, pady=20)

root.mainloop()
