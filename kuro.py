# filename: metube_bot.py
# Python 3.9+ recommended. Works on Pydroid3 with pyrogram.
import os
import sqlite3
import time
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from PIL import Image
from io import BytesIO

# ---------- CONFIG ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
API_ID = int(os.environ.get("API_ID", "0"))    # optional if using Bot token only
API_HASH = os.environ.get("API_HASH", "")     # optional

APP = Client("metube_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

DB_PATH = "metube.db"
UPLOAD_STATE = {}   # {user_id: {"step": "...", "temp": {...}}}

# ---------- DB helpers ----------
def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS videos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      file_id TEXT NOT NULL,
      thumb_id TEXT,
      title TEXT,
      description TEXT,
      tags TEXT,
      uploader INTEGER,
      upload_time TEXT,
      views INTEGER DEFAULT 0
    )""")
    con.commit()
    con.close()

def add_video(file_id, uploader, title="", description="", tags="", thumb_id=None):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("INSERT INTO videos (file_id, thumb_id, title, description, tags, uploader, upload_time) VALUES (?,?,?,?,?,?,?)",
                (file_id, thumb_id, title, description, tags, uploader, datetime.utcnow().isoformat()))
    vid = cur.lastrowid
    con.commit(); con.close()
    return vid

def get_video(vid):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id,file_id,thumb_id,title,description,tags,uploader,upload_time,views FROM videos WHERE id=?", (vid,))
    row = cur.fetchone()
    con.close()
    return row

def search_videos(q, limit=20):
    qlike = f"%{q}%"
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""SELECT id,title,description,tags,uploader,upload_time,views
                   FROM videos
                   WHERE title LIKE ? OR description LIKE ? OR tags LIKE ?
                   ORDER BY id DESC LIMIT ?""", (qlike, qlike, qlike, limit))
    rows = cur.fetchall()
    con.close()
    return rows

def list_user_videos(user_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id,title,upload_time,views FROM videos WHERE uploader=? ORDER BY id DESC", (user_id,))
    rows = cur.fetchall()
    con.close()
    return rows

def inc_views(vid):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE videos SET views = views + 1 WHERE id=?", (vid,))
    con.commit(); con.close()

def update_title(vid, new_title):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE videos SET title=? WHERE id=?", (new_title, vid))
    con.commit(); con.close()

def delete_video(vid):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM videos WHERE id=?", (vid,))
    con.commit(); con.close()

# ---------- Helpers ----------
def make_video_buttons(vid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶ Watch", callback_data=f"watch:{vid}"),
         InlineKeyboardButton("ℹ Info", callback_data=f"info:{vid}")],
        [InlineKeyboardButton("🔗 Share", switch_inline_query=str(vid))]
    ])

# ---------- Commands ----------
@APP.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    await message.reply_text(
        "MeTube bot — Upload aur Search karo apne videos.\n\nCommands:\n/upload\n/myvideos\n/search <query>\n/watch <id>\n/info <id>\n\nExample: /search cats",
        quote=True
    )

# Upload flow
@APP.on_message(filters.command("upload"))
async def upload_cmd(client, message: Message):
    uid = message.from_user.id
    UPLOAD_STATE[uid] = {"step": "await_video", "temp": {}}
    await message.reply_text("Send me the video file now (as a file or video).", quote=True)

@APP.on_message(filters.video | filters.document)
async def receive_video(client, message: Message):
    uid = message.from_user.id
    state = UPLOAD_STATE.get(uid)
    if not state or state.get("step") != "await_video":
        return  # ignore if not in upload flow

    # Save file_id
    if message.video:
        file_id = message.video.file_id
    else:
        # document could be a video file
        file_id = message.document.file_id

    state["temp"]["file_id"] = file_id
    state["step"] = "await_title"
    await message.reply_text("Got it. Ab title bhejo for the video.", quote=True)

@APP.on_message(filters.text & ~filters.command(["start","upload","search","myvideos","watch","info","rename","delete"]))
async def text_handler(client, message: Message):
    uid = message.from_user.id
    state = UPLOAD_STATE.get(uid)
    if not state:
        return

    step = state.get("step")
    text = message.text.strip()

    if step == "await_title":
        state["temp"]["title"] = text
        state["step"] = "await_description"
        await message.reply_text("Now send description (or type '-' to skip).", quote=True)
        return

    if step == "await_description":
        state["temp"]["description"] = (text if text != "-" else "")
        state["step"] = "await_tags"
        await message.reply_text("Tags? comma separated (or '-' to skip).", quote=True)
        return

    if step == "await_tags":
        tags = (text if text != "-" else "")
        state["temp"]["tags"] = tags
        # finalize
        file_id = state["temp"].get("file_id")
        title = state["temp"].get("title", "")
        desc = state["temp"].get("description", "")
        tgs = state["temp"].get("tags", "")
        vid = add_video(file_id, uid, title, desc, tgs, thumb_id=None)
        UPLOAD_STATE.pop(uid, None)
        await message.reply_text(f"Uploaded! Video ID: {vid}\nUse /watch {vid} to watch or /info {vid} for details.", quote=True)
        return

