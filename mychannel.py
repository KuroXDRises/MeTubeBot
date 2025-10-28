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
            pfp = Image.open(pic_path).convert("RGB").resize((350, 350))

        # Circle Mask for round DP
            mask = Image.new("L", (350, 350), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 350, 350), fill=255)

        # 🟢 Create stroke (white border)
            stroke_width = 10  # border thickness
            stroke_size = 350 + (stroke_width * 2)
            stroke_img = Image.new("RGBA", (stroke_size, stroke_size), (0, 0, 0, 0))
            stroke_draw = ImageDraw.Draw(stroke_img)
            stroke_draw.ellipse(
                (0, 0, stroke_size, stroke_size),
                fill=None,
                outline=(255, 255, 255, 255),  # white color
                width=stroke_width
        )

        # 🟣 Paste profile pic with mask inside stroke
            stroke_img.paste(pfp, (stroke_width, stroke_width), mask)

        # 🖼 Final paste on base image
            base.paste(stroke_img, (60, 40), stroke_img)

            os.remove(pic_path)

        except Exception as e:
            print("Pic error:", e)

    # Fonts (Install DejaVu Sans on server if needed)
    font_title = ImageFont.truetype("TrajanPro-Bold.otf", 45)
    font_stats = ImageFont.truetype("TrajanPro-Rugular.ttf", 32)

    # --- Write Text on Image ---
    draw.text((465, 140), f"{channel['channel_name']}", fill="black", font=font_title)
    draw.text((460, 280), f"Channel ID: {channel['_id']}", fill="black", font=font_stats)
    draw.text((460, 330), f"Videos: {channel['videos']}", fill="black", font=font_stats)
    draw.text((460, 380), f"Subscribers: {channel['subscribers']}", fill="black", font=font_stats)
    draw.text((460, 430), f"Views: {channel['total_views']}", fill="black", font=font_stats)
    draw.text((460, 480), f"Likes: {channel['likes']}", fill="black", font=font_stats)

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
