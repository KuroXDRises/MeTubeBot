from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot import MeTube
from db import videos, channels


async def send_watch_video(client, query, video):

    channel = channels.find_one({"channel_id": video.get("channel_id")})
    channel_name = channel.get("channel_name", "Unknown") if channel else "Unknown"
    subs = channel.get("subscribers", 0) if channel else 0

    title = video.get("title", "Unknown")
    views = video.get("views", 0)
    likes = video.get("likes", 0)
    dislikes = video.get("dislikes", 0)
    video_file = video.get("video_file_id")

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"👍 {likes}", callback_data=f"like_{video['video_id']}"),
            InlineKeyboardButton(f"👎 {dislikes}", callback_data=f"dislike_{video['video_id']}")
        ],
        [
            InlineKeyboardButton(f"🔔 Subscribe ({subs})",
                                 callback_data=f"sub_{video.get('channel_id', '0')}")
        ],
        [
            InlineKeyboardButton("📤 Share",
                                 switch_inline_query=video.get("video_id", ""))
        ]
    ])

    caption = (
        f"🎬 **{title}**\n"
        f"👁 Views: {views}\n"
        f"👍 {likes} | 👎 {dislikes}\n"
        f"📺 Channel: **{channel_name}**"
    )

    if not video_file:
        return await query.answer("❌ Video file missing!", show_alert=True)

    if query.message:
        await query.message.reply_video(video_file, caption=caption, reply_markup=keyboard)
    else:
        await client.send_video(
            chat_id=query.from_user.id,
            video=video_file,
            caption=caption,
            reply_markup=keyboard
        )


async def update_buttons(query, video):

    channel = channels.find_one({"channel_id": video.get("channel_id")})
    subs = channel.get("subscribers", 0) if channel else 0

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"👍 {video.get('likes',0)}", callback_data=f"like_{video['video_id']}"),
            InlineKeyboardButton(f"👎 {video.get('dislikes',0)}", callback_data=f"dislike_{video['video_id']}")
        ],
        [
            InlineKeyboardButton(f"🔔 Subscribe ({subs})",
                                 callback_data=f"sub_{video.get('channel_id', '0')}")
        ],
        [
            InlineKeyboardButton("📤 Share", switch_inline_query=video.get("video_id", ""))
        ]
    ])

    try:
        await query.message.edit_reply_markup(keyboard)
    except:
        pass



@MeTube.on_callback_query(filters.regex(r"^watch_(.+)"))
async def watch_callback(client, query):
    video_id = query.data.split("_")[1]
    video = videos.find_one({"video_id": video_id})

    if not video:
        return await query.answer("❌ Video Not Found", show_alert=True)

    videos.update_one({"video_id": video_id}, {"$inc": {"views": 1}})
    channels.update_one({"channel_id": video.get("channel_id")}, {"$inc": {"total_views": 1}})

    video = videos.find_one({"video_id": video_id})
    await send_watch_video(client, query, video)
    await query.answer()


@MeTube.on_callback_query(filters.regex(r"^like_(.+)"))
async def like_video(client, query):
    video_id = query.data.split("_")[1]
    video = videos.find_one({"video_id": video_id})

    if not video:
        return await query.answer("Video not found ❌", show_alert=True)

    videos.update_one({"video_id": video_id}, {"$inc": {"likes": 1}})
    channels.update_one({"channel_id": video.get("channel_id")}, {"$inc": {"total_likes": 1}})

    video = videos.find_one({"video_id": video_id})
    await update_buttons(query, video)

    await query.answer("Liked 👍")

@MeTube.on_callback_query(filters.regex(r"^dislike_(.+)"))
async def dislike_video(client, query):
    video_id = query.data.split("_")[1]
    video = videos.find_one({"video_id": video_id})

    if not video:
        return await query.answer("Video not found ❌", show_alert=True)

    videos.update_one({"video_id": video_id}, {"$inc": {"dislikes": 1}})
    channels.update_one({"channel_id": video.get("channel_id")}, {"$inc": {"total_likes": -1}})

    video = videos.find_one({"video_id": video_id})
    await update_buttons(query, video)

    await query.answer("Disliked 👎")

@MeTube.on_callback_query(filters.regex(r"^sub_(.+)"))
async def subscribe_channel(client, query):
    channel_id = query.data.split("_")[1]
    channels.update_one({"channel_id": channel_id}, {"$inc": {"subscribers": 1}})

    video = videos.find_one({"channel_id": channel_id})
    if video:
        await update_buttons(query, video)

    await query.answer("Subscribed ✅")