# My videos
@APP.on_message(filters.command("myvideos"))
async def myvideos_cmd(client, message: Message):
    uid = message.from_user.id
    rows = list_user_videos(uid)
    if not rows:
        await message.reply_text("Tumne koi video upload nahi kiya.", quote=True)
        return
    text = "Your videos:\n\n" + "\n".join([f"ID:{r[0]} — {r[1]} — {r[2][:19]} — {r[3]} views" for r in rows])
    await message.reply_text(text, quote=True)

# Search
@APP.on_message(filters.command("search"))
async def search_cmd(client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("Usage: /search <query>", quote=True)
        return
    q = args[1].strip()
    rows = search_videos(q)
    if not rows:
        await message.reply_text("Kuch bhi nahi mila.", quote=True)
        return
    out = []
    for r in rows:
        out.append(f"ID:{r[0]} — {r[1] or 'No title'} — {r[5][:10]} — {r[6]} views")
    txt = "Search results:\n\n" + "\n".join(out[:20])
    await message.reply_text(txt, quote=True)

# Watch (send the video)
@APP.on_message(filters.command("watch"))
async def watch_cmd(client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("Usage: /watch <video_id>", quote=True)
        return
    try:
        vid = int(args[1].strip())
    except:
        await message.reply_text("Invalid ID.", quote=True)
        return
    row = get_video(vid)
    if not row:
        await message.reply_text("Video not found.", quote=True)
        return
    _, file_id, thumb_id, title, desc, tags, uploader, upload_time, views = row
    # increment view
    inc_views(vid)
    # send video (as file_id)
    caption = f"{title or 'Untitled'}\n\n{desc or ''}\n\nID: {vid} • {views+1} views"
    await message.reply_video(file_id, caption=caption, reply_markup=make_video_buttons(vid))

# Info
@APP.on_message(filters.command("info"))
async def info_cmd(client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("Usage: /info <video_id>", quote=True)
        return
    try:
        vid = int(args[1].strip())
    except:
        await message.reply_text("Invalid ID.", quote=True)
        return
    row = get_video(vid)
    if not row:
        await message.reply_text("Not found.", quote=True)
        return
    idd, file_id, thumb_id, title, desc, tags, uploader, upload_time, views = row
    text = f"ID: {idd}\nTitle: {title}\nDesc: {desc}\nTags: {tags}\nUploader: {uploader}\nUploaded: {upload_time}\nViews: {views}"
    await message.reply_text(text, quote=True)

# Rename
@APP.on_message(filters.command("rename"))
async def rename_cmd(client, message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply_text("Usage: /rename <video_id> <new title>", quote=True)
        return
    try:
        vid = int(parts[1])
    except:
        await message.reply_text("Invalid ID.", quote=True); return
    row = get_video(vid)
    if not row:
        await message.reply_text("Not found.", quote=True); return
    if row[6] != message.from_user.id:  # uploader check
        await message.reply_text("You are not the uploader.", quote=True); return
    new_title = parts[2].strip()
    update_title(vid, new_title)
    await message.reply_text("Title updated.", quote=True)

# Delete
@APP.on_message(filters.command("delete"))
async def delete_cmd(client, message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply_text("Usage: /delete <video_id>", quote=True); return
    try:
        vid = int(parts[1])
    except:
        await message.reply_text("Invalid ID."); return
    row = get_video(vid)
    if not row:
        await message.reply_text("Not found."); return
    if row[6] != message.from_user.id:
        await message.reply_text("You are not the uploader."); return
    delete_video(vid)
    await message.reply_text("Deleted.", quote=True)

# Callback handlers for inline keyboard
@APP.on_callback_query()
async def cb_handler(client, cb):
    data = cb.data or ""
    if data.startswith("watch:"):
        vid = int(data.split(":",1)[1])
        row = get_video(vid)
        if not row:
            await cb.answer("Not found", show_alert=True); return
        _,file_id,_,title,desc,_,_,_,views = row
        inc_views(vid)
        await APP.send_video(cb.message.chat.id, file_id, caption=f"{title}\n\nID:{vid} • {views+1} views")
        await cb.answer()
    elif data.startswith("info:"):
        vid = int(data.split(":",1)[1])
        row = get_video(vid)
        if not row:
            await cb.answer("Not found", show_alert=True); return
        idd,_,_,title,desc,tags,uploader,upload_time,views = row
        txt = f"ID:{idd}\nTitle:{title}\nDesc:{desc}\nTags:{tags}\nUploader:{uploader}\nUploaded:{upload_time}\nViews:{views}"
        await cb.answer()  # dismiss
        await APP.send_message(cb.message.chat.id, txt)

# ---------- Startup ----------
if __name__ == "__main__":
    init_db()
    print("MeTube bot starting...")
    APP.run()