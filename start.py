from pyrogram import Client, filters
from db import *
from pyrogram.enums import ParseMode
from bot import Metube
@MeTube.on_message(filters.command("start"), group=1)
async def start(client, message):
    user = message.from_user

    await message.reply_photo(
        photo="https://files.catbox.moe/vomj5q.jpg",
        caption=f"👋 **Hello {user.first_name}!**\n\n"
                "Welcome to **MeTube** 🎥\n"
                "Here you can download anime clips, episodes & more!\n\n"
                "🔥 Send me **link** or **anime name** to start.",
        parse_mode=ParseMode.MARKDOWN
    )
