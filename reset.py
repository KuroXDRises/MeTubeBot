from pyrogram import filters
from pyrogram.enums import ParseMode
from bot import MeTube
from db import *

DEV = [6239769036]

@MeTube.on_message(filters.command("reset_all") & filters.user(DEV), group=4)
async def reset_all(_, message):
    m = await message.reply_text("Clearing database")

    # Loading animation
    for dot in [".", "..", "...", "...."]:
        await m.edit_text(f"Clearing database{dot}")
        await asyncio.sleep(0.5)  # animation delay

    # Clear all collections
    users.delete_many({})
    channels.delete_many({})
    videos.delete_many({})

    await m.edit_text("✅ **All database data has been cleared!**")
