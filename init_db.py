import sqlite3
import os

DB_PATH = 'honeypot.db'

# Delete old DB if exists (optional)
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("[*] Old database deleted.")

# Create new DB
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute('''
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    src_ip TEXT,
    src_port INTEGER,
    dest_ip TEXT,
    dest_port INTEGER,
    location TEXT,
    country TEXT,
    attack_type TEXT,
    brute_force INTEGER
)
''')

conn.commit()
conn.close()
print("[+] New database initialized with correct schema.")
