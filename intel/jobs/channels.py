# list_channels.py - shows every channel you joined with the exact name to put in CHANNELS
import asyncio
from telethon import TelegramClient
from ..config import API_ID, API_HASH, SESSION_PATH

async def main():
    c = TelegramClient(SESSION_PATH, API_ID, API_HASH); await c.connect()
    print(f"{'USERNAME (use this)':30} TITLE")
    async for d in c.iter_dialogs():
        if d.is_channel and not d.is_group:
            u = getattr(d.entity, "username", None)
            print(f"{(u or '(private - use title)'):30} {d.name}")
    await c.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
