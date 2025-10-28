from bot import MeTube
from pyrogram.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
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

    # Search by ID or Title
    search_results = videos.find({
        "$or": [
            {"video_id": query},
            {"title": Regex(query, "i")}
        ]
    }).limit(20)

    for video in search_results:
        results.append(
            InlineQueryResultArticle(
                id=video["video_id"],
                title=video["title"],
                description=f"Channel: {video.get('channelname', 'Unknown')}",
                input_message_content=InputTextMessageContent(
                    message_text=f"/watch {video['video_id']}"
                )
            )
        )

    await inline_query.answer(results, cache_time=0)
