import sqlite3

DB_PATH = '../core_data.db' # TO DO: MOVE THIS INTO A CONFIGS FILE

def init_db():
    db = sqlite3.connect(DB_PATH)
    with open('../schema/core_data.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    