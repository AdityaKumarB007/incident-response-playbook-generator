import sqlite3
import os

# Get the directory of the current file and construct the path to db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '../data/siem.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            incident_id TEXT PRIMARY KEY,
            attack_type TEXT,
            timestamp TEXT,
            source_ip TEXT,
            endpoint TEXT,
            severity TEXT,
            evidence TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_incident(incident):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO incidents 
        (incident_id, attack_type, timestamp, source_ip, endpoint, severity, evidence)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        incident['incident_id'],
        incident['attack_type'],
        incident['timestamp'],
        incident['source_ip'],
        incident['endpoint'],
        incident['severity'],
        incident['evidence']
    ))
    conn.commit()
    conn.close()

def get_all_incidents():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM incidents ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(ix) for ix in rows]

if __name__ == '__main__':
    init_db()
    print(f"Database initialized at {DB_PATH}")

