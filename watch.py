from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import ReturnDocument
from bot import MeTube
from db import *

# ✅ WATCH CALLBACK
@MeTube.on_callback_query(filters.regex(r"^watch_(.+)"))
async def watch_callback(client, query):
    user = query.from_user.id
    video_id = query.data.split("_")[1]

    video = videos.find_one({"video_id": video_id})
    if not video:
        await query.answer("Video not found!", show_alert=True)
        return

    channel = channels.find_one({"channel_id": video.get("channel_id")})

    # ✅ Count Views
    videos.update_one({"video_id": video_id}, {"$inc": {"views": 1}})
    if channel:
        channels.update_one({"channel_id": video["channel_id"]}, {"$inc": {"total_views": 1}})

    await send_watch_video(query, video_id, user)
    await query.answer()


# ✅ Like Handler
@MeTube.on_callback_query(filters.regex(r"^like_(.+)"))
async def like_video(client, query):
    user = query.from_user.id
    video_id = query.data.split("_")[1]

    if likes.find_one({"user_id": user, "video_id": video_id}):
        await query.answer("Already liked ✅", show_alert=True)
        return

    videos.update_one({"video_id": video_id}, {"$inc": {"likes": 1}})
    likes.insert_one({"user_id": user, "video_id": video_id})

    video = videos.find_one({"video_id": video_id})
    await refresh_buttons(query, video)
    await query.answer("Liked 👍")


# ✅ Dislike Handler
@MeTube.on_callback_query(filters.regex(r"^dislike_(.+)"))
async def dislike_video(client, query):
    user = query.from_user.id
    video_id = query.data.split("_")[1]

    if dislikes.find_one({"user_id": user, "video_id": video_id}):
        await query.answer("Already disliked ❌", show_alert=True)
        return

    videos.update_one({"video_id": video_id}, {"$inc": {"dislikes": 1}})
    dislikes.insert_one({"user_id": user, "video_id": video_id})

    video = videos.find_one({"video_id": video_id})
    await refresh_buttons(query, video)
    await query.answer("Disliked 👎")


# ✅ Subscribe
@MeTube.on_callback_query(filters.regex(r"^sub_(.+)"))
async def subscribe(client, query):
    user = query.from_user.id
    channel_id = query.data.split("_")[1]

    if subscriptions.find_one({"user_id": user, "channel_id": channel_id}):
        await query.answer("Already subscribed!", show_alert=True)
        return

    channels.update_one({"channel_id": channel_id}, {"$inc": {"subscribers": 1}})
    subscriptions.insert_one({"user_id": user, "channel_id": channel_id})

    video_id = query.message.caption.split()[-1]
    video = videos.find_one({"video_id": video_id})
    await refresh_buttons(query, video)
    await query.answer("Subscribed ✅")


# ✅ Unsubscribe
@MeTube.on_callback_query(filters.regex(r"^unsub_(.+)"))
async def unsubscribe(client, query):
    user = query.from_user.id
    channel_id = query.data.split("_")[1]

    if not subscriptions.find_one({"user_id": user, "channel_id": channel_id}):
        await query.answer("You aren’t subscribed!", show_alert=True)
        return

    channels.update_one({"channel_id": channel_id}, {"$inc": {"subscribers": -1}})
    subscriptions.delete_one({"user_id": user, "channel_id": channel_id})

    video_id = query.message.caption.split()[-1]
    video = videos.find_one({"video_id": video_id})
    await refresh_buttons(query, video)
    await query.answer("Unsubscribed ❌")


# ✅ Send video with correct UI
async def send_watch_video(query, video_id, user):
    video = videos.find_one({"video_id": video_id})
    channel = channels.find_one({"channel_id": video.get("channel_id")})

    views = video.get("views", 0)
    caption = (
        f"🎬 **{video['title']}**\n"
        f"👁 Views: {views}\n"
        f"👍 {video.get('likes', 0)} | 👎 {video.get('dislikes', 0)}\n"
        f"📌 Channel: {channel.get('channelname') if channel else 'Unknown'}\n"
        f"{video_id}"
    )

    await query.message.reply_video(
        video["file_id"],
        caption=caption,
        reply_markup=await generate_buttons(video_id, user)
    )


# ✅ Main Buttons UI Generator
async def generate_buttons(video_id, user):
    video = videos.find_one({"video_id": video_id})
    channel_id = video.get("channel_id")

    likes_count = video.get("likes", 0)
    dislikes_count = video.get("dislikes", 0)

    is_sub = subscriptions.find_one({"user_id": user, "channel_id": channel_id})
    channel = channels.find_one({"channel_id": channel_id})
    subs_count = channel.get("subscribers", 0)

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"👍 {likes_count}", callback_data=f"like_{video_id}"),
            InlineKeyboardButton(f"👎 {dislikes_count}", callback_data=f"dislike_{video_id}")
        ],
        [
            InlineKeyboardButton(
                f"🔔 Subscribed ({subs_count})" if is_sub else f"➕ Subscribe ({subs_count})",
                callback_data=f"{'unsub' if is_sub else 'sub'}_{channel_id}"
            )
        ],
        [InlineKeyboardButton("🔗 Share", switch_inline_query=video["title"])]
    ])


# ✅ Update Buttons UI
async def refresh_buttons(query, video):
    user = query.from_user.id
    keyboard = await generate_buttons(video["video_id"], user)
    await query.message.edit_reply_markup(reply_markup=keyboard)
