import sqlite3

DB_PATH = '../core_data.db' # TO DO: MOVE THESE INTO A CONFIGS FILE
DB_SCHEMA = './core_data.sql' 

def init_db():
    db = sqlite3.connect(DB_PATH)
    with open(DB_SCHEMA, mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

if __name__=="__main__":
    init_db()
    