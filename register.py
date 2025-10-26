from pyrogram import Client, filters
from db import channels, generate_channel_id
from pyrogram.enums import ParseMode
from bot import MeTube
REGISTER_STATE = {}
OWNER_ID = 6239769036  # Admin who will receive notifications

@MeTube.on_message(filters.command("register") & filters.private, group=2)
async def register_start(client, message):
    user_id = message.from_user.id
    
    # Check if already made a channel
    if channels.find_one({"owner_id": user_id}):
        return await message.reply("✅ You have already registered your channel!")

    REGISTER_STATE[user_id] = {"step": 1}
    await message.reply("📌 **Step 1:** Enter your **Channel Name** (No stylish letters):")


@MeTube.on_message(filters.text & filters.private, group=3)
async def register_steps(client, message):
    user_id = message.from_user.id

    if user_id not in REGISTER_STATE:
        return
    
    step = REGISTER_STATE[user_id]["step"]

    # Step 1 — Channel Name
    if step == 1:
        if not message.text.replace(" ", "").isalnum():
            return await message.reply("⚠️ Stylish / Symbol letters are not allowed. Use normal characters only.")
        
        REGISTER_STATE[user_id]["channel_name"] = message.text
        REGISTER_STATE[user_id]["step"] = 2
        return await message.reply("📸 **Step 2:** Send Channel **Profile Picture**.\nOr type: `skip`")

    # Step 2 — Profile Picture
    if step == 2:
        if message.text.lower() == "skip":
            REGISTER_STATE[user_id]["pic"] = None
        elif message.photo:
            REGISTER_STATE[user_id]["pic"] = message.photo.file_id
        else:
            return await message.reply("⚠️ Send a photo or type `skip`.")

        REGISTER_STATE[user_id]["step"] = 3
        return await message.reply("📝 **Step 3:** Send Channel Description:")

    # Step 3 — Description
    if step == 3:
        REGISTER_STATE[user_id]["desc"] = message.text
        REGISTER_STATE[user_id]["step"] = 4
        return await message.reply("🖼 **Step 4:** Send Channel Banner.\nOr type: `skip`")

    # Step 4 — Banner
    if step == 4:
        if message.text.lower() == "skip":
            REGISTER_STATE[user_id]["banner"] = None
        elif message.photo:
            REGISTER_STATE[user_id]["banner"] = message.photo.file_id
        else:
            return await message.reply("⚠️ Send a photo or type `skip`.")

        # ✅ Generate Channel ID
        channel_id = generate_channel_id()

        # ✅ Insert in Database
        channels.insert_one({
            "_id": channel_id,
            "owner_id": user_id,
            "channel_name": REGISTER_STATE[user_id]["channel_name"],
            "pic": REGISTER_STATE[user_id]["pic"],
            "banner": REGISTER_STATE[user_id]["banner"],
            "desc": REGISTER_STATE[user_id]["desc"],
            "videos": 0,
            "subscribers": 0,
            "total_views": 0,
            "likes": 0
        })

        # ✅ Notify the owner
        await client.send_message(
            OWNER_ID,
            f"📢 **New Channel Registered!**\n\n"
            f"👤 User: `{user_id}`\n"
            f"📛 Name: **{REGISTER_STATE[user_id]['channel_name']}**\n"
            f"🆔 Channel ID: `{channel_id}`",
            parse_mode=ParseMode.MARKDOWN
        )

        del REGISTER_STATE[user_id]  # Clear memory

        return await message.reply(
            f"🎉 **Channel Registered Successfully!**\n\n"
            f"🆔 Your Channel ID: `{channel_id}`\n"
            f"Use **/mychannel** to manage your channel.",
            parse_mode=ParseMode.MARKDOWN
        )
