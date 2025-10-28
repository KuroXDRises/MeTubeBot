from pyrogram import filters
from pyrogram.enums import ParseMode
from bot import MeTube
from db import channels
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

# ---------------- GENERATE CHANNEL CARD ---------------- #
async def generate_channel_card(client, channel):
    # Load Base Template
    base = Image.open("IMG_20251028_063529_945.jpg").convert("RGB")
    draw = ImageDraw.Draw(base)

    # --- Load Channel Profile Photo ---
    if channel.get("pic"):
        try:
            pic_path = await client.download_media(channel["pic"])
            pfp = Image.open(pic_path).convert("RGB").resize((300, 300))

            # Circle Mask for round DP
            mask = Image.new("L", (300, 300), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 300, 300), fill=300)

            base.paste(pfp, (95, 70), mask)  # adjust position as needed
            os.remove(pic_path)
        except Exception as e:
            print("Pic error:", e)

    # Fonts (Install DejaVu Sans on server if needed)
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 45)
    font_stats = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)

    # --- Write Text on Image ---
    draw.text((460, 145), f"{channel['channel_name']}", fill="white", font=font_title)
    draw.text((460, 280), f"Channel ID: {channel['_id']}", fill="white", font=font_stats)
    draw.text((460, 330), f"Videos: {channel['videos']}", fill="white", font=font_stats)
    draw.text((460, 380), f"Subscribers: {channel['subscribers']}", fill="white", font=font_stats)
    draw.text((460, 430), f"Views: {channel['total_views']}", fill="white", font=font_stats)
    draw.text((460, 480), f"Likes: {channel['likes']}", fill="white", font=font_stats)

    # Save Output
    output = BytesIO()
    output.name = "my_channel_status.jpg"
    base.save(output, "JPEG")
    output.seek(0)
    return output


# ---------------- COMMAND HANDLER ---------------- #
@MeTube.on_message(filters.command("my_channel") & filters.private, group=5)
async def my_channel(client, message):
    user_id = message.from_user.id
    channel = channels.find_one({"owner_id": user_id})

    if not channel:
        return await message.reply("❌ You haven't registered any channel yet!\nUse: `/register`")

    card = await generate_channel_card(client, channel)

    await message.reply_photo(
        photo=card,
        caption=f"✅ **Your Channel Stats Generated!**",
        parse_mode=ParseMode.MARKDOWN
    )
