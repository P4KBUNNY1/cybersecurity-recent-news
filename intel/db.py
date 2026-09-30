# db_init.py - shared database setup
import sqlite3
from .config import DB_PATH

def get_db():
    db = sqlite3.connect(DB_PATH, timeout=30)
    db.execute("""CREATE TABLE IF NOT EXISTS posts(
        id TEXT PRIMARY KEY, channel TEXT, date TEXT,
        text TEXT, summary TEXT, category TEXT, severity TEXT)""")
    cols = [r[1] for r in db.execute("PRAGMA table_info(posts)")]
    if "digested" not in cols:                       # remember what was already emailed
        db.execute("ALTER TABLE posts ADD COLUMN digested INTEGER DEFAULT 0")
    if "entities" not in cols:
        db.execute("ALTER TABLE posts ADD COLUMN entities TEXT")
    db.execute("CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(date)")
    db.commit()
    return db
