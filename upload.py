from pyrogram import filters
from db import videos, channels
from bot import MeTube
from pyrogram.types import Message
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

upload_state = {}


@MeTube.on_message(filters.private & filters.command("upload"))
async def upload_command(client, message: Message):
    upload_state[message.from_user.id] = {"step": "video"}
    await message.reply("🎥 Send the **Video File** you want to upload.")


@MeTube.on_message(filters.private & filters.video)
async def get_video(client, message: Message):
    user_id = message.from_user.id
    if upload_state.get(user_id, {}).get("step") == "video":
        upload_state[user_id]["video"] = message.video.file_id
        upload_state[user_id]["step"] = "thumb_url"
        await message.reply("🌐 Send **Thumbnail URL Link** (Must be a direct link to image)")


@MeTube.on_message(filters.private & filters.text)
async def get_text_data(client, message: Message):
    user_id = message.from_user.id
    state = upload_state.get(user_id)

    if not state:
        return

    msg = message.text.strip()

    if state["step"] == "thumb_url":
        if not (msg.startswith("http://") or msg.startswith("https://")):
            await message.reply("❌ Invalid URL! Please send a valid **thumbnail image URL**.")
            return

        state["thumb_url"] = msg
        state["step"] = "title"
        await message.reply("✍️ Send **Video Title**")
        return

    if state["step"] == "title":
        state["title"] = msg
        state["step"] = "desc"
        await message.reply("📝 Send **Video Description**")
        return

    if state["step"] == "desc":
        state["desc"] = msg

        # Fetch channel
        channel = channels.find_one({"owner_id": user_id})
        if not channel:
            await message.reply("❌ Channel not found! Register a channel first.")
            upload_state.pop(user_id, None)
            return

        channel_name = channel["channel_name"]

        # Create unique video id
        video_count = videos.count_documents({"channelname": channel_name}) + 1
        video_id = f"{channel_name}-{video_count}"

        videos.insert_one({
            "video_id": video_id,
            "title": state["title"],
            "description": state["desc"],
            "video_file_id": state["video"],
            "thumb_url": state["thumb_url"],  # ✅ URL stored!
            "likes": 0,
            "dislikes": 0,
            "views": 0,
            "channelname": channel_name
        })

        channels.update_one(
            {"owner_id": user_id},
            {"$inc": {"videos": 1}}
        )

        # ✅ Share button
        buttons = [[InlineKeyboardButton("📤 Share", switch_inline_query=video_id)]]
        reply_markup = InlineKeyboardMarkup(buttons)

        await message.reply_photo(
            photo=state["thumb_url"],
            caption=(
                f"✅ **Video Uploaded Successfully!**\n\n"
                f"🎬 **{state['title']}**\n"
                f"👁 Views: 0\n"
                f"👍 Likes: 0 | 👎 Dislikes: 0\n"
                f"📌 Channel: **{channel_name}**\n\n"
                f"🔑 Video ID: `{video_id}`"
            ),
            reply_markup=reply_markup
        )

        upload_state.pop(user_id, None)
