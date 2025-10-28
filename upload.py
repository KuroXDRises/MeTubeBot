from pyrogram import filters
from db import videos, channels
from bot import MeTube
from pyrogram.types import Message
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

upload_state = {}

@MeTube.on_message(filters.private & filters.command("upload"))
async def upload_command(client, message: Message):
    upload_state[message.from_user.id] = {"step": "video"}
    await message.reply("🎥 Send me the **Video** you want to upload.")


@MeTube.on_message(filters.private & filters.video)
async def get_video(client, message: Message):
    user_id = message.from_user.id
    if upload_state.get(user_id, {}).get("step") == "video":
        upload_state[user_id]["video"] = message.video.file_id
        upload_state[user_id]["step"] = "thumb"
        await message.reply("📌 Send **Thumbnail** image for the video.")


@MeTube.on_message(filters.private & filters.photo)
async def get_thumbnail(client, message: Message):
    user_id = message.from_user.id
    if upload_state.get(user_id, {}).get("step") == "thumb":
        upload_state[user_id]["thumb"] = message.photo.file_id
        upload_state[user_id]["step"] = "title"
        await message.reply("✍️ Now send **Video Title**")


@MeTube.on_message(filters.private & filters.text)
async def get_text_data(client, message: Message):
    user_id = message.from_user.id
    state = upload_state.get(user_id)

    if not state:
        return
    
    if state["step"] == "title":
        state["title"] = message.text
        state["step"] = "desc"
        await message.reply("📝 Send **Video Description**")
        return
    
    if state["step"] == "desc":
        state["desc"] = message.text

        # Fetch channel using owner id
        channel = channels.find_one({"owner_id": str(user_id)})
        if not channel:
            await message.reply("❌ Channel not found! Register a channel first.")
            upload_state.pop(user_id, None)
            return

        channel_name = channel["channel_name"]

        # Generate Next Video ID
        video_count = videos.count_documents({"channelname": channel_name}) + 1
        video_id = f"{channel_name}-{video_count}"

        # Upload to actual channel
        sent_msg = await client.send_video(
            chat_id=message.chat.id,
            video=state["video"],
            thumb=state["thumb"],
            caption=f"🎬 **{state['title']}**\n\n{state['desc']}"
        )

        # Save in DB
        # Save in DB
        videos.insert_one({
            "video_id": video_id,
            "title": state["title"],
            "description": state["desc"],
            "video_file_id": state["video"],
            "thumb_file_id": state["thumb"],
            "likes": 0,
            "dislikes": 0,
            "views": 0,
            "channelname": channel_name
        })

        # Final message with thumbnail + details + buttons

        keyboard = InlineKeyboardMarkup(
             [
                 [
                     InlineKeyboardButton(
                         "🔗 Share",
                         switch_inline_query=f"{video_id}"
                     )
                 ]
             ]  
         )
        await message.reply_photo(
            photo=state["thumb"],
            caption=(
                f"✅ **Video Added Successfully!**\n\n"
                f"🎬 **{state['title']}**\n"
                f"👁 Views: 0\n"
                f"👍 Likes: 0 | 👎 Dislikes: 0\n"
                f"📌 Channel: **{channel_name}**\n\n"
                f"💡 Video ID: `{video_id}`\n"
                f"🔗 **Share with your friends!**"
            ),
            reply_markup=keyboard,
            parse_mode="markdown"
)

        upload_state.pop(user_id, None)
