from bot import MeTube
from pyrogram.types import (
    InlineQueryResultPhoto,
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

    search_results = videos.find({
        "$or": [
            {"video_id": query},
            {"title": Regex(query, "i")}
        ]
    }).limit(20)

    for video in search_results:

        caption = (
            f"🎬 **{video['title']}**\n"
            f"👁 Views: {video.get('views', 0)}\n"
            f"👍 {video.get('likes', 0)} | 👎 {video.get('dislikes', 0)}\n"
            f"📌 Channel: {video.get('channelname', 'Unknown')}\n\n"
            f"📽 Video ID: `{video['video_id']}`"
        )

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Watch", callback_data=f"watch_{video['video_id']}")]
        ])

        results.append(
            InlineQueryResultPhoto(
                id=video["video_id"],
                title=video["title"],
                caption=caption,
                photo_url=video["thumb_url"],
                thumb_url=video["thumb_url"],
                reply_markup=buttons
            )
        )

    await inline_query.answer(results, cache_time=0)
    await inline_query.answer(results, cache_time=0)
