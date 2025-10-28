from pyrogram import filters
from pyrogram.enums import ParseMode
from bot import MeTube
from db import channels
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests

def generate_channel_card(channel):
    # Load Base Template
    base = Image.open("IMG_20251028_063529_945.jpg").convert("RGB")
    draw = ImageDraw.Draw(base)

    # --- Load Channel Profile Photo ---
    if channel.get("pic"):
        try:
            r = requests.get(channel["pic"])
            pfp = Image.open(BytesIO(r.content)).convert("RGB").resize((250, 250))

            # Circle Mask for round dp
            mask = Image.new("L", (250, 250), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 250, 250), fill=255)
            base.paste(pfp, (330, 100), mask) # Change position if needed
        except:
            pass

    # Fonts (Install DejaVu Sans on server if needed)
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 45)
    font_stats = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)

    # --- Write Text on Image ---
    draw.text((350, 105), f"{channel['channel_name']}", fill="white", font=font_title)
    draw.text((350, 180), f"Channel ID: {channel['_id']}", fill="white", font=font_stats)
    draw.text((350, 250), f"Videos: {channel['videos']}", fill="white", font=font_stats)
    draw.text((350, 280), f"Subscribers: {channel['subscribers']}", fill="white", font=font_stats)
    draw.text((350, 340), f"Views: {channel['total_views']}", fill="white", font=font_stats)
    draw.text((350, 390), f"Likes: {channel['likes']}", fill="white", font=font_stats)

    # Save Output
    output = BytesIO()
    output.name = "my_channel_status.jpg"
    base.save(output, "JPEG")
    output.seek(0)
    return output

@MeTube.on_message(filters.command("my_channel") & filters.private, group=5)
async def my_channel(client, message):
    user_id = message.from_user.id
    channel = channels.find_one({"owner_id": user_id})

    if not channel:
        return await message.reply("❌ You haven't registered any channel yet!\nUse: `/register`")

    card = generate_channel_card(channel)

    await message.reply_photo(
        photo=card,
        caption=f"✅ **Your Channel Stats Generated!**",
        parse_mode=ParseMode.MARKDOWN
    )
