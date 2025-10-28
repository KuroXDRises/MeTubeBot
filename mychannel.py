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

            # White stroke border
            stroke_width = 10
            stroke_size = 350 + (stroke_width * 2)
            stroke_img = Image.new("RGBA", (stroke_size, stroke_size), (0, 0, 0, 0))
            stroke_draw = ImageDraw.Draw(stroke_img)
            stroke_draw.ellipse(
                (0, 0, stroke_size, stroke_size),
                fill=None,
                outline=(255, 255, 255, 255),
                width=stroke_width
            )

            # Paste profile pic inside border
            stroke_img.paste(pfp, (stroke_width, stroke_width), mask)
            base.paste(stroke_img, (60, 40), stroke_img)

            os.remove(pic_path)
        except Exception as e:
            print("Pic error:", e)

    # Fonts
    font_title = ImageFont.truetype("TrajanPro-Bold.otf", 45)
    font_stats = ImageFont.truetype("TrajanPro-Regular.ttf", 32)
    font_box = ImageFont.truetype("TrajanPro-Regular.ttf", 35)

    # --- Write Text on Main Area ---
    draw.text((465, 140), f"{channel['channel_name']}", fill="black", font=font_title)
    draw.text((460, 280), f"Channel ID: {channel['_id']}", fill="black", font=font_stats)
    draw.text((460, 330), f"Videos: {channel['videos']}", fill="black", font=font_stats)
    draw.text((460, 380), f"Subscribers: {channel['subscribers']}", fill="black", font=font_stats)
    draw.text((460, 430), f"Views: {channel['total_views']}", fill="black", font=font_stats)
    draw.text((460, 480), f"Likes: {channel['likes']}", fill="black", font=font_stats)

    # --- Bottom Info Box ---
    box_height = 180
    box_y_start = base.height - box_height
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(
        [(0, box_y_start), (base.width, base.height)],
        fill=(255, 255, 255, 200)
    )

    base = Image.alpha_composite(base.convert("RGBA"), overlay)

    draw = ImageDraw.Draw(base)
    text_y = box_y_start + 35
    draw.text((80, text_y), f"Name: {channel['channel_name']}", fill="black", font=font_box)
    draw.text((80, text_y + 45), f"Videos: {channel['videos']}", fill="black", font=font_box)
    draw.text((80, text_y + 90), f"Subscribers: {channel['subscribers']}", fill="black", font=font_box)
    draw.text((520, text_y + 45), f"Views: {channel['total_views']}", fill="black", font=font_box)
    draw.text((520, text_y + 90), f"Likes: {channel['likes']}", fill="black", font=font_box)

    # Save output
    output = BytesIO()
    output.name = "my_channel_status.jpg"
    base.convert("RGB").save(output, "JPEG")
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

    # 📝 Caption with full details
    caption_text = (
        f"📊 **Your Channel Stats**\n\n"
        f"🏷️ **Name:** {channel['channel_name']}\n"
        f"🎬 **Videos:** {channel['videos']}\n"
        f"👥 **Subscribers:** {channel['subscribers']}\n"
        f"👀 **Views:** {channel['total_views']}\n"
        f"❤️ **Likes:** {channel['likes']}\n"
        f"🆔 **Channel ID:** `{channel['_id']}`"
    )

    await message.reply_photo(
        photo=card,
        caption=caption_text,
        parse_mode=ParseMode.MARKDOWN
            )
