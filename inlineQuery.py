from bot import MeTube
from pyrogram.types import (
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from bson.regex import Regex
from db import *
@MeTube.on_inline_query()
async def inline_query_handler(client, inline_query):
    query = inline_query.query.strip()

    results = []

    if not query:
        await inline_query.answer([], cache_time=0)
        return

    # Search video by ID (Exact match)
    video = videos.find_one({"video_id": query})

    if video:
        caption = (
            f"🎬 **{video['title']}**\n"
            f"👁 Views: {video.get('views', 0)}\n"
            f"👍 {video.get('likes', 0)} | 👎 {video.get('dislikes', 0)}\n"
            f"📌 Channel: {video.get('channelname', 'Unknown')}\n\n"
            f"📽 Video ID: `{video['video_id']}`"
        )

        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton("▶️ Watch", callback_data=f"watch_{video['video_id']}")]]
        )

        results.append(
            InlineQueryResultPhoto(
                id=video['video_id'],
                title=video['title'],
                caption=caption,
                photo_url=video['thumb_file_id'],
                thumb_url=video['thumb_file_id'],
                reply_markup=buttons
            )
        )

    # Search by title also (Case-Insensitive)
    title_results = videos.find({"title": Regex(query, "i")}).limit(10)

    for vid in title_results:
        if vid['video_id'] == query:  # already added above
            continue

        results.append(
            InlineQueryResultArticle(
                id=vid["video_id"],
                title=vid["title"],
                input_message_content=InputTextMessageContent(
                    message_text=f"/watch {vid['video_id']}"
                ),
                description=f"Channel: {vid.get('channelname', 'Unknown')}",
                thumb_url=vid["thumb_file_id"]
            )
        )

    await inline_query.answer(results, cache_time=0)
