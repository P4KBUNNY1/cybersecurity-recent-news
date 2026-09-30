# scraper.py - fetch NEW posts from every channel in CHANNELS
# A channel can be a username (BugCrowd), a t.me link, or the channel's display name.
import asyncio, re
from telethon import TelegramClient, functions
from telethon.errors import FloodWaitError, ChannelPrivateError
from ..config import API_ID, API_HASH, CHANNELS, FETCH_LIMIT, SESSION_PATH
from ..db import get_db

def last_id(db, label):
    r = db.execute("SELECT MAX(CAST(substr(id, length(channel)+2) AS INTEGER)) "
                   "FROM posts WHERE channel=?", (label,)).fetchone()
    return r[0] or 0

_dialogs = None
async def resolve(client, name):
    """username -> joined chat title -> global search (exact title only)."""
    global _dialogs
    if re.fullmatch(r"[A-Za-z0-9_]{4,}", name):
        try: return await client.get_entity(name)
        except Exception: pass
    want = name.lower()
    if _dialogs is None:
        _dialogs = [d async for d in client.iter_dialogs() if d.is_channel]
    exact = [d.entity for d in _dialogs if d.name.lower() == want]
    if exact: return exact[0]
    part = [d.entity for d in _dialogs if want in d.name.lower()]
    if part: return part[0]
    res = await client(functions.contacts.SearchRequest(q=name, limit=10))
    chans = [c for c in res.chats if getattr(c, "broadcast", False)]
    for c in chans:
        if c.title.lower() == want: return c
    hint = ", ".join(f"@{c.username} ({c.title})" for c in chans[:4] if c.username)
    raise ValueError(f"'{name}' not found. Use its @username in CHANNELS. Close matches: {hint or 'none'}")

async def main():
    if not CHANNELS:
        print("[ERROR] No channels set. Fill CHANNELS in .env"); return 1
    print(f"Channels to fetch ({len(CHANNELS)}): {', '.join(CHANNELS)}")
    db = get_db()
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        print("[ERROR] Telegram session not logged in. Run: python login.py"); return 1
    for ch in CHANNELS:
        try:
            entity = await resolve(client, ch)
            label = getattr(entity, "username", None) or entity.title   # stored as the channel name
            new = 0
            async for msg in client.iter_messages(entity, limit=FETCH_LIMIT, min_id=last_id(db, label)):
                text = (msg.message or "").strip()
                if text:
                    db.execute("INSERT OR IGNORE INTO posts(id,channel,date,text) VALUES(?,?,?,?)",
                               (f"{label}_{msg.id}", label, str(msg.date), text))
                    new += 1
            db.commit()
            print(f"[OK] {ch} -> {label}: {new} new posts")
        except FloodWaitError as e:
            print(f"[WAIT] {ch}: rate-limited, sleeping {e.seconds}s"); await asyncio.sleep(e.seconds + 5)
        except ChannelPrivateError:
            print(f"[SKIP] {ch}: private - join it in Telegram first")
        except Exception as e:
            print(f"[ERROR] {ch}: {e}")
    await client.disconnect()
    return 0

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
