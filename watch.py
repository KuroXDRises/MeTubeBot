from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot import MeTube
from db import videos, channels


# ✅ Send Video in watch UI
async def send_watch_video(query, video):

    channel = channels.find_one({"channel_id": video.get("channel_id")})

    title = video.get("title", "Unknown")
    views = video.get("views", 0)
    likes = video.get("likes", 0)
    dislikes = video.get("dislikes", 0)
    channel_name = channel.get("channel_name") if channel else "Unknown"
    subs = channel.get("subscribers", 0) if channel else 0

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"👍 {likes}", callback_data=f"like_{video['video_id']}"),
            InlineKeyboardButton(f"👎 {dislikes}", callback_data=f"dislike_{video['video_id']}")
        ],
        [
            InlineKeyboardButton(f"🔔 Subscribe ({subs})", callback_data=f"sub_{video['channel_id']}")
        ],
        [
            InlineKeyboardButton("📤 Share", switch_inline_query=video["video_id"])
        ]
    ])

    await query.message.reply_video(
        video["video_file_id"],
        caption=(
            f"🎬 **{title}**\n"
            f"👁 Views: {views}\n"
            f"👍 {likes} | 👎 {dislikes}\n"
            f"📺 Channel: **{channel_name}**"
        ),
        reply_markup=keyboard
    )


# ✅ WATCH Handler
@MeTube.on_callback_query(filters.regex(r"^watch_(.+)"))
async def watch_callback(client, query):
    video_id = query.data.split("_")[1]

    video = videos.find_one({"video_id": video_id})
    if not video:
        return await query.answer("Video not found ❌", show_alert=True)

    videos.update_one({"video_id": video_id}, {"$inc": {"views": 1}})

    if video.get("channel_id"):
        channels.update_one({"channel_id": video["channel_id"]}, {"$inc": {"total_views": 1}})

    video = videos.find_one({"video_id": video_id})
    await send_watch_video(query, video)

    await query.answer()


# ✅ LIKE Button
@MeTube.on_callback_query(filters.regex(r"^like_(.+)"))
async def like_video(client, query):
    video_id = query.data.split("_")[1]
    videos.update_one({"video_id": video_id}, {"$inc": {"likes": 1}})

    video = videos.find_one({"video_id": video_id})
    await update_buttons(query, video)

    await query.answer("Liked 👍")


# ✅ DISLIKE Button
@MeTube.on_callback_query(filters.regex(r"^dislike_(.+)"))
async def dislike_video(client, query):
    video_id = query.data.split("_")[1]
    videos.update_one({"video_id": video_id}, {"$inc": {"dislikes": 1}})

    video = videos.find_one({"video_id": video_id})
    await update_buttons(query, video)

    await query.answer("Disliked 👎")


# ✅ SUBSCRIBE
@MeTube.on_callback_query(filters.regex(r"^sub_(.+)"))
async def subscribe_channel(client, query):
    channel_id = query.data.split("_")[1]
    channels.update_one({"channel_id": channel_id}, {"$inc": {"subscribers": 1}})

    # ✅ Only refresh buttons properly
    video_id = query.message.caption.split("\n")[0].replace("🎬 **", "").replace("**", "")
    video = videos.find_one({"title": video_id})

    if video:
        await update_buttons(query, video)

    await query.answer("Subscribed ✅")


# ✅ Refresh Buttons — No broken message edit
async def update_buttons(query, video):
    channel = channels.find_one({"channel_id": video.get("channel_id")})

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"👍 {video.get('likes',0)}", callback_data=f"like_{video['video_id']}"),
            InlineKeyboardButton(f"👎 {video.get('dislikes',0)}", callback_data=f"dislike_{video['video_id']}")
        ],
        [
            InlineKeyboardButton(f"🔔 Subscribe ({channel.get('subscribers',0)})",
                                 callback_data=f"sub_{video['channel_id']}")
        ],
        [
            InlineKeyboardButton("📤 Share", switch_inline_query=video["video_id"])
        ]
    ])

    await query.message.edit_reply_markup(keyboard)
