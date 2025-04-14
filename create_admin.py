import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
INSERT OR IGNORE INTO users (name, personal_number, email, password_hash)
VALUES (?, ?, ?, ?)
""", (
    "Админ", "0000", "admin", generate_password_hash("admin")
))

conn.commit()
conn.close()
print("Админ потребителят е създаден.")
