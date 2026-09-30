# config.py - settings (.env) and every file path in one place
import os, shutil
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
LOG_DIR = ROOT / "logs"
DATA_DIR.mkdir(exist_ok=True); LOG_DIR.mkdir(exist_ok=True)
for _n in ("cyber.db", "session.session"):          # old flat layout -> data/
    if (ROOT / _n).exists() and not (DATA_DIR / _n).exists():
        shutil.move(str(ROOT / _n), str(DATA_DIR / _n))

DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "cyber.db"))
SESSION_PATH = str(DATA_DIR / "session")            # Telethon adds ".session"
KEV_CACHE = DATA_DIR / "kev_cache.json"
TRAIN_FILE = DATA_DIR / "train.jsonl"
LOCK_FILE = DATA_DIR / ".pipeline.lock"
LOG_FILE = LOG_DIR / "pipeline.log"

API_ID = int(os.getenv("TG_API_ID", "0"))
API_HASH = os.getenv("TG_API_HASH", "")
PHONE = os.getenv("TG_PHONE", "")

def _clean(c):
    c = c.strip().strip('"\'')
    for p in ("https://t.me/", "http://t.me/", "t.me/"):
        if c.lower().startswith(p): c = c[len(p):]
    return c.lstrip("@").split("/")[0].strip()
CHANNELS = [x for x in (_clean(c) for c in os.getenv("CHANNELS", "").split(",")) if x]

MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
FETCH_LIMIT = int(os.getenv("FETCH_LIMIT", "100"))
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
DIGEST_TO = os.getenv("DIGEST_TO", GMAIL_USER)
