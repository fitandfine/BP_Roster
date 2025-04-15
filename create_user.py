import sqlite3
conn = sqlite3.connect('roster.db')
cursor = conn.cursor()
# Insert a default manager account. You can change the username and password as needed.
cursor.execute("INSERT INTO managers (username, password) VALUES (?, ?)", ("admin", "admin123"))
conn.commit()
conn.close()
