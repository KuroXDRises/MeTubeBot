# filename: metube_bot.py
import os
import sqlite3
import time
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# ---------- CONFIG ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", "21218274"))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")

APP = Client("metube_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

DB_PATH = "metube.db"
UPLOAD_STATE = {}

# ---------- DB Helpers ----------
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
      views INTEGER DEFAULT 0,
      likes INTEGER DEFAULT 0,
      dislikes INTEGER DEFAULT 0
    )""")
    con.commit()
    con.close()

def add_video(file_id, uploader, title="", description="", tags="", thumb_id=None):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""INSERT INTO videos 
    (file_id, thumb_id, title, description, tags, uploader, upload_time) 
    VALUES (?,?,?,?,?,?,?)""",
    (file_id, thumb_id, title, description, tags, uploader, datetime.utcnow().isoformat()))
    vid = cur.lastrowid
    con.commit(); con.close()
    return vid

def get_video(vid):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""SELECT id,file_id,thumb_id,title,description,tags,uploader,
    upload_time,views,likes,dislikes FROM videos WHERE id=?""", (vid,))
    row = cur.fetchone()
    con.close()
    return row

def inc_views(vid):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE videos SET views = views + 1 WHERE id=?", (vid,))
    con.commit(); con.close()

def inc_like(vid):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE videos SET likes = likes + 1 WHERE id=?", (vid,))
    con.commit(); con.close()

def inc_dislike(vid):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE videos SET dislikes = dislikes + 1 WHERE id=?", (vid,))
    con.commit(); con.close()

def list_user_videos(user_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id,title,upload_time,views FROM videos WHERE uploader=? ORDER BY id DESC", (user_id,))
    rows = cur.fetchall()
    con.close()
    return rows

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
def make_video_buttons(vid, likes=0, dislikes=0):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶ Watch", callback_data=f"watch:{vid}"),
         InlineKeyboardButton("ℹ Info", callback_data=f"info:{vid}")],
        [InlineKeyboardButton(f"👍 {likes}", callback_data=f"like:{vid}"),
         InlineKeyboardButton(f"👎 {dislikes}", callback_data=f"dislike:{vid}")],
        [InlineKeyboardButton("🔗 Share", switch_inline_query=str(vid))]
    ])

# ---------- Commands ----------
@APP.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    await message.reply_text(
        "🎬 Welcome to MeTube Bot!\n\nUpload and share your videos easily.\n\nCommands:\n"
        "/upload - Upload a video\n/myvideos - List your uploads\n/search <query>\n/watch <id>\n/info <id>\n/rename <id> <new_title>\n/delete <id>",
        quote=True
    )

# ---------- Upload Flow ----------
@APP.on_message(filters.command("upload"))
async def upload_cmd(client, message: Message):
    uid = message.from_user.id
    UPLOAD_STATE[uid] = {"step": "await_video", "temp": {}}
    await message.reply_text("📤 Send me the video file to upload.", quote=True)

@APP.on_message(filters.video | filters.document)
async def receive_video(client, message: Message):
    uid = message.from_user.id
    state = UPLOAD_STATE.get(uid)
    if not state or state.get("step") != "await_video":
        return

    file_id = message.video.file_id if message.video else message.document.file_id
    state["temp"]["file_id"] = file_id
    state["step"] = "await_title"

    # show fake loading
    msg = await message.reply_text("Uploading: ■□□□□ 20%", quote=True)
    for p in [40, 60, 80, 100]:
        time.sleep(0.6)
        blocks = "■" * (p // 20) + "□" * (5 - (p // 20))
        await msg.edit_text(f"Uploading: {blocks} {p}%")
    await msg.edit_text("✅ Upload ready! Now send the title.")

@APP.on_message(filters.text & ~filters.command(["start","upload","search","myvideos","watch","info","rename","delete"]))
async def text_handler(client, message: Message):
    uid = message.from_user.id
    state = UPLOAD_STATE.get(uid)
    if not state: return

    step = state.get("step")
    text = message.text.strip()

    if step == "await_title":
        state["temp"]["title"] = text
        state["step"] = "await_description"
        await message.reply_text("📝 Send a description (or '-' to skip).", quote=True)
    elif step == "await_description":
        state["temp"]["description"] = (text if text != "-" else "")
        state["step"] = "await_tags"
        await message.reply_text("🏷️ Send tags, comma separated (or '-' to skip).", quote=True)
    elif step == "await_tags":
        state["temp"]["tags"] = (text if text != "-" else "")
        file_id = state["temp"]["file_id"]
        title = state["temp"]["title"]
        desc = state["temp"]["description"]
        tags = state["temp"]["tags"]
        vid = add_video(file_id, uid, title, desc, tags)
        UPLOAD_STATE.pop(uid, None)
        await message.reply_text(f"✅ Uploaded successfully!\n\nVideo ID: {vid}\nUse /watch {vid} to view.", quote=True)

# ---------- My Videos ----------
@APP.on_message(filters.command("myvideos"))
async def myvideos_cmd(client, message: Message):
    uid = message.from_user.id
    rows = list_user_videos(uid)
    if not rows:
        await message.reply_text("You have not uploaded any videos yet.", quote=True)
        return
    text = "📂 Your videos:\n\n" + "\n".join([f"ID:{r[0]} — {r[1]} — {r[2][:19]} — {r[3]} views" for r in rows])
    await message.reply_text(text, quote=True)

# ---------- Search ----------
@APP.on_message(filters.command("search"))
async def search_cmd(client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("Usage: /search <query>", quote=True)
        return
    q = args[1].strip()
    rows = search_videos(q)
    if not rows:
        await message.reply_text("No results found.", quote=True)
        return
    out = []
    for r in rows:
        out.append(f"ID:{r[0]} — {r[1] or 'Untitled'} — {r[5][:10]} — {r[6]} views")
    txt = "🔍 Search results:\n\n" + "\n".join(out[:20])
    await message.reply_text(txt, quote=True)

# ---------- Watch ----------
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
    _, file_id, _, title, desc, tags, uploader, upload_time, views, likes, dislikes = row
    inc_views(vid)
    caption = f"{title or 'Untitled'}\n\n{desc or ''}\n\nID: {vid} • {views+1} views"
    await message.reply_video(file_id, caption=caption, reply_markup=make_video_buttons(vid, likes, dislikes))

# ---------- Info ----------
@APP.on_message(filters.command("info"))
async def info_cmd(client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("Usage: /info <video_id>", quote=True)
        return
    vid = int(args[1])
    row = get_video(vid)
    if not row:
        await message.reply_text("Video not found.", quote=True)
        return
    idd, file_id, thumb_id, title, desc, tags, uploader, upload_time, views, likes, dislikes = row
    text = (f"ID: {idd}\nTitle: {title}\nDescription: {desc}\nTags: {tags}\nUploader: {uploader}"
            f"\nUploaded: {upload_time}\nViews: {views}\n👍 Likes: {likes}\n👎 Dislikes: {dislikes}")
    await message.reply_text(text, quote=True)

# ---------- Rename ----------
@APP.on_message(filters.command("rename"))
async def rename_cmd(client, message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply_text("Usage: /rename <video_id> <new title>", quote=True)
        return
    vid = int(parts[1])
    row = get_video(vid)
    if not row:
        await message.reply_text("Not found.", quote=True)
        return
    if row[6] != message.from_user.id:
        await message.reply_text("You are not the uploader.", quote=True)
        return
    new_title = parts[2].strip()
    update_title(vid, new_title)
    await message.reply_text("✅ Title updated.", quote=True)

# ---------- Delete ----------
@APP.on_message(filters.command("delete"))
async def delete_cmd(client, message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply_text("Usage: /delete <video_id>", quote=True)
        return
    vid = int(parts[1])
    row = get_video(vid)
    if not row:
        await message.reply_text("Not found.", quote=True)
        return
    if row[6] != message.from_user.id:
        await message.reply_text("You are not the uploader.", quote=True)
        return
    delete_video(vid)
    await message.reply_text("🗑️ Deleted.", quote=True)

# ---------- Inline Button Callbacks ----------
@APP.on_callback_query()
async def cb_handler(client, cb):
    data = cb.data or ""
    if data.startswith("watch:"):
        vid = int(data.split(":",1)[1])
        row = get_video(vid)
        if not row:
            await cb.answer("Not found", show_alert=True); return
        _,file_id,_,title,desc,_,_,_,views,likes,dislikes = row
        inc_views(vid)
        await APP.send_video(cb.message.chat.id, file_id, caption=f"{title}\n\nID:{vid} • {views+1} views", reply_markup=make_video_buttons(vid, likes, dislikes))
        await cb.answer()

    elif data.startswith("info:"):
        vid = int(data.split(":",1)[1])
        row = get_video(vid)
        if not row:
            await cb.answer("Not found", show_alert=True); return
        idd,_,_,title,desc,tags,uploader,upload_time,views,likes,dislikes = row
        txt = (f"ID:{idd}\nTitle:{title}\nDesc:{desc}\nTags:{tags}\nUploader:{uploader}\n"
               f"Uploaded:{upload_time}\nViews:{views}\n👍 {likes} 👎 {dislikes}")
        await APP.send_message(cb.message.chat.id, txt)
        await cb.answer()

    elif data.startswith("like:"):
        vid = int(data.split(":",1)[1])
        inc_like(vid)
        row = get_video(vid)
        await cb.message.edit_reply_markup(make_video_buttons(vid, row[9], row[10]))
        await cb.answer("👍 Liked")

    elif data.startswith("dislike:"):
        vid = int(data.split(":",1)[1])
        inc_dislike(vid)
        row = get_video(vid)
        await cb.message.edit_reply_markup(make_video_buttons(vid, row[9], row[10]))
        await cb.answer("👎 Disliked")

# ---------- Startup ----------
if __name__ == "__main__":
    init_db()
    print("🚀 MeTube bot started...")
    APP.run()
