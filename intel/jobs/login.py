# login.py - run ONCE by hand to create session.session
import asyncio
from telethon import TelegramClient
from ..config import API_ID, API_HASH, PHONE, SESSION_PATH

async def main():
    c = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await c.connect()
    if not await c.is_user_authorized():
        await c.send_code_request(PHONE)
        await c.sign_in(PHONE, input("Code from Telegram: "))
    print("Logged in. Session saved."); await c.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
