import sqlite3

conn = sqlite3.connect("students.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS favourites(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_email TEXT,
    company TEXT,
    internship TEXT,
    location TEXT,
    stipend TEXT
)
""")

conn.commit()
conn.close()

print("Database Created Successfully")