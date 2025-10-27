from pyrogram import filters
from pyrogram.enums import ParseMode
from bot import MeTube
from db import channels

@MeTube.on_message(filters.command("my_channel") & filters.private)
async def my_channel(client, message):
    user_id = message.from_user.id
    
    # Check channel exists
    channel = channels.find_one({"owner_id": user_id})
    if not channel:
        return await message.reply("❌ You haven't registered any channel yet!\nUse: `/register`")

    # Prepare caption
    caption = (
        f"📺 **Your Channel Information**\n\n"
        f"🔹 **Channel Name:** `{channel['channel_name']}`\n"
        f"🆔 **Channel ID:** `{channel['_id']}`\n"
        f"📄 **Description:** {channel['desc']}\n\n"
        f"🎞 **Videos:** `{channel['videos']}`\n"
        f"👥 **Subscribers:** `{channel['subscribers']}`\n"
        f"👀 **Total Views:** `{channel['total_views']}`\n"
        f"❤️ **Likes:** `{channel['likes']}`\n"
    )

    # Send with profile picture if exists
    if channel.get("pic"):
        try:
            await message.reply_photo(
                channel["pic"],
                caption=caption,
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            await message.reply(caption, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply(caption, parse_mode=ParseMode.MARKDOWN)
